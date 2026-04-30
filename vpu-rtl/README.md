# VPU Research Project

## Overview
This repository contains the complete source code and project files for a Vector Processing Unit (VPU) implementation targeted for the Nexys A7 FPGA board. Developed as part of a semester-long research project, this VPU supports vectorized operations such as VADD_I8 with configurable vector lengths (VL) and lanes, optimized for efficient computation in embedded systems.

The project demonstrates proficiency in hardware design, simulation, and verification using industry-standard tools, resulting in a fully synthesizable and testable FPGA design.

## Key Features
- **Vectorized Operations**: Implements VADD_I8 (8-bit integer vector addition) with support for VL=16 and 4 lanes.
- **Modular Architecture**: Includes components like VPU Core, Lanes, Scratchpad, and Sparsity Mask for scalable vector processing.
- **Golden Model**: Python-based reference implementation for validation and testing.
- **FPGA Implementation**: Ready-to-use Vivado project for synthesis and deployment on Nexys A7.
- **Simulation and Verification**: Comprehensive testbench ensuring correctness of operations.

## Technologies Used
- **Hardware Description**: SystemVerilog
- **Simulation**: Vivado Simulator (XSim)
- **FPGA Toolchain**: Xilinx Vivado
- **Reference Model**: Python
- **Target Hardware**: Digilent Nexys A7 (Artix-7 FPGA)

## Project Structure
```
VPU_Research/
├── Models/
│   └── golden.py          # Python golden model for VPU operations
├── Scripts/
│   └── run_sim.sh         # Shell script for running simulations
├── Vivado/
│   ├── build.tcl          # TCL script for building the project
│   └── create_project.tcl # TCL script for creating Vivado project
├── VPU_NexysA7/           # Vivado project directory
│   ├── VPU_NexysA7.xpr    # Vivado project file
│   ├── VPU_NexysA7.srcs/
│   │   ├── sources_1/new/ # Design sources (vpu_core.sv, lane_i8.sv, etc.)
│   │   └── sim_1/new/     # Simulation sources (tb_vpu_core.sv)
│   └── VPU_NexysA7.sim/   # Simulation outputs and logs
└── README.md              # This file
```

## Prerequisites
- Xilinx Vivado (version 2020.1 or later) installed and licensed.
- Python 3.x for running the golden model.
- Bash-compatible terminal (for running scripts on Windows, use WSL or Git Bash).

## Setup and Installation
1. Clone the repository:
   ```
   git clone https://github.com/tiffcmw/VPU_Research.git
   cd VPU_Research
   ```

2. Ensure Vivado is installed and accessible via command line.

## Usage
### Running the Golden Model
Execute the Python script to validate VPU operations:
```
python Models/golden.py
```

### Running Simulation in Vivado
1. Open Vivado and import the project:
   - Launch Vivado.
   - Select `File > Open Project` and navigate to `VPU_NexysA7/VPU_NexysA7.xpr`.

2. Run Behavioral Simulation:
   - Go to `Flow > Run Simulation > Run Behavioral Simulation`.
   - In the simulation window, click the "Run All" button (▶️) or press F3.

3. Verify Success:
   - Check the console for the message: `TB PASS: VADD_I8 correct for VL=16, LANES=4`.

### Alternative: Run Simulation via Script
Use the provided shell script for automated simulation:
```
./Scripts/run_sim.sh
```
(Note: Ensure execute permissions on the script.)

## Synthesis and Deployment
- After simulation, proceed to synthesis: `Flow > Run Synthesis`.
- Implement the design: `Flow > Run Implementation`.
- Generate bitstream: `Flow > Generate Bitstream`.
- Program the FPGA on Nexys A7 board for hardware testing.

## Results and Validation
- Simulation confirms correct VADD_I8 operations for specified VL and lanes.
- The design is optimized for low latency and resource efficiency on Artix-7 FPGA.

## Author
Tiffany Cheng - Developed as part of academic research in Fall 2025. 

Contact: tiffanycmw530@gmail.com

## License
This project is for educational and research purposes. See repository license for details.
