#!/bin/bash
#
# lib/common.sh - functions shared by the simulation scripts, and the list of
# the stack switches a set may declare.
#
# Source it at the top of a script:
#   source "$(dirname "$(readlink -f "$0")")/lib/common.sh"
#
# Provides:
#   die              error exit, message on stderr
#   log_step         step heading
#   log_info         information line
#   parse_args       fills ARG[...] from "-key value" options
#   require_args     fails when an expected key is empty
#   require_files    fails when a file or directory is missing
#   require_cmds     fails when a command is not on the PATH
#   script_dir       real directory of the calling script
#   STACK_KNOBS      the switches of the knobs column of sets.conf that ns2.sh
#                    hands to evalvsn.tcl as -key value
#   is_stack_knob    true when its argument is one of them
#   knob_ok          true when key=value is one of them with a value it takes
#   data_file        the path of a file under the repository's data/ folder

set -uo pipefail

# Associative array filled by parse_args
declare -A ARG

die() {
  echo "Error: $*" >&2
  exit 1
}

# Progress goes to the terminal AND, when PROGRESS_LOG names a file, to that
# file. Without the second destination a long run leaves nothing behind: the
# headings live only in the terminal that started it, so a campaign launched in
# the background is indistinguishable from one that never started, and once the
# terminal is gone there is no way to tell how far it got.
#
# The per-set log is a different thing: it collects the raw output of ffmpeg,
# EvalVSN and ns-2, not the progress. Both are needed.
log_to_progress() {
  [[ -n "${PROGRESS_LOG:-}" ]] || return 0
  printf '%s\n' "$*" >>"$PROGRESS_LOG" 2>/dev/null || true
}

log_step() {
  echo -e "\n=== $* ==="
  log_to_progress "[$(date '+%H:%M:%S')] === $* ==="
}

log_info() {
  echo "$*"
  log_to_progress "[$(date '+%H:%M:%S')] $*"
}

script_dir() {
  dirname "$(readlink -f "${BASH_SOURCE[1]}")"
}

# parse_args "usage" "$@"
#
# Accepts options of the form "-key value". The key is stored without the
# dash: "-ip file" yields ARG[ip]=file. Recognises -h and --help.
parse_args() {
  local usage="$1"; shift

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        echo "$usage"
        exit 0
        ;;
      -*)
        [[ $# -ge 2 ]] || die "option $1 expects a value.\n$usage"
        ARG["${1#-}"]="$2"
        shift 2
        ;;
      *)
        die "unexpected argument: $1\n$usage"
        ;;
    esac
  done
}

# require_args "usage" key...
#
# Checks that every key was given and is not empty. This is the check ns2.sh
# lacked: called without -nn, it passed an empty value to ns-2, which silently
# fell back to its default.
require_args() {
  local usage="$1"; shift
  local missing=()

  for key in "$@"; do
    [[ -n "${ARG[$key]:-}" ]] || missing+=("-$key")
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    die "missing argument(s): ${missing[*]}\n$usage"
  fi
}

require_files() {
  local missing=()
  for f in "$@"; do
    [[ -e "$f" ]] || missing+=("$f")
  done
  [[ ${#missing[@]} -eq 0 ]] || die "not found: ${missing[*]}"
}

require_cmds() {
  local missing=()
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || missing+=("$c")
  done
  [[ ${#missing[@]} -eq 0 ]] || die "command(s) missing from PATH: ${missing[*]}"
}

# Pattern of the trace lines emitted by the ns-2 cross-layer instrumentation.
# Used by the optional log filtering: a twelve-second AOMDV_QPV simulation
# produces 1.3 GB, most of it from these lines.
#
# shellcheck disable=SC2034  # consumed by run_sets.sh, which sources this file
readonly CROSSLAYER_TRACE_PATTERN='\(cross-layer\) using:|MAC ChState|PHY PHYState|PHY Mod_Scheme|PHY PMX Power|MAC PHYIdleInd'

# The stack switches a declaration may set in the knobs column of sets.conf,
# one list for run_sets.sh, which validates the declarations, and ns2.sh,
# which forwards them; evalvsn.tcl gives each its default (an empty value
# keeps the one of ns-default.tcl and radio-params.tcl). simtime, the one
# other key, never reaches ns-2: set.sh applies it.
#
# shellcheck disable=SC2034  # consumed by run_sets.sh and ns2.sh
readonly STACK_KNOBS=(
  rl_path rl_congestion rl_break rl_discovery rl_access rl_power
  rule_discard rl_discard
  rl_alpha rl_epsilon rl_mac_alpha rl_mac_epsilon rl_eps_start rl_eps_end rl_break_eps rl_trace
  rl_access_fixed rl_break_eps_start rl_break_eps_end rl_access_dump rl_access_policy
  aomdv_derived aomdv_tuned jitter camnode sinknode
  firewind firedir firealpha firezone firefail firefailwin firefaildist
)

is_stack_knob() {
  local k
  for k in "${STACK_KNOBS[@]}"; do
    [[ "$k" == "$1" ]] && return 0
  done
  return 1
}

# knob_ok KEY=VALUE: true when KEY is a stack switch and VALUE one it takes in
# the knobs column: a number (or n:m), but for the two files of the
# channel-access agent's learned configuration (study 11):
# rl_access_dump, the file name the run writes in its simulation's folder, and
# rl_access_policy, the file it replays, a path under the repository's data/
# folder (data_file), no component starting with a dot. The keys the shell
# reads itself, simtime and realisation, are checked where they are read.
knob_ok() {
  local k=${1%%=*} v=${1#*=}
  [[ $1 == *=* ]] && is_stack_knob "$k" || return 1
  case $k in
    rl_access_dump) [[ $v =~ ^[A-Za-z0-9_][A-Za-z0-9._-]*$ ]] ;;
    rl_access_policy) [[ $v =~ ^[A-Za-z0-9_][A-Za-z0-9._-]*(/[A-Za-z0-9_][A-Za-z0-9._-]*)*$ ]] ;;
    *) [[ $v =~ ^[0-9.:]+$ ]] ;;
  esac
}

# data_file REL: the path of REL under the repository's data/ folder, or under
# DATA_DIR when it is set: the private copies of code/campaign/ a campaign
# runs in have no data/ beside them.
data_file() {
  printf '%s/%s\n' "${DATA_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/data}" "$1"
}
