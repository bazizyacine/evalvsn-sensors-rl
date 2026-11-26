#------------------------------------------------------------------------------
# evalvsn.tcl - NS2 Simulation Script for Video Sensor Networks (VSN)
#
# Description:
#   This script sets up and runs a wireless ad hoc network simulation in NS2,
#   specifically designed for evaluating video sensor network (VSN) scenarios.
#   It supports two routing protocols: AOMDV and AOMDV_QPV, and dynamically
#   configures simulation parameters based on input trace files and user
#   arguments.
#
# Main Features:
#   - Parses command-line arguments to override default simulation parameters.
#   - Reads a sender trace file to determine the maximum video packet priority
#     and total number of video packets.
#   - Sizes the interface queue from the radio's real transmit buffers through
#     radio-params.tcl: 16 frames.
#   - Configures wireless node parameters, energy models, and the grid
#     topology.
#   - Loads and configures the appropriate routing protocol (AOMDV or
#     AOMDV_QPV), including protocol-specific parameters and trace files.
#   - Initializes nodes, attaches agents (UDP, Sink), and sets up video
#     traffic using a trace-driven application.
#   - Sets up tracing for simulation and network animator (NAM).
#   - Schedules simulation events, including traffic start/stop, file closure,
#     and simulation termination.
#
# Usage:
#   ns evalvsn.tcl -st <st> -rt <rt> -simt <simt> -nn <nn> -rp <rp> \
#                  -dist <m> -initeng <J> \
#                  -dbg <0|1> -rndSeed <n> \
#                  -fire <0|1> -firet0 <s> -firev <m/s> -firex <m> -firey <m> \
#                  -prop <tworay|shadowing> -plexp <n> -pstd <dB> \
#                  -standby <period:size|0>
#   If no arguments are provided, default parameters are used.
#
# Parameters:
#   -st     : Sender trace file (default: "st-packet.dat")
#   -rt     : Receiver trace file (default: "rt-packet.dat")
#   -simt   : Simulation time in seconds (default: 12)
#   -nn     : Number of nodes (default: 100)
#   -rp     : Routing protocol ("AOMDV" or "AOMDV_QPV", default: "AOMDV_QPV")
#             The radio is IEEE 802.15.4 alone, so the two configurations
#             compared, cross-layer 802.15.4 against plain 802.15.4, run
#             from the same script on the same binary;
#             radio-params.tcl carries the constants, anchored to the
#             AT86RF231 radio of the IoT-LAB M3 node, and branches on -rp.
#   -dist   : Grid spacing in meters between neighbour nodes (default: 100).
#   -initeng: Initial battery energy in Joules. Empty (default) applies one
#             real pack - 650 mAh / 3.7 V, some 8,658 J - on every stack;
#             each stack drains it at its own radio's rates.
#   -dbg    : Cross-layer debug traces, 1 or 0 (default: 1). Controls
#             AOMDV_QPV_DBG and IFQ_DBG. These traces are what makes an AOMDV_QPV log reach
#             1.3 GB for a twelve-second run, against 161 KB for a whole
#             AOMDV set, whose release stack has no such traces. Pass -dbg 0 for
#             production runs that do not need the traces.
#   -rndSeed: ns-2 random seed. 0 (default) keeps ns-2's own sequence, so
#             previously computed sets stay bit-for-bit reproducible. A positive
#             value selects one realisation among many, for averaging.
#   -fire   : Forest-fire scenario, 1 or 0 (default: 0 - every existing
#             configuration replays unchanged). When on, a fire front starts
#             at (-firex, -firey) at time -firet0 and advances radially at
#             -firev meters per second; each node is destroyed the instant
#             the front reaches its position. Destruction uses the
#             simulator's own switch - NodeOff on the node's PHY - which
#             makes the node deaf and mute at the physical layer (the
#             energy-model checks in WirelessPhy::sendUp/sendDown drop every
#             packet in and out), exactly the network-level effect of a
#             burned sensor. The death schedule is a pure function of the
#             topology and the three fire parameters: deterministic,
#             replayable, independent of the traffic.
#   -firet0 : Ignition time in seconds (default: 3, after route formation).
#   -firev  : Front speed in meters per second (default: 1.0, a surface-fire
#             rate of spread; the survival study's stress axis).
#   -firex  : Ignition X in meters (default: 0, the camera's corner - the
#             network films the fire that is consuming it).
#   -firey  : Ignition Y in meters (default: 0).
#   The four elements of the forest fire, each off by default:
#   -firewind: Midflame wind speed in m/s (default 0: radial front). The
#             front becomes FARSITE's ellipse (Finney 1998, eq. 13-17):
#             Anderson's (1983) length-to-breadth ratio, the ignition at the
#             rear focus, -firev the head spread rate downwind.
#   -firedir: Direction the wind blows towards, degrees from the x axis
#             (default 0).
#   -firealpha: dB lost per metre of link inside the heated zone ahead of
#             the front (default 0; Mphale, Heron and Verma 2007 computed
#             0.14-1.65 dB/m along the fuel-fire interface). Needs -prop
#             shadowing.
#   -firezone: Depth of that zone, in seconds before the front arrives
#             (default 60).
#   -firefail: Probability that a node fails before the flames reach it,
#             its electronics past their rated temperature (default 0).
#   -firefailwin: Window of those failures, in seconds before the front
#             arrives; the instant is drawn uniformly in it (default 60).
#   The alarm mode is the capture calendar's period, set by the -capture
#   option of set.sh: no knob here.
#   The stack switches (-rl_access, -rl_path, ...) are the STACK_KNOBS of
#   lib/common.sh, each described in code/evalvsn/README.md; two take a file:
#   -rl_access_dump FILE writes the channel-access agent's learned
#   configuration at the end of the run, -rl_access_policy FILE replays one
#   (the format: "The channel-access agent's learned configuration", below).
#   -prop   : Propagation model: "tworay" (default) or "shadowing" -
#             ns-2's log-normal shadowing parameterised for the forest
#             canopy, its RNG seeded by -rndSeed so the
#             protocol's seed law applies to the channel draws too.
#   -plexp  : Shadowing path-loss exponent (default 3.2; pine-forest
#             measurements at 2.4 GHz report 3.1-3.3).
#   -pstd   : Shadowing deviation in dB (default 7.0, same anchoring).
#   -standby: Bi-regime standby flow, "period:size" in seconds and bytes
#             (default 0 = off): scalar readings from the camera node to
#             the sink for the whole mission - the network's first regime,
#             which the video burst joins at detection.
#
# Notes:
#   - Requires radio-params.tcl for the radio and protocol parameters.
#   - The script is designed for research and evaluation of VSN routing and
#     queue management strategies.
#   - The script is written in TCL for use with the NS2 network simulator.
#
# Author:
#   [M.Y BAZIZ]
#------------------------------------------------------------------------------

