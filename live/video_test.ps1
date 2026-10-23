# Offline-video test of the full live pipeline (YOLO pose on Windows -> WSL server -> native render).
# Usage: powershell -ExecutionPolicy Bypass -File video_test.ps1 [-Names gym_sss,switch_test]
param([string[]]$Names = @('gym_sss', 'hoodie_sss', 'bda_ming_gxdsm_a', 'bda_ming_gxdsm_b', 'switch_test'))
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:WSL_UTF8 = 1
$log = '\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance_logs\live_server.log'
$Names = $Names | ForEach-Object { $_ -split ',' } | Where-Object { $_ }  # "-Names a,b" arrives as one string via -File
foreach ($n in $Names) {
  if (Test-Path $log) { Remove-Item $log -Force }
  Start-Process -FilePath wsl.exe -ArgumentList '-d','Ubuntu-22.04','--','bash','/home/user/dance_win/live/server_logged.sh' -WindowStyle Hidden | Out-Null
  for ($i = 0; $i -lt 120; $i++) {
    Start-Sleep -Seconds 1
    if ((Test-Path $log) -and ((Get-Content $log -Raw) -match 'waiting for the camera client')) { break }
  }
  $video = "\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance\live_tests\$n.mp4"
  Write-Host "=== $n"
  & <conda>\envs\dancecam\python.exe "$here\cam_client.py" --no_window --video $video --record "..\video_test_$n.mp4" 2>&1 |
    Select-String -Pattern 'recorded|final status'
  wsl.exe -d Ubuntu-22.04 -- bash /home/user/dance_win/live/stop_server.sh | Out-Null
}
