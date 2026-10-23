# One-click live demo: G1 follows you through the laptop camera.
# Run from PowerShell:  powershell -ExecutionPolicy Bypass -File start_live.ps1  [-Record]
# 1) starts the simulation server in WSL (hidden window), 2) waits until it is ready, 3) opens the camera window.
# Stand ~2.5-3 m from the laptop so your whole body is visible. ESC closes the window; the server is stopped too.
param([switch]$Record)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:WSL_UTF8 = 1
$log = '\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance_logs\live_server.log'
Write-Host "starting simulation server in WSL (first start takes ~30-60 s) ..."
$srv = Start-Process -FilePath wsl.exe -ArgumentList '-d','Ubuntu-22.04','--','bash','/home/user/dance_win/live/server_logged.sh' -WindowStyle Hidden -PassThru
for ($i = 0; $i -lt 120; $i++) {
  Start-Sleep -Seconds 1
  if ((Test-Path $log) -and ((Get-Content $log -Raw) -match 'waiting for the camera client')) { break }
}
if (-not ((Get-Content $log -Raw) -match 'waiting for the camera client')) { Write-Host "server did not start, see $log"; exit 1 }
Write-Host "server ready, opening camera window ..."
$args = @("$here\cam_client.py")
if ($Record) { $args += @('--record', "..\live_$(Get-Date -Format yyyyMMdd_HHmmss).mp4") }
& <conda>\envs\dancecam\python.exe @args
wsl.exe -d Ubuntu-22.04 -- bash /home/user/dance_win/live/stop_server.sh | Out-Null
Write-Host "done"