#============================================================================== 
# Initialize 
#==============================================================================

#––– 1. Defaults –––
set val(st)   "st-packet.dat"
set val(rt)   "rt-packet.dat"
set val(simt) 12
set val(nn)   100
set val(rp)  "AOMDV_QPV"
set val(dbg)  1

# Seed of the ns-2 random generator. Zero - the default - leaves ns-2 to its
# own behaviour, so that sets already computed stay reproducible bit for bit. A
# strictly positive value turns the draw on: that is what makes it possible to
# repeat one configuration over several realisations and average the results.
set val(rndSeed) 0

#––– 2. Check arguments –––––
# Options come in "-key value" pairs: an even count is required rather than a
# fixed one, so that adding an option such as -dbg stays possible.
if {$argc == 0} {
    puts "Starting with all default parameters."
} elseif {$argc % 2 != 0} {
    puts "Wrong number of command-line arguments."
    puts "Usage: ns evalvsn.tcl -st <st> -rt <rt> -simt <simt> -nn <nn> -rp <rp> \[-dbg 0|1\]"
    exit 0
}

#––– 3. Parsing overrides –––––
proc getval {argc argv} {
     global val
     lappend st rt simt nn rp
 
     for {set i 0} {$i < $argc} {incr i} {
          set arg [lindex $argv $i]
          if {[string range $arg 0 0] != "-"} continue
          set ID [string range $arg 1 end]
          set val($ID) [lindex $argv [expr $i+1]]
     }
}

getval $argc $argv

# Reads maxPrioNb and the total number of video packets (maxSeqNb) from a trace.
proc getPrioAndPktCount {filename} {
    set maxPrioNb 0
    set maxSeqNb 0
    set file [open $filename r]
    while {[gets $file line] >= 0} {
        # Skip comment lines
        if {[string match "#*" $line]} {
            continue
        }

        set fields [split $line "\t"]
        set prioNb [lindex $fields 5]
        set seqNb [lindex $fields 1]

        if {$prioNb > $maxPrioNb} {
            set maxPrioNb $prioNb
        }

        if {$seqNb > $maxSeqNb} {
            set maxSeqNb $seqNb
        }
    }
    close $file
    # maxSeqNb starts at 0, hence +1 for the total number of packets
    return [list $maxPrioNb [expr {$maxSeqNb + 1}]]
}

# Read the trace
set prio_pkt [getPrioAndPktCount $val(st)]
set maxPrioNb_ [lindex $prio_pkt 0]
set maxSeqNb_ [lindex $prio_pkt 1]
puts "Max Priority Number (maxPrioNb_): $maxPrioNb_"
puts "Number of video packets to transmit (maxSeqNb_): $maxSeqNb_"

# The interface queue length is the one radio-params.tcl anchors to the
# radio's real buffers: 16 frames, the Contiki/TinyOS order.
set ifqlen_ "radio"
puts "Interface queue length: anchored to the radio (radio-params.tcl)"

#––– 4. Echo all five parameters –––
puts "Simulation time: $val(simt) sec, \
nodes: $val(nn), \
routing: $val(rp), \
sender trace: $val(st), \
recv trace: $val(rt)"

#==============================================================================
# Parameter for wireless nodes
#==============================================================================

