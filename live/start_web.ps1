# One-click web demo: starts web_app.py (which starts the WSL simulation server) and opens the browser.
# Run:  powershell -ExecutionPolicy Bypass -File start_web.ps1     (close this window or Ctrl+C to stop)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:WSL_UTF8 = 1
Start-Job -ScriptBlock { Start-Sleep -Seconds 4; Start-Process "http://localhost:8000" } | Out-Null
& <conda>\envs\dancecam\python.exe "$here\web_app.py"
