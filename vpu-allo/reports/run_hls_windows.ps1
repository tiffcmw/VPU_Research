# reports/run_hls_windows.ps1

$Vivado = "C:\Xilinx\2025.1\Vivado\settings64.bat"
$Vitis  = "C:\Xilinx\2025.1\Vitis\settings64.bat"
$HlsExe = "C:\Xilinx\2025.1\Vitis\bin\unwrapped\win64.o\vitis_hls.exe"
$RdiDataDir = "C:\Xilinx\2025.1\data"
$TclLibrary = "C:\Xilinx\2025.1\tps\tcl\tcl8\8.6"

$ProjectRoot = (Get-Location).Path
$HlsDir = Join-Path $ProjectRoot "sim\hls_output"
$ReportDir = Join-Path $ProjectRoot "reports\synth_reports"

$Part = "xc7a100tcsg324-1"
$ClockPeriod = "10"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$cppFiles = Get-ChildItem $HlsDir -Filter *.cpp

foreach ($cpp in $cppFiles) {
    $name = [System.IO.Path]::GetFileNameWithoutExtension($cpp.Name)
    $outdir = Join-Path $ReportDir $name
    New-Item -ItemType Directory -Force -Path $outdir | Out-Null

    if ($name -like "vadd*") {
        $top = "vadd_i8"
    } elseif ($name -like "vmac*") {
        $top = "vmac_i8"
    } elseif ($name -like "linear_relu*") {
        $top = "linear_relu_i8"
    } elseif ($name -like "linear*") {
        $top = "linear_i8"
    } elseif ($name -like "relu*") {
        $top = "relu_i8"
    } else {
        Write-Host "Skipping unknown kernel $name"
        continue
    }

    $tcl = Join-Path $outdir "run.tcl"
    $cppPath = $cpp.FullName.Replace("\", "/")
    $projPath = (Join-Path $outdir "proj").Replace("\", "/")

@"
open_project "$projPath"
set_top $top
add_files "$cppPath"
open_solution "solution1" -reset
set_part {$Part}
create_clock -period $ClockPeriod -name default
csynth_design
exit
"@ | Set-Content -Path $tcl -Encoding ASCII

    Write-Host "[$name] top=$top"

    $log = Join-Path $outdir "vitis_hls.log"

    $cmdLine = "call `"$Vitis`" && set RDI_DATADIR=$RdiDataDir&& set TCL_LIBRARY=$TclLibrary&& vitis-run --mode hls --tcl `"$tcl`""
    cmd /c $cmdLine > "$log" 2>&1

    Write-Host "  exit code: $LASTEXITCODE"

    $rpt = Get-ChildItem (Join-Path $outdir "proj") -Recurse -Filter csynth.rpt -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($rpt) {
        Copy-Item $rpt.FullName (Join-Path $outdir "csynth.rpt") -Force
        Write-Host "  -> done"
    } else {
        Write-Host "  -> csynth.rpt not found, check vitis_hls.log"
    }
}