set val(chan)       Channel/WirelessChannel       ;# Channel type
# Propagation model (-prop): "tworay", the default, or "shadowing": ns-2's
# own log-normal shadowing, no code, parameterised for the forest canopy the
# scenario films. 2.4 GHz propagation measurements in pine forest report
# path-loss exponents around 3.1-3.3 and shadowing deviations near 7 dB;
# -plexp and -pstd override for a study. The shadowing generator is an
# RNG of its own, so its seed follows the realisation seed (-rndSeed):
# seed 0 stays the deterministic default sequence, a derived seed picks
# one realisation among many - the protocol's law, unchanged.
if {![info exists val(firewind)]}    { set val(firewind) 0 }
if {![info exists val(firedir)]}     { set val(firedir) 0 }
if {![info exists val(firealpha)]}   { set val(firealpha) 0 }
if {![info exists val(firezone)]}    { set val(firezone) 60 }
if {![info exists val(firefail)]}    { set val(firefail) 0 }
if {![info exists val(firefailwin)]} { set val(firefailwin) 60 }
if {![info exists val(prop)]}  { set val(prop)  tworay }
if {![info exists val(plexp)]} { set val(plexp) 3.2 }
if {![info exists val(pstd)]}  { set val(pstd)  7.0 }
if {$val(prop) == "shadowing"} {
    set val(prop) Propagation/Shadowing
    Propagation/Shadowing set pathlossExp_ $val(plexp)
    Propagation/Shadowing set std_db_      $val(pstd)
    Propagation/Shadowing set dist0_       1.0
    # The shadowing RNG seeds from ns-2's PREDEFINED table, whose index
    # must stay below 64 - a derived realisation seed passed raw aborts
    # the simulator (measured: seed 730823, instant death before the
    # first packet). The fixed law folds the realisation seed into the
    # table; with the campaign's std 0 the draws are inert anyway
    # (multiplied by zero), and with a non-zero std the 64 entries bound
    # the number of distinct channel streams - an assumed limit of the
    # simulator's table, not of the protocol.
    Propagation/Shadowing set seed_        [expr {$val(rndSeed) % 64}]
    puts "Propagation: log-normal shadowing (exp $val(plexp), std $val(pstd) dB, seed [expr {$val(rndSeed) % 64}] of table)"
    # The heated zone ahead of the fire front (-firealpha): the same
    # shadowing, plus the flame and plume loss of the links whose ends stand
    # in the zone (mac/fire-propagationEvalVSN.h). The class inherits every
    # Propagation/Shadowing default set above.
    if {$val(firealpha) > 0} {
        set val(prop) Propagation/Shadowing/FireEvalVSN
        Propagation/Shadowing/FireEvalVSN set fireAlpha_ $val(firealpha)
        Propagation/Shadowing/FireEvalVSN set fireZone_  $val(firezone)
        puts "Propagation: heated zone ahead of the front, $val(firealpha) dB/m from $val(firezone) s before it arrives"
    }
} elseif {$val(prop) == "tworay"} {
    if {$val(firealpha) > 0} {
        puts "Error: -firealpha needs -prop shadowing."
        exit 1
    }
    set val(prop) Propagation/TwoRayGround
} else {
    puts "Error: unknown propagation $val(prop) (expected tworay or shadowing)."
    exit 1
}
set val(ant)        Antenna/OmniAntenna           ;# Antenna type
set val(ll)         LL                            ;# Link layer type
set val(ifqlen)     $ifqlen_                      ;# Max packet in ifq; "radio" resolved by radio-params.tcl
set val(nn)         $val(nn)                      ;# Number of mobile nodes
set val(rp)	        $val(rp)                      ;# Routing protocol
set val(topo)       Grid                          ;# Topography (the frozen Chain residue of the old model is gone)
if {![info exists val(dist)]} {
    set val(dist)   100                           ;# Distance in meters; -dist overrides
}
foreach knob {rl_access rl_path rl_congestion rl_break rl_discovery rl_power rule_discard rl_discard rl_alpha rl_epsilon rl_mac_alpha rl_mac_epsilon rl_eps_start rl_eps_end rl_break_eps rl_break_eps_start rl_break_eps_end rl_access_fixed rl_access_dump rl_access_policy rl_trace aomdv_derived aomdv_tuned jitter camnode sinknode firefaildist} {
    if {![info exists val($knob)]} { set val($knob) "" } ;# the stack switches: empty keeps the default of ns-default.tcl and radio-params.tcl
}
# The two files of the channel-access agent's learned configuration (below,
# after the nodes) belong to the cross-layer MAC.
if {$val(rp) != "AOMDV_QPV" && ($val(rl_access_dump) != "" || $val(rl_access_policy) != "")} {
    puts "Error: rl_access_dump and rl_access_policy need -rp AOMDV_QPV."
    exit 1
}
# Forest-fire scenario knobs. Off by default: with -fire 0 the script is
# byte-for-byte the static study, and every set already computed replays
# unchanged. The front model is the simplest one that destroys nodes in a
# physically ordered way: radial spread at constant speed from the ignition
# point, death when reached. Speed is the survival study's stress axis.
if {![info exists val(fire)]}   { set val(fire)   0 }
if {![info exists val(firet0)]} { set val(firet0) 3 }
if {![info exists val(firev)]}  { set val(firev)  1.0 }
if {![info exists val(firex)]}  { set val(firex)  0 }
if {![info exists val(firey)]}  { set val(firey)  0 }
# Bi-regime standby traffic (-standby period:size, default 0 = off): a
# surveillance node samples scalar readings - temperature, smoke index -
# for the whole mission, a few tens of bytes at a low cadence, and the
# video burst joins them at detection (the capture calendar's detect
# instant). The scalar flow runs from t=0 to the end: it is what makes
# the network alive before the fire - and what the video must share the
# channel with after. Plain UDP/CBR, ns-2's own classes: the stacks see
# it as non-video traffic and treat it by their own rules.
if {![info exists val(standby)]} { set val(standby) 0 }
set val(engmodel)   EnergyModel
# The consumption rates belong to the radio chip, hence to the stack:
# radio-params.tcl sets them. The battery belongs to the stack too:
# radio-params.tcl sets it from the
# radio's real node hardware; -initeng overrides for a study.
if {![info exists val(initeng)]} { set val(initeng) "" }
set val(simt)       $val(simt)                    ;# Simulation time in Secondes

