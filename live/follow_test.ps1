# Full follow-dance pipeline on video files (no prior about the person or the dance):
# video -> YOLO pose (Windows) -> WSL server: skill retrieval + dancer policy, falls -> learned get-up -> dance again
# -> native MuJoCo render; records ..\videos\follow\follow_<name>.mp4
# Usage: powershell -ExecutionPolicy Bypass -File follow_test.ps1 -Names unseen_sss_1,unseen_gxdsm_1 [-PushAt "6"]
param([string[]]$Names = @('gym_sss'), [string]$PushAt = "", [int]$Loops = 1, [string[]]$ServerArgs = @())
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:WSL_UTF8 = 1
$log = '\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance_logs\live_server.log'
$outdir = Join-Path (Split-Path -Parent $here) 'videos\follow'
New-Item -ItemType Directory -Force $outdir | Out-Null
$Names = $Names | ForEach-Object { $_ -split ',' } | Where-Object { $_ }
foreach ($n in $Names) {
  if (Test-Path $log) { Remove-Item $log -Force }
  $sargs = @('-d', 'Ubuntu-22.04', '--', 'bash', '/home/user/dance_win/live/server_logged.sh', '--trace') + $ServerArgs
  $cargs = @()
  if ($PushAt) { $cargs += @('--push_at', $PushAt) }  # sent by the client, timed from the video start
  Start-Process -FilePath wsl.exe -ArgumentList $sargs -WindowStyle Hidden | Out-Null
  for ($i = 0; $i -lt 150; $i++) {
    Start-Sleep -Seconds 1
    if ((Test-Path $log) -and ((Get-Content $log -Raw) -match 'waiting for the camera client')) { break }
  }
  $video = "\\wsl.localhost\Ubuntu-22.04\home\user\projects\dance\live_tests\$n.mp4"
  Write-Host "=== $n (push at: $PushAt)"
  & <conda>\envs\dancecam\python.exe "$here\cam_client.py" --no_window --video $video --loops $Loops @cargs --record "$outdir\follow_$n.mp4" 2>&1 |
    Select-String -Pattern 'recorded|final status|\[client\]'
  Start-Sleep -Seconds 2
  wsl.exe -d Ubuntu-22.04 -- bash /home/user/dance_win/live/stop_server.sh | Out-Null
  Start-Sleep -Seconds 2
  if (Test-Path $log) {
    Get-Content $log | Select-String -Pattern '\[server\] event'
    Get-Content $log | Select-String -Pattern '\[trace\]|\[tick\]|\[server\] event' | Out-File -Encoding utf8 "$outdir\follow_$n`_trace.txt"
  }
}
