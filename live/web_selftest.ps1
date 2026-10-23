# Drive the running web app like a user: start a video, push, collect status + snapshots.
# Usage: powershell -ExecutionPolicy Bypass -File web_selftest.ps1 [-Source gym_sss.mp4]
param([string]$Source = "gym_sss.mp4")
$out = Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) "videos\follow\web_selftest"
New-Item -ItemType Directory -Force $out | Out-Null
$base = "http://localhost:8000"
function Post($p, $b) { Invoke-RestMethod -Method Post -Uri "$base$p" -Body ($b | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 15 }
function Snap($tag) {
  Invoke-WebRequest "$base/snap/human" -OutFile "$out\$tag`_human.jpg" -TimeoutSec 10 | Out-Null
  Invoke-WebRequest "$base/snap/robot" -OutFile "$out\$tag`_robot.jpg" -TimeoutSec 10 | Out-Null
}
function Status($tag) {
  $s = Invoke-RestMethod "$base/api/status" -TimeoutSec 10
  "{0,-8} src={1} fps={2} dance={3} p={4} phase={5} mode={6} push/fell/getups={7}/{8}/{9} rt={10}" -f $tag, $s.source, $s.cam_fps,
    $s.sim.dance, $s.sim.dance_p, $s.sim.phase, $s.sim.mode, $s.sim.push_count, $s.sim.fell_count, $s.sim.getups, $s.sim.rt_factor
}
Post "/api/start" @{source = $Source; loop = $true} | ConvertTo-Json -Compress
Start-Sleep 5; Status "t=5"; Snap "a_dancing"
Post "/api/push" @{} | ConvertTo-Json -Compress
Start-Sleep 1.5; Status "t=6.5"; Snap "b_fallen"
Start-Sleep 2; Status "t=8.5"; Snap "c_getting_up"
Start-Sleep 5; Status "t=13.5"; Snap "d_dancing_again"
(Invoke-RestMethod "$base/api/status").sim.events
Post "/api/stop" @{} | ConvertTo-Json -Compress