# =============================================================================
# Models for PHY & MAC & Channel, by routing protocol
# =============================================================================

# Two stacks, one binary, one radio. Classic AOMDV is the reference: it runs on
# the release's stack as distributed - its priority queue, its IEEE 802.15.4
# PHY and MAC, its AOMDV. The EvalVSN derivations of the PHY and MAC (the
# original wpan/ classes are never modified), their TX watchdog included,
# belong to the cross-layer stacks only.
if {$val(rp) == "AOMDV"} {
    set val(ifq)        Queue/DropTail/PriQueue       ;# Interface queue type
    set val(netif)      Phy/WirelessPhy/802_15_4      ;# Network interface type
    set val(mac)        Mac/802_15_4                  ;# MAC type
    # A control of study 10, never the reference: AOMDV on the derived PHY
    # and MAC, whose TX watchdog the release's MAC lacks.
    if {$val(aomdv_derived) == 1} {
        set val(netif)  Phy/WirelessPhy/802_15_4EvalVSN
        set val(mac)    Mac/802_15_4EvalVSN
    }
} elseif {$val(rp) == "AOMDV_QPV"} {
    set val(ifq)        Queue/priqueueEvalVSN         ;# Interface queue type
    set val(netif)      Phy/WirelessPhy/802_15_4EvalVSN ;# Network interface type
    set val(mac)        Mac/802_15_4EvalVSN           ;# MAC type
} else {
    puts "Error: unknown routing protocol $val(rp) (expected AOMDV or AOMDV_QPV)."
    exit 1
}
puts "Layers: routing $val(rp), queue $val(ifq), PHY $val(netif), MAC $val(mac)"

# One parameter file for the two stacks: it branches on $val(rp).
set val(params) "radio-params.tcl"

if {[file exists $val(params)]} {
    source $val(params)
} else {
    puts "Error: Could not find $val(params) file."
    exit 1
}

# ------------------------------------------------------------------------------
# Channel model
# ------------------------------------------------------------------------------

$val(ant) set X_    0
$val(ant) set Y_    0
$val(ant) set Z_    1.5
$val(ant) set Gt_   1            ;# transmitter antenna gain
$val(ant) set Gr_   1            ;# receiver antenna gain

# ------------------------------------------------------------------------------
# Network interface type model AOMDV_QPV
# ------------------------------------------------------------------------------

if {$val(rp) == "AOMDV_QPV"} {
    Agent/$val(rp) set aomdv_qpv_max_paths_                 [expr 2 * $maxPrioNb_]  
    Agent/$val(rp) set aomdv_qpv_prim_alt_path_len_diff_    [expr 2 * $maxPrioNb_] 
    Agent/$val(rp) set AOMDV_QPV_DBG                        $val(dbg)

    # --- Routing trace file for AOMDV ---
    set aomdv_qpv_tr [open aomdv_qpv.tr w]
    set aomdv_qpv_trace [new Trace/Generic]
    $aomdv_qpv_trace attach $aomdv_qpv_tr
}

# ------------------------------------------------------------------------------
# Interface queue type model
# ------------------------------------------------------------------------------

$val(ifq) set drop_front_       false
$val(ifq) set summarystats_     true
$val(ifq) set queue_in_bytes_   false
$val(ifq) set mean_pktsize_     0
$val(ifq) set IFQ_DBG           $val(dbg)

#==============================================================================
# Main Program
#==============================================================================

# packet trace Video
puts "\n*** $val(st) ***\n"

# *** Initialize Simulator ***
set ns_ [new Simulator]

