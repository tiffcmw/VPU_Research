open_project "C:/Users/tiffa/Documents/RPI/VPU_Research/Spring_2026/reports/synth_reports/vmac_opt/proj"
set_top vmac_i8
add_files "C:/Users/tiffa/Documents/RPI/VPU_Research/Spring_2026/sim/hls_output/vmac_opt.cpp"
open_solution "solution1" -reset
set_part {xc7a100tcsg324-1}
create_clock -period 10 -name default
csynth_design
exit
