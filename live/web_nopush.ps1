# Control run on the running web app: play a video in a loop WITHOUT pushes, report falls every 5 s.
param([string]$Source = "gym_sss.mp4", [int]$Seconds = 20)
$b = "http://localhost:8000"
Invoke-RestMethod -Method Post -Uri "$b/api/start" -Body (@{source = $Source; loop = $true} | ConvertTo-Json) -ContentType "application/json" | ConvertTo-Json -Compress
for ($t = 5; $t -le $Seconds; $t += 5) {
  Start-Sleep 5
  $s = Invoke-RestMethod "$b/api/status"
  "t={0,2}s dance={1} p={2} phase={3} mode={4} pushes={5} falls={6} rt={7}" -f $t, $s.sim.dance, $s.sim.dance_p, $s.sim.phase, $s.sim.mode, $s.sim.push_count, $s.sim.fell_count, $s.sim.rt_factor
}
(Invoke-RestMethod "$b/api/status").sim.events
Invoke-RestMethod -Method Post -Uri "$b/api/stop" -Body '{}' -ContentType "application/json" | Out-Null