# Random generator seed. Without an explicit seed (rndSeed = 0), ns-2 keeps its
# default sequence and two runs of the same configuration give the same result -
# reproducible, but silent about variability. A strictly positive seed fixes one
# realisation among many; averaging over several seeds separates the signal from
# the noise.
if {$val(rndSeed) > 0} {
    ns-random $val(rndSeed)
    puts "Random seed set to $val(rndSeed)"
}
    
$ns_ use-newtrace

# *** Initialize Trace file ***
set tracefd [open st-packet.tr w]
$ns_ trace-all $tracefd

# topography
set gridspace [expr int(sqrt($val(nn)))]                ;# Grid of topography
set rlen      [expr int($val(nn) - pow($gridspace,2))]  ;# Rlen of topography
set val(x)    [expr ($gridspace + $rlen) * $val(dist)]  ;# X dimension of topography
set val(y)    [expr ($gridspace + $rlen) * $val(dist)]  ;# Y dimension of topography

# *** Initialize Network Animator ***
set namtrace [open st-packet.nam w]
$ns_ namtrace-all-wireless $namtrace $val(x) $val(y)

# *** set up topography object ***
set topo [new Topography]
$topo load_flatgrid $val(x) $val(y)

# Create  General Operations Director (GOD) object. It is used to store global information about the state of the environment, network, or nodes that an
# omniscent observer would have, but that should not be made known to any participant in the simulation.
set god_ [create-god $val(nn)]

# CONFIGURE AND CREATE NODES
$ns_ node-config -adhocRouting $val(rp) \
                 -llType $val(ll) \
                 -macType $val(mac) \
                 -ifqType $val(ifq) \
                 -ifqLen $val(ifqlen) \
                 -antType $val(ant) \
                 -propType $val(prop) \
                 -phyType $val(netif) \
                 -channelType $val(chan) \
                 -topoInstance $topo \
                 -agentTrace ON \
                 -routerTrace ON \
                 -macTrace ON \
                 -phyTrace ON \
                 -movementTrace ON \
                 -energyModel $val(engmodel) \
                 -rxPower $val(rxPower) \
                 -txPower $val(txPower) \
                 -sleepPower $val(sleepPower) \
                 -idlePower $val(idlePower) \
                 -initialEnergy $val(initeng)

# Define a 'finish' procedure
proc finish { } {
     global ns_ tracefd namtrace val
    $ns_ flush-trace
    flush $tracefd
    flush $namtrace
    close $tracefd
    close $namtrace
    # The learned configuration, at the run's last event (below).
    if {$val(rl_access_dump) != ""} { rlAccessDump $val(rl_access_dump) }
    exit 0
}

# ------------------------------------------------------------------------------
# The channel-access agent's learned configuration (study 11, control 2 with
# learned configurations; data/sensors-rl/2-round2/README.md)
# ------------------------------------------------------------------------------
# -rl_access_dump FILE: at the end of the run, in finish (simt + 0.0001 s, the
# simulation's last event, after the nodes' reset at simt), each node's
# AOMDV_QPV agent returns the greedy action of its channel-access agent in
# each of the nine states (rl-access-greedy), and FILE gets one line per node
# and state, tab-separated:
#   node  class  link  action  be  nb  frames  q
# class 0 critical, 1 normal, 2 low (the packet); link 0 poor, 1 fair, 2 good
# (the destination's mean LQI under 120, under 180, else); action a = 3 i + j,
# the minimum backoff exponent be = 2 + i and the maximum backoffs nb = 3 + j
# (a4, be 3 and nb 4, the standard's, which a state never visited keeps);
# frames, the unicast frames the agent configured in the state; q, the value
# of the action. Lines starting with # are comments; the line of the column
# names starts with "node". The dump only reads the agents: no random draw, no
# event added, the run unchanged.
# -rl_access_policy FILE: a file of that format, read before the simulation
# starts; it gives each of the nn nodes its nine states, once each, and only
# its first four columns are read. Every unicast frame then takes the action
# of its node and state (RL_ACCESS_POLICY_, mac/mac-802_15_4EvalVSN.h).
proc rlAccessDump {path} {
    global ns_ node_ val
    if {[catch {
        set f [open $path w]
        puts $f "# rl_access_dump: the channel-access agent's greedy action per node and state at t = [$ns_ now] s (rndSeed $val(rndSeed), $val(nn) nodes)"
        puts $f "# class 0 critical, 1 normal, 2 low; link 0 poor, 1 fair, 2 good; action a = 3 i + j: be = 2 + i, nb = 3 + j; frames: unicast frames configured in the state; q: the action's value"
        puts $f "node\tclass\tlink\taction\tbe\tnb\tframes\tq"
        for {set i 0} {$i < $val(nn)} {incr i} {
            foreach line [split [string trim [[$node_($i) set ragent_] rl-access-greedy]] "\n"] {
                puts $f "$i\t[join $line "\t"]"
            }
        }
        close $f
    } err]} {
        puts "Error: rl_access_dump $path: $err"
        exit 1
    }
    puts "Channel access: the learned configuration of the $val(nn) nodes written to $path at t = [$ns_ now] s"
}

