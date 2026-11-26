# ------------------------------------------------------------------------------
# radio-params.tcl - the radio and MAC parameters of the two stacks
# evalvsn.tcl can run, in one file.
#
# The radio is IEEE 802.15.4 for both stacks; -rp decides whether the EvalVSN
# cross-layer extras apply, so this file branches on $val(rp) alone.
# $val(netif) and $val(mac) name the right classes before it is sourced.
#
# The values are anchored to a real sensor radio - the AT86RF231 of the
# IoT-LAB M3 node: +3 dBm maximum output, -101 dBm
# sensitivity, the 2.4 GHz O-QPSK band - and the power-monitor constants sit
# on the -111 dBm thermal floor of its 2 MHz channel.
# ------------------------------------------------------------------------------

# The queue length the radio's real buffers justify: 16 frames, the order of
# the Contiki and TinyOS transmit queues, and a sane share of the M3's 64 KB.
if {$val(ifqlen) == "radio"} {
    set val(ifqlen) 16
    puts "Interface queue length (radio-anchored): $val(ifqlen)"
}

# The battery is the stack's, not the terrain's, and both stacks live on the
# same model: one real 650 mAh / 3.7 V pack (some 8,658 J) everywhere.
if {$val(initeng) == ""} {
    set val(initeng) 8658
}

# The consumption rates are the chip's own. AT86RF231 at 3.0 V: TX +3 dBm
# 14 mA, RX_ON 12.3 mA - also the listening state, the chip has no cheaper
# idle-listening mode - SLEEP 0.02 uA.
set val(txPower)    0.042
set val(rxPower)    0.037
set val(sleepPower) 0.00000006
set val(idlePower)  0.037

$val(netif) set CPThresh_   2.0         ;# 3 dB co-channel rejection, the AT86RF231's own capture
                                        ;# figure: the ns-2 default of 10 made any transmitter at
                                        ;# 300 m corrupt a 100 m neighbour ((300/100)^2 = 9 < 10),
                                        ;# and no route survived it
$val(netif) set CSThresh_   7.94e-13    ;# -91 dBm: the AT86RF231's CCA mode 1 energy-detection
                                        ;# floor. Sensing at -106/-101 dBm heard carrier over the
                                        ;# whole grid - one collision domain, no spatial reuse; the
                                        ;# chip's own ED range restores three-cell sensing
$val(netif) set RXThresh_   7.943e-14   ;# -101 dBm, AT86RF231 sensitivity
$val(netif) set Pt_         0.002       ;# +3 dBm, AT86RF231 maximum output
$val(netif) set freq_       2.4e9       ;# 2.4 GHz O-QPSK band
$val(netif) set L_          1.0         ;# no additional system loss

# The CSMA/CA constants of Mac/802_15_4 are the standard's, compiled in
# wpan/p802_15_4const.h and left untouched: the MAC needs no line here.

# The routing timers of the cross-layer stacks, read by AOMDV_QPV below and by
# the tuned AOMDV of experiment E1 (aomdv_tuned), so that each value
# is written once. Per-second hellos are the dimensioning of a fast radio: a
# hundred nodes of them eat a 250 kbit/s channel in collisions before any
# video is sent, where real sensor stacks beacon in tens of seconds. Five is
# conservative on that scale. A 1 s cap on the RREQ backoff makes a
# hundred nodes rebroadcast a rediscovery every second - the measured
# ~63,000-drop storm; 10 s is RFC 3561's own value. Routes outlive the
# capture period (30 s at the base point, 9 s under the fires of study 09),
# or every frame would pay the discovery backoff again.
set helloInterval_      5.0
set maxRreqTimeout_     10.0
set activeRouteTimeout_ 35.0

