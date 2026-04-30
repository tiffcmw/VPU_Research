open_project "C:/Users/tiffa/Documents/RPI/VPU_Research/Spring_2026/reports/synth_reports/linear_baseline/proj"
set_top linear_i8
add_files "C:/Users/tiffa/Documents/RPI/VPU_Research/Spring_2026/sim/hls_output/linear_baseline.cpp"
open_solution "solution1" -reset
set_part {xc7a100tcsg324-1}
create_clock -period 10 -name default
csynth_design
exit
