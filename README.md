# Critical Path Extractor

This repository is created to explain the VLSI design flow we've used in our paper.

"[Clock Data Compensation Aware Clock Tree Synthesis in Digital Circuits with Adaptive Clock Generation](http://ieeexplore.ieee.org/document/7927229/),"
Taesik Na, Jong Hwan Ko and Saibal Mukhopadhyay,
Design, Automation & Test in Europe Conference & Exhibition (DATE), Mar 2017

Please cite our paper in your publications if it helps your research.


### Prerequisites

Please make sure you have created gate-level netlist and parasitic file after performing place and route.
We've used Synopsys IC compiler.
These are the sample tcl commands for our jpeg encoder to generate gate-level netlist and parasitic file on icc_shell.

```
icc_shell> extract_rc
icc_shell> report_timing -group clk -nets -max_paths 20 -path_type full_clock > Timing.rpt
icc_shell> write_verilog jpeg_top.apr.v
icc_shell> write_parasitics -no_name_mapping
```

This series of commands will produce timing report (Timing.rpt),
gate-level netlist (jpeg_top.apr.v) and parasitic file (jpeg_top.spf).

### Critical path verilog generation

After you have created necessary output files, please prepare .lib file provided by PDK provider.
We've used Synopsys 28nm standard cell library file (saed32rvt_tt1p05v25c.lib).
Please run the script in the following way.

```
./getcritical.py Timing.rpt jpeg_top.apr.v saed32rvt_tt1p05v25c.lib 1 jpeg_top.spf
```

This will create,

| File name | Description |
| --------- | ----------- |
| lib.report | .lib report file for analysis purpose. |
| criticalpath.net.report | critical path report file for analysis purpose. |
| jpeg_top.crit.v | Critical path only gate-level netlist verilog. This is a verilog file for a reference. |
| jpeg_top.crit.spf.v | Critical path only gate-level netlist verilog in which the net names are changed based on Timing.rpt file to reflect parasitics. We will convert this to SPICE netlist. And the resulting SPICE netlist will be used with critical path parasitic file for later HSPICE simulation. |
| jpeg_top.crit.spf.parasitics.ckt | Critical path only parasitic file. |
| jpeg_top.force.ckt | Reference HSPICE input deck to force floating inputs to some values (ground or vdd). Note that you need to change this forcing file accordingly to make critical path get activated. |

### Critical path SPICE netlist generation

After you have created critical path verilog (jpeg_top.crit.spf.v), we need to convert this into SPICE netlist.
We will use Synopsys v2s to do this.
v2s is the script which can be founded in Synopsys HSIM package.
Please prepare standard cell SPICE netlist.
We've used Synopsys 28nm standard cell SPICE netlist file (saed32nm_rvt.spf).
Please run v2s as follows and substitute necessary strings.

```
v2s jpeg_top.crit.spf.v -s saed32nm_rvt.spf -const0 0 -const1 evc -o jpeg_top.crit.spf.ckt
sed -i -e 's/unexpectedcolon/\:/g' jpeg_top.crit.spf.ckt
sed -i -e 's/VDD_dummy[0-9][0-9][0-9]/VDD/g' jpeg_top.crit.spf.ckt
sed -i -e 's/VDD_dummy[0-9][0-9]/VDD/g' jpeg_top.crit.spf.ckt
sed -i -e 's/VDD_dummy[0-9]/VDD/g' jpeg_top.crit.spf.ckt
sed -i -e 's/VSS_dummy[0-9][0-9][0-9]/VSS/g' jpeg_top.crit.spf.ckt
sed -i -e 's/VSS_dummy[0-9][0-9]/VSS/g' jpeg_top.crit.spf.ckt
sed -i -e 's/VSS_dummy[0-9]/VSS/g' jpeg_top.crit.spf.ckt
```

We have obtained critical path SPICE netlist (jpeg_top.crit.spf.ckt) !!
You are now ready to run HSPICE simulation !!
Please use saed32nm_rvt.spf, jpeg_top.crit.spf.ckt, jpeg_top.crit.spf.parasitics.ckt, and jpeg_top.force.ckt (You might have to change the forcing value if necessary) for HSPICE simulation for the delay characterization !!!

