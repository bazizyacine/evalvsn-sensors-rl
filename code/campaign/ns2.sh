#!/bin/bash
#
# Runs an ns-2 simulation from a packet file.
#
# Usage: ns2.sh -st st-packet.dat -rt rtName -vd videoDuration -nn nodes -rp protocol
#        [-dbg 0|1] [-seed N]   seed 0 = ns-2 default sequence

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

USAGE="Usage: $0 -st st-packet.dat -rt rtName -vd videoDuration -nn number_mobile_nodes -rp routing_protocol

  -st  per-packet send trace file
  -rt  name of the reception trace file to produce
  -vd  video duration in seconds, also the simulation time
  -nn  number of mobile nodes
  -rp  routing protocol: AOMDV or AOMDV_QPV
  -fire t0:v[:x:y] - forest-fire front: ignition at (x, y) metres (default
       0, 0) at t0 seconds, radial spread at v m/s, each node destroyed as
       the front reaches it; 0 (default) runs the static scenario unchanged
  -prop propagation model: tworay (default, historical) or
       shadowing[:exp:std] - log-normal shadowing for the forest canopy,
       optional path-loss exponent and deviation override
  -standby period:size - bi-regime scalar flow from the camera node to the
       sink, one packet of size bytes every period seconds for the whole
       mission; 0 (default) none
  -knobs k=v[,k=v] - the stack switches of lib/common.sh (STACK_KNOBS),
          forwarded as evalvsn.tcl options; 0 (default) leaves the
          defaults of ns-default.tcl and radio-params.tcl
  -dbg cross-layer traces, 1 by default (historical behaviour)"

parse_args "$USAGE" "$@"
require_args "$USAGE" st rt vd nn rp

case "${ARG[rp]}" in
  AOMDV|AOMDV_QPV) ;;
  *) die "unknown routing protocol: ${ARG[rp]} (expected AOMDV or AOMDV_QPV)" ;;
esac

require_cmds ns
require_files "${ARG[st]}" evalvsn.tcl

# The fire spec travels as one token (t0:v[:x:y], the capture-column idiom)
# and is unpacked here into the script's five knobs. 0 leaves them at their
# defaults, with the master switch off: the static scenario, byte for byte.
FIRE_ARGS=(-fire 0)
if [[ "${ARG[fire]:-0}" != "0" ]]; then
  IFS=':' read -r fireT0 fireV fireX fireY <<< "${ARG[fire]}"
  [[ -n "$fireT0" && -n "$fireV" ]] \
    || die "invalid -fire spec: ${ARG[fire]} (expected t0:v[:x:y])"
  FIRE_ARGS=(-fire 1 -firet0 "$fireT0" -firev "$fireV" \
             -firex "${fireX:-0}" -firey "${fireY:-0}")
fi

# The propagation spec: tworay, or shadowing with an optional exp:std
# override riding the same token. The Tcl side holds the anchored defaults.
PROP_ARGS=(-prop tworay)
if [[ "${ARG[prop]:-tworay}" != "tworay" ]]; then
  IFS=':' read -r propName propExp propStd <<< "${ARG[prop]}"
  [[ "$propName" == "shadowing" ]] \
    || die "invalid -prop spec: ${ARG[prop]} (expected tworay or shadowing[:exp:std])"
  PROP_ARGS=(-prop shadowing)
  [[ -n "$propExp" ]] && PROP_ARGS+=(-plexp "$propExp")
  [[ -n "$propStd" ]] && PROP_ARGS+=(-pstd "$propStd")
fi

# The knobs, each an option the scenario parses.
KNOB_ARGS=()
if [[ -n "${ARG[knobs]:-}" && "${ARG[knobs]}" != "0" ]]; then
  IFS=',' read -r -a pairs <<< "${ARG[knobs]}"
  for kv in "${pairs[@]}"; do
    key="${kv%%=*}"; value="${kv#*=}"
    is_stack_knob "$key" || die "unknown knob: $key (expected one of: ${STACK_KNOBS[*]})"
    # the replayed configuration is named under data/ (lib/common.sh, data_file)
    [[ "$key" == rl_access_policy ]] && value="$(data_file "$value")"
    KNOB_ARGS+=("-$key" "$value")
  done
fi

# NS_TIMEOUT (seconds), when set, bounds one simulation's wall-clock time so
# that a hung run fails instead of stalling a campaign; unset, the call is
# unchanged.
${NS_TIMEOUT:+timeout -s KILL "$NS_TIMEOUT"} ns evalvsn.tcl \
  -st      "${ARG[st]}" \
  -rt      "${ARG[rt]}" \
  -simt    "${ARG[vd]}" \
  -nn      "${ARG[nn]}" \
  -rp      "${ARG[rp]}" \
  "${KNOB_ARGS[@]}" \
  -dist    "${ARG[dist]:-100}" \
  "${FIRE_ARGS[@]}" \
  "${PROP_ARGS[@]}" \
  -standby "${ARG[standby]:-0}" \
  -dbg     "${ARG[dbg]:-1}" \
  -rndSeed "${ARG[seed]:-0}"
