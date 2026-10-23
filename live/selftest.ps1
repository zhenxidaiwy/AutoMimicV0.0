# Headless end-to-end self test: start server, run the client without a window for N seconds, record, stop server.
param([int]$Seconds = 15)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:WSL_UTF8 = 1
$log = '\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance_logs\live_server.log'
if (Test-Path $log) { Remove-Item $log -Force }
Start-Process -FilePath wsl.exe -ArgumentList '-d','Ubuntu-22.04','--','bash','/home/user/dance_win/live/server_logged.sh' -WindowStyle Hidden | Out-Null
for ($i = 0; $i -lt 120; $i++) {
  Start-Sleep -Seconds 1
  if ((Test-Path $log) -and ((Get-Content $log -Raw) -match 'waiting for the camera client')) { break }
}
& <conda>\envs\dancecam\python.exe "$here\cam_client.py" --no_window --duration $Seconds --record ..\live_selftest.mp4 2>&1 | Select-Object -Last 2
wsl.exe -d Ubuntu-22.04 -- bash /home/user/dance_win/live/stop_server.sh
