# Test the "dance this" buttons via the API (no input source), plus a push during the dance.
$b = "http://localhost:8000"
$out = Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) "videos\follow\web_selftest"
New-Item -ItemType Directory -Force $out | Out-Null
for ($i = 0; $i -lt 100; $i++) { Start-Sleep 3; try { $s = Invoke-RestMethod "$b/api/status" -TimeoutSec 3; if ($s.server -ne 'starting') { "server: $($s.server)"; break } } catch {} }
function Post($p, $body) { Invoke-RestMethod -Method Post -Uri "$b$p" -Body ($body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 15 }
function St($tag) { $s = Invoke-RestMethod "$b/api/status"; "{0,-6} src={1} mode={2} dance={3} phase={4} push/fell/getups={5}/{6}/{7}" -f $tag, $s.source, $s.sim.mode, $s.sim.dance_en, $s.sim.phase, $s.sim.push_count, $s.sim.fell_count, $s.sim.getups }
"dance1: " + (Post "/api/dance" @{dance = 1} | ConvertTo-Json -Compress)
Start-Sleep 3; St "t=3"; Invoke-WebRequest "$b/snap/robot" -OutFile "$out\btn_gxdsm.jpg" | Out-Null
"dance0 (queued): " + (Post "/api/dance" @{dance = 0} | ConvertTo-Json -Compress)
Start-Sleep 7; St "t=10"; Invoke-WebRequest "$b/snap/robot" -OutFile "$out\btn_sss.jpg" | Out-Null
"push: " + (Post "/api/push" @{} | ConvertTo-Json -Compress)
Start-Sleep 5; St "t=15"
(Invoke-RestMethod "$b/api/status").sim.events
Post "/api/stop" @{} | Out-Null