proc rlAccessPolicy {path} {
    global node_ val
    if {![file readable $path]} {
        puts "Error: rl_access_policy: no file $path."
        exit 1
    }
    set f [open $path r]
    set n 0
    set moved 0
    while {[gets $f line] >= 0} {
        if {[string trim $line] == "" || [string index $line 0] == "#" || [string match "node*" $line]} continue
        set v [regexp -all -inline {\S+} $line]
        set ok [expr {[llength $v] >= 4}]
        foreach x [lrange $v 0 3] { if {![regexp {^(0|[1-9][0-9]*)$} $x]} { set ok 0 } }
        if {$ok} {
            lassign $v i c b a
            set ok [expr {$i >= 0 && $i < $val(nn) && $c >= 0 && $c <= 2 && $b >= 0 && $b <= 2 && $a >= 0 && $a <= 8}]
        }
        if {!$ok} {
            puts "Error: rl_access_policy $path: \"$line\" is not \"node class link action\" (node below $val(nn), class and link 0 to 2, action 0 to 8)."
            exit 1
        }
        if {[info exists pol($i,$c,$b)]} {
            puts "Error: rl_access_policy $path: node $i, class $c, link $b given twice."
            exit 1
        }
        set pol($i,$c,$b) $a
        incr n
        if {$a != 4} { incr moved }
    }
    close $f
    if {$n != 9 * $val(nn)} {
        puts "Error: rl_access_policy $path: $n states, where the $val(nn) nodes have [expr {9 * $val(nn)}]."
        exit 1
    }
    for {set i 0} {$i < $val(nn)} {incr i} {
        for {set c 0} {$c < 3} {incr c} {
            for {set b 0} {$b < 3} {incr b} {
                if {[catch {[$node_($i) set ragent_] rl-access-policy $c $b $pol($i,$c,$b)} err]} {
                    puts "Error: rl_access_policy $path: $err"
                    exit 1
                }
            }
        }
    }
    puts "Channel access: the configuration of $path replayed, $n states of $val(nn) nodes, $moved of them on another action than a4"
}

# Create Nodes
for {set i 0} {$i < $val(nn)} {incr i} {
     set node_($i) [$ns_ node]	
     $node_($i) random-motion 0
}

# --- Attach the log target to every AOMDV_QPV agent and bind MAC/PHY/IFQ (single interface) ---
if {$val(rp) == "AOMDV_QPV"} {
    for {set i 0} {$i < $val(nn)} {incr i} {
        # The node's AOMDV_QPV routing agent
        set agentAOMDV_QPV [$node_($i) set ragent_]
        # The node's MAC (single interface)
        set macEvalVSN [$node_($i) set mac_(0)]
        # The node's interface queue (single interface)
        set ifqEvalVSN [$node_($i) set ifq_(0)]
        # Bind the IFQ to AOMDV_QPV by passing its address
        set nexthop_addr [$node_($i) id]

        if {$agentAOMDV_QPV != ""} {
            $agentAOMDV_QPV log-target $aomdv_qpv_trace
            $agentAOMDV_QPV set-rtq-max-len $val(ifqlen)

            if {$macEvalVSN != ""} {
                $agentAOMDV_QPV setMac $macEvalVSN
            }

            if {$ifqEvalVSN != ""} {
                $agentAOMDV_QPV if-queue $ifqEvalVSN
                $ifqEvalVSN setAOMDV_QPV $agentAOMDV_QPV
                $agentAOMDV_QPV register_ifq_for_nexthop $nexthop_addr $ifqEvalVSN
            }
        }
    }
}

# A replayed channel-access configuration (rl_access_policy), once every node
# has its MAC; radio-params.tcl has set RL_ACCESS_POLICY_.
if {$val(rl_access_policy) != ""} {
    rlAccessPolicy $val(rl_access_policy)
}

# The tuned AOMDV control of study 10 (E1): the route queue of the cross-layer
# stacks, one interface queue long, instead of the release's 64 packets.
if {$val(rp) == "AOMDV" && $val(aomdv_tuned) == 1} {
    for {set i 0} {$i < $val(nn)} {incr i} {
        [$node_($i) set ragent_] set-rtq-max-len $val(ifqlen)
    }
}

# Provide initial (X,Y,Z = 0) co-ordinates for mobilenodes
if {$val(topo) == "Grid"} {
    for {set i 0} {$i < $gridspace} {incr i} { 
        for {set j 0} {$j < $gridspace + $rlen} {incr j} {
            if {[expr $i * ($gridspace + $rlen) + $j] < $val(nn)} {
                set ln [expr $i * ($gridspace + $rlen) + $j]
                $node_($ln) set X_ [expr $i * $val(dist)]
                $node_($ln) set Y_ [expr $j * $val(dist)]
                $node_($ln) set Z_ 0.0
                # Study 10: an irregular deployment, the same for every run.
                if {$val(jitter) != "" && $val(jitter) > 0} {
                    if {![info exists jitRng]} {
                        set jitRng [new RNG]
                        $jitRng seed 20261106
                    }
                    $node_($ln) set X_ [expr {abs($i * $val(dist) + [$jitRng uniform [expr {-$val(jitter)}] $val(jitter)])}]
                    $node_($ln) set Y_ [expr {abs($j * $val(dist) + [$jitRng uniform [expr {-$val(jitter)}] $val(jitter)])}]
                }
            }
        }
    }
}

