# Usage: vivado -mode batch -source vivado/create_project.tcl

set proj_name "vpu_nexys_a7"
set proj_dir  "./build/$proj_name"
set part      "xc7a100tcsg324-1"   ;# Nexys A7-100T

create_project $proj_name $proj_dir -part $part -force
set_property target_language Verilog [current_project]
set_property default_lib xil_defaultlib [current_project]

# Add RTL
add_files -norecurse [glob ./rtl/*.sv]
# Add TB
add_files -fileset sim_1 -norecurse [glob ./sim/*.sv]

# XDC (placeholder—edit pins for your board constraints)
add_files -fileset constrs_1 -norecurse ./vivado/nexys_a7_100t.xdc

update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

puts "Project created at: $proj_dir"
