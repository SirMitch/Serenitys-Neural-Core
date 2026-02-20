param(
    [switch]$DebugMode
)

try {
    if ($DebugMode) {
        Write-Host "[DEBUG] Starting system info scan." -ForegroundColor DarkGray
    }

    $ErrorActionPreference = "SilentlyContinue"

    # --- OS Info ---
    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
    $osVersion = if ($osInfo) { $osInfo.Caption } else { "N/A" }

    # --- CPU Info ---
    $cpuInfo = Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1
    $cpuName  = if ($cpuInfo) { $cpuInfo.Name.Trim() } else { "N/A" }
    $cpuCores = if ($cpuInfo) { $cpuInfo.NumberOfCores } else { "N/A" }

    # --- RAM Info ---
    $ramGB = if ($osInfo) { [math]::Round($osInfo.TotalVisibleMemorySize / 1024 / 1024) } else { "N/A" }
    $pageFileMB = if ($osInfo) { [math]::Round($osInfo.TotalVirtualMemorySize / 1024) } else { "N/A" }

    # --- GPU Info (NVIDIA via nvidia-smi) ---
    $gpuName     = "N/A"
    $gpuDriver   = "N/A"
    $vramTotalMB = "N/A"
    $vramFreeMB  = "0"

    $nvidiaSmiPath = (Get-Command nvidia-smi -ErrorAction SilentlyContinue).Source

    if ($nvidiaSmiPath) {
        if ($DebugMode) { Write-Host "[DEBUG] Found nvidia-smi at: $nvidiaSmiPath" -ForegroundColor DarkGray }

        $gpuName     = (& nvidia-smi --query-gpu=gpu_name        --format=csv,noheader,nounits 2>$null | Select-Object -First 1).Trim()
        $gpuDriver   = (& nvidia-smi --query-gpu=driver_version   --format=csv,noheader,nounits 2>$null | Select-Object -First 1).Trim()
        $vramTotalMB = (& nvidia-smi --query-gpu=memory.total     --format=csv,noheader,nounits 2>$null | Select-Object -First 1).Trim()
        $vramFreeMB  = (& nvidia-smi --query-gpu=memory.free      --format=csv,noheader,nounits 2>$null | Select-Object -First 1).Trim()

        if (-not $vramFreeMB -or $vramFreeMB -notmatch '^\d+$') { $vramFreeMB = "0" }

        if ($DebugMode) {
            Write-Host "[DEBUG] GPU:         $gpuName"     -ForegroundColor DarkGray
            Write-Host "[DEBUG] Driver:      $gpuDriver"   -ForegroundColor DarkGray
            Write-Host "[DEBUG] VRAM Total:  $vramTotalMB MB" -ForegroundColor DarkGray
            Write-Host "[DEBUG] VRAM Free:   $vramFreeMB MB"  -ForegroundColor DarkGray
        }
    } elseif ($DebugMode) {
        Write-Host "[DEBUG] nvidia-smi not found in PATH. VRAM info unavailable." -ForegroundColor DarkGray
    }

    # --- Output as key=value pairs ---
    Write-Output "OS_VERSION=$osVersion"
    Write-Output "CPU_NAME=$cpuName"
    Write-Output "CPU_CORES=$cpuCores"
    Write-Output "RAM_GB=$ramGB"
    Write-Output "PAGE_FILE_MB=$pageFileMB"
    Write-Output "GPU_NAME=$gpuName"
    Write-Output "GPU_DRIVER=$gpuDriver"
    Write-Output "VRAM_TOTAL_MB=$vramTotalMB"
    Write-Output "VRAM_FREE_MB=$vramFreeMB"

    if ($DebugMode) {
        Write-Host "[DEBUG] System info scan complete." -ForegroundColor DarkGray
    }
    exit 0

} catch {
    Write-Error "gather_system_info.ps1 failed: $_"
    exit 1
}
