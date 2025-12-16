# Build script for an EXISTING Vivado project
# Usage (GUI):   source Vivado/build_existing_project.tcl
# Usage (batch): vivado -mode batch -source Vivado/build_existing_project.tcl

# Resolve project-root from the script location
set script_dir [file dirname [info script]]
set root_dir   [file normalize [file join $script_dir ".."]]

set proj_xpr   [file join $root_dir "VPU_NexysA7" "VPU_NexysA7.xpr"]
set rpt_dir    [file join $root_dir "Reports"]

file mkdir $rpt_dir

puts "Root dir : $root_dir"
puts "Project  : $proj_xpr"
puts "Reports  : $rpt_dir"

open_project $proj_xpr

# Optional: ensure top is set (adjust if your top differs)
# set_property top vpu_top [current_fileset]

# Run synthesis/implementation
launch_runs synth_1 -jobs 8
wait_on_run synth_1

open_run synth_1
report_utilization     -file [file join $rpt_dir "util_synth.rpt"]
report_timing_summary  -file [file join $rpt_dir "timing_synth.rpt"]

launch_runs impl_1 -jobs 8
wait_on_run impl_1

open_run impl_1
report_utilization     -file [file join $rpt_dir "util_impl.rpt"]
report_timing_summary  -file [file join $rpt_dir "timing_impl.rpt"]
report_power           -file [file join $rpt_dir "power_impl.rpt"]

puts "DONE. Reports written to: $rpt_dir"