if {$val(rp) == "AOMDV_QPV"} {
    Agent/AOMDV_QPV set HELLO_INTERVAL_  $helloInterval_
    Agent/AOMDV_QPV set MAX_RREQ_TIMEOUT_ $maxRreqTimeout_
    # The learning MAC (CSMA parameters per class and link), off by default.
    if {$val(rl_access) != ""}          { Mac/802_15_4EvalVSN set RL_ACCESS_ $val(rl_access) }
    # The learning agents that replace the rules, each off by default: path,
    # congestion, link-break detection, discovery jitter, transmit power.
    if {$val(rl_path) != ""}            { Agent/AOMDV_QPV set RL_PATH_ $val(rl_path) }
    if {$val(rl_congestion) != ""}      { Agent/AOMDV_QPV set RL_CONGESTION_ $val(rl_congestion) }
    if {$val(rl_break) != ""}           { Agent/AOMDV_QPV set RL_BREAK_ $val(rl_break) }
    if {$val(rl_discovery) != ""}       { Agent/AOMDV_QPV set RL_DISCOVERY_ $val(rl_discovery) }
    if {$val(rl_power) != ""}           { Mac/802_15_4EvalVSN set RL_POWER_ $val(rl_power) }
    # The exploration schedule and the agents' trace (study 10).
    if {$val(rl_eps_start) != ""}       { Agent/AOMDV_QPV set RL_EPS_START_ $val(rl_eps_start); Mac/802_15_4EvalVSN set RL_EPS_START_ $val(rl_eps_start) }
    if {$val(rl_eps_end) != ""}         { Agent/AOMDV_QPV set RL_EPS_END_ $val(rl_eps_end); Mac/802_15_4EvalVSN set RL_EPS_END_ $val(rl_eps_end) }
    if {$val(rl_break_eps) != ""}       { Agent/AOMDV_QPV set RL_BREAK_EPSILON_ $val(rl_break_eps) }
    if {$val(rl_trace) != ""}           { Agent/AOMDV_QPV set RL_TRACE_ $val(rl_trace) }
    # The controls of study 11: the channel-access agent fixed on one of its
    # nine actions, a = 3 i + j for the backoff exponent 2 + i and the
    # backoff count 3 + j (rl_access_fixed), and the link-break agent's
    # exploration alone falling linearly to 0 (rl_break_eps_start,
    # rl_break_eps_end). Without its agent a knob would change nothing, so
    # the run stops instead.
    if {$val(rl_access_fixed) != ""} {
        if {$val(rl_access) != 1 || ![string is integer -strict $val(rl_access_fixed)] ||
            $val(rl_access_fixed) < 0 || $val(rl_access_fixed) > 8} {
            puts "Error: rl_access_fixed takes an action from 0 to 8 and needs rl_access=1."
            exit 1
        }
        Mac/802_15_4EvalVSN set RL_ACCESS_FIXED_ $val(rl_access_fixed)
    }
    # Control 2 with learned configurations (study 11): the
    # channel-access agent's greedy action per node and state written at the
    # end of the run (rl_access_dump), or such a configuration replayed on
    # every unicast frame (rl_access_policy; evalvsn.tcl loads the file once
    # the nodes exist). The dump writes what the agent learned, and a fixed
    # or replayed action learns nothing: the three exclude each other.
    if {$val(rl_access_dump) != "" || $val(rl_access_policy) != ""} {
        if {$val(rl_access) != 1} {
            puts "Error: rl_access_dump and rl_access_policy need rl_access=1."
            exit 1
        }
        if {$val(rl_access_fixed) != "" || ($val(rl_access_dump) != "" && $val(rl_access_policy) != "")} {
            puts "Error: rl_access_fixed, rl_access_dump and rl_access_policy exclude each other."
            exit 1
        }
        if {$val(rl_access_policy) != ""} { Mac/802_15_4EvalVSN set RL_ACCESS_POLICY_ 1 }
    }
    if {$val(rl_break_eps_start) != "" || $val(rl_break_eps_end) != ""} {
        if {$val(rl_break) != 1} {
            puts "Error: rl_break_eps_start and rl_break_eps_end need rl_break=1."
            exit 1
        }
        if {$val(rl_break_eps_start) != ""} { Agent/AOMDV_QPV set RL_BREAK_EPS_START_ $val(rl_break_eps_start) }
        if {$val(rl_break_eps_end) != ""}   { Agent/AOMDV_QPV set RL_BREAK_EPS_END_ $val(rl_break_eps_end) }
    }
    # The agents' learning and exploration rates; all four at 0 freeze every
    # agent on its initial choice (the frozen-policy control of study 10).
    if {$val(rl_alpha) != ""}           { Agent/AOMDV_QPV set RL_ALPHA_ $val(rl_alpha) }
    if {$val(rl_epsilon) != ""}         { Agent/AOMDV_QPV set RL_EPSILON_ $val(rl_epsilon) }
    if {$val(rl_mac_alpha) != ""}       { Mac/802_15_4EvalVSN set RL_MAC_ALPHA_ $val(rl_mac_alpha) }
    if {$val(rl_mac_epsilon) != ""}     { Mac/802_15_4EvalVSN set RL_MAC_EPSILON_ $val(rl_mac_epsilon) }
    # Early discard by priority: the rule (rule_discard) or its learning agent (rl_discard).
    if {$val(rule_discard) != ""}       { Agent/AOMDV_QPV set DISCARD_RULE_ $val(rule_discard) }
    if {$val(rl_discard) != ""}         { Agent/AOMDV_QPV set RL_DISCARD_ $val(rl_discard) }
    Agent/AOMDV_QPV set ACTIVE_ROUTE_TIMEOUT_ $activeRouteTimeout_
    $val(netif) set noise_floor_         7.94328e-15 ;# -111 dBm: thermal noise kTB over the 2 MHz channel
    $val(netif) set PowerMonitorThresh_  2.64776e-15 ;# noise_floor_ / 3, the monitor's ratio
    $val(netif) set SINRThresh_          10.0        ;# 10 dB: the -101 dBm sensitivity over the -111 dBm floor
    $val(netif) set MAX_PRIO_NB          $maxPrioNb_ ;# the PHY's own copy for its score
    $val(netif) set TxPowerAdapt_        1           ;# closed-loop power per neighbour on the chip's TX_PWR steps
    $val(mac)   set MAX_PRIO_NB          $maxPrioNb_ ;# the cross-layer MAC holds the count
}
# The tuned AOMDV of experiment E1 (aomdv_tuned), never the reference:
# the cross-layer stacks' routing timers (the route queue's length is set per
# agent in evalvsn.tcl).
if {$val(rp) == "AOMDV" && $val(aomdv_tuned) == 1} {
    Agent/AOMDV set HELLO_INTERVAL_       $helloInterval_
    Agent/AOMDV set MAX_RREQ_TIMEOUT_     $maxRreqTimeout_
    Agent/AOMDV set ACTIVE_ROUTE_TIMEOUT_ $activeRouteTimeout_
}
# The AOMDV control of study 10: the derived PHY's constants, no power loop.
if {$val(rp) == "AOMDV" && $val(aomdv_derived) == 1} {
    $val(netif) set noise_floor_         7.94328e-15
    $val(netif) set PowerMonitorThresh_  2.64776e-15
    $val(netif) set SINRThresh_          10.0
    $val(netif) set MAX_PRIO_NB          $maxPrioNb_
    $val(netif) set TxPowerAdapt_        0
    $val(mac)   set MAX_PRIO_NB          $maxPrioNb_
}