# ------------------------------------------------------------------------------
# Forest-fire front (-fire 1): progressive node destruction
# ------------------------------------------------------------------------------
# The front leaves (firex, firey) at firet0 and advances radially at firev.
# Node i dies at t_i = firet0 + dist(node_i, ignition) / firev - a pure
# function of the grid and the three parameters, so the destruction sequence
# is deterministic and replayable. Death is the PHY's own NodeOff switch:
# WirelessPhy drops every packet of an off node, in and out, which is the
# network-level truth of a burned sensor (the EvalVSN PHYs end in
# WirelessPhy::sendUp/sendDown, so both stacks die the same way). The
# routing agent above keeps its timers; its packets just never leave the
# radio - as for a real destroyed node, the survivors alone must notice.
# NAM shows the front: dead nodes turn red with a FIRE mark.
if {$val(fire)} {
    set firedead 0
    set fireearly 0
    # The wind-driven front (-firewind): FARSITE's ellipse, whose rear focus
    # is the ignition point. Anderson's ratio is 1 at no wind, where the
    # ellipse is the radial circle; the radial formula is kept for that
    # case so the existing sets replay bit for bit.
    if {$val(firewind) > 0} {
        set fU $val(firewind)
        set fLB [expr {0.936*exp(0.2566*$fU) + 0.461*exp(-0.1548*$fU) - 0.397}]
        if {$fLB > 8.0} { set fLB 8.0 }
        set fHB [expr {($fLB + sqrt($fLB*$fLB - 1.0)) / ($fLB - sqrt($fLB*$fLB - 1.0))}]
        set fR  [expr {double($val(firev))}]
        set fa  [expr {0.5*($fR + $fR/$fHB)/$fLB}] ;# across the wind (FARSITE a)
        set fb  [expr {($fR + $fR/$fHB)/2.0}]      ;# along the wind (FARSITE b)
        set fc  [expr {$fb - $fR/$fHB}]            ;# the centre's drift downwind (FARSITE c)
        set fth [expr {$val(firedir)*acos(-1.0)/180.0}]
        puts [format "Fire: wind %.2f m/s towards %.1f deg, length-to-breadth %.3f, head %.3f m/s, back %.3f m/s, flank %.3f m/s" \
            $fU $val(firedir) $fLB $fR [expr {$fR/$fHB}] $fa]
    }
    # Failures before combustion (-firefail): an RNG of their own, seeded
    # from the realisation, so the rest of the simulation keeps its streams.
    # Two draws per node whatever happens, so a node's draws do not depend
    # on the others'.
    if {$val(firefail) > 0} {
        set fireRng [new RNG]
        $fireRng seed [expr {($val(rndSeed) % 900000) + 1}]
    }
    if {$val(firealpha) > 0} {
        set fireProp [$ns_ set propInstance_]
    }
    # The oracle's input (metrics/fire_oracle.py): the radio constants, then
    # each node's position, front arrival and death time.
    set fireLog [open fire-nodes.dat w]
    set fNetif [$node_(0) set netif_(0)]
    puts $fireLog "# Pt_ [$fNetif set Pt_] L_ [$fNetif set L_] freq_ [$fNetif set freq_] CSThresh_ [$fNetif set CSThresh_] RXThresh_ [$fNetif set RXThresh_] Gt_ [Antenna/OmniAntenna set Gt_] Gr_ [Antenna/OmniAntenna set Gr_]"
    puts $fireLog "# prop $val(prop) plexp $val(plexp) pstd $val(pstd) dist0 1.0 firealpha $val(firealpha) firezone $val(firezone) firet0 $val(firet0) camera [expr {$val(camnode) != "" ? $val(camnode) : 0}] sink [expr {$val(sinknode) != "" ? $val(sinknode) : $ln}] simt $val(simt)"
    puts $fireLog "# id x y front death"
    for {set i 0} {$i < $val(nn)} {incr i} {
        # NAM's color change needs an initial color on record: nodes start
        # green - live vegetation - and turn red when the front takes them.
        $node_($i) color green
        set dx [expr [$node_($i) set X_] - $val(firex)]
        set dy [expr [$node_($i) set Y_] - $val(firey)]
        if {$val(firewind) > 0} {
            # Inside the ellipse at time t when a^2 (x - c t)^2 + b^2 y^2
            # <= a^2 b^2 t^2, in the wind's frame; the entry time is the
            # positive root.
            set xw [expr {$dx*cos($fth) + $dy*sin($fth)}]
            set yw [expr {-$dx*sin($fth) + $dy*cos($fth)}]
            set qa [expr {$fa*$fa*($fc*$fc - $fb*$fb)}]
            set qb [expr {-2.0*$xw*$fc*$fa*$fa}]
            set qc [expr {$xw*$xw*$fa*$fa + $yw*$yw*$fb*$fb}]
            set ti [expr {$val(firet0) + ($qb + sqrt($qb*$qb - 4.0*$qa*$qc)) / (-2.0*$qa)}]
        } else {
            set ti [expr $val(firet0) + sqrt($dx*$dx + $dy*$dy) / double($val(firev))]
        }
        set tdie $ti
        if {$val(firefail) > 0} {
            set u1 [$fireRng uniform 0 1]
            set u2 [$fireRng uniform 0 1]
            if {$u1 < $val(firefail)} {
                # firefaildist 1: closer to the front, as the heating grows.
                if {$val(firefaildist) == 1} { set u2 [expr {$u2 * $u2}] }
                set tdie [expr {$ti - $val(firefailwin)*$u2}]
                if {$tdie < $val(firet0)} { set tdie $val(firet0) }
            }
        }
        if {$val(firealpha) > 0} {
            $fireProp fire-node [$node_($i) id] $ti
        }
        puts $fireLog "$i [$node_($i) set X_] [$node_($i) set Y_] $ti $tdie"
        if {$tdie < $val(simt)} {
            $ns_ at $tdie "[$node_($i) set netif_(0)] NodeOff"
            $ns_ at $tdie "$node_($i) color red"
            $ns_ at $tdie "$node_($i) add-mark FIRE red circle"
            incr firedead
            if {$tdie < $ti} { incr fireearly }
        }
    }
    close $fireLog
    puts "Fire: ignition ($val(firex), $val(firey)) at t=$val(firet0) s,\
 front speed $val(firev) m/s: $firedead of $val(nn) nodes destroyed before t=$val(simt) s"
    if {$val(firefail) > 0} {
        puts "Fire: $fireearly of them failed before the flames reached them (p=$val(firefail), window $val(firefailwin) s)"
    }
}

# Define traffic model
# 0 connecting to last node, unless -camnode and -sinknode say otherwise
set camN 0
if {$val(camnode) != ""} { set camN $val(camnode) }
if {$val(sinknode) != ""} { set ln $val(sinknode) }
set udp [new Agent/evalvsnUDP]
$udp set packetSize_ 0
$ns_ attach-agent $node_($camN) $udp
$node_($camN) label "VBR"
set sink [new Agent/evalvsnSink]
$sink set packetSize_ 0
$ns_ attach-agent $node_($ln) $sink
$node_($ln) label "Sink"
set video [new Application/Traffic/evalvsn]
$video set packetSize_ 0
$video attach-agent $udp
$ns_ connect $udp $sink

# Video setting
puts "Video start..."
# Traffic Video
# EvalVSN's own trace-file class, not ns-2's Tracefile: the application
# casts what it is given to evalvsnFile, whose end-of-trace flag sits past
# the stock object's 72 bytes. A Tracefile here would write that flag into
# the next heap chunk at the end of every trace.
set trace_file [new evalvsnFile]
$trace_file filename $val(st)
$video attach-tracefile $trace_file
$udp set_filename ns2_[file tail $val(st)]
$sink set_filename $val(rt)

# ------------------------------------------------------------------------------
# Standby scalar flow (-standby period:size): the mission's first regime
# ------------------------------------------------------------------------------
if {$val(standby) != "0"} {
    set sbFields [split $val(standby) ":"]
    set sbPeriod [lindex $sbFields 0]
    set sbSize   [lindex $sbFields 1]
    if {$sbPeriod == "" || $sbSize == ""} {
        puts "Error: invalid -standby spec $val(standby) (expected period:size)."
        exit 1
    }
    set sbUdp [new Agent/UDP]
    $ns_ attach-agent $node_($camN) $sbUdp
    set sbSink [new Agent/Null]
    $ns_ attach-agent $node_($ln) $sbSink
    $ns_ connect $sbUdp $sbSink
    set sbCbr [new Application/Traffic/CBR]
    $sbCbr set packetSize_ $sbSize
    $sbCbr set interval_   $sbPeriod
    $sbCbr set random_     0
    $sbCbr attach-agent $sbUdp
    $ns_ at 0.0 "$sbCbr start"
    $ns_ at $val(simt) "$sbCbr stop"
    puts "Standby scalar flow: $sbSize bytes every $sbPeriod s, camera to sink, whole mission"
}

# Define node initial position in nam
for {set i 0} {$i < $val(nn)} {incr i} {
     $ns_ initial_node_pos $node_($i) 30
}

# tell all nodes when the simulation ends
for {set i 0} {$i < $val(nn)} {incr i} {
     $ns_ at $val(simt) "$node_($i) reset"
}

$ns_ at 0.0 "$video start"
$ns_ at $val(simt) "$video stop"
$ns_ at $val(simt) "$udp closefile"
$ns_ at $val(simt) "$sink closefile"
$ns_ at $val(simt) "$udp printstatus"
$ns_ at $val(simt) "$sink printstatus"
$ns_ at $val(simt).0001 "finish"
$ns_ at $val(simt).0002 "puts \"NS EXITING...\" ; $ns_ halt"

# Run the simulation
puts "Starting Simulation..."
$ns_ run
