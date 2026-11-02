param(
  [ValidateSet('start','stop','status','restart','logs')]
  [string]$Action = 'start',
  [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
$Root    = Split-Path $PSScriptRoot -Parent
$PidFile = Join-Path $PSScriptRoot '.dev.pid'
$LogFile = Join-Path $PSScriptRoot '.dev.log'
$ErrFile = Join-Path $PSScriptRoot '.dev.err.log'

function Get-RunningPid {
  if (-not (Test-Path $PidFile)) { return $null }
  $raw = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if (-not $raw) { return $null }
  try {
    $proc = Get-Process -Id ([int]$raw) -ErrorAction Stop
    return $proc.Id
  } catch { return $null }
}

function Start-Dev {
  $existing = Get-RunningPid
  if ($existing) { Write-Output "already running: PID $existing on http://127.0.0.1:$Port/"; return }

  if (Test-Path $LogFile) { Remove-Item $LogFile -Force }
  if (Test-Path $ErrFile) { Remove-Item $ErrFile -Force }

  $proc = Start-Process `
    -FilePath 'python' `
    -ArgumentList '-m','uvicorn','main:app','--host','127.0.0.1','--port',$Port `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError  $ErrFile `
    -WindowStyle Hidden `
    -PassThru

  $proc.Id | Out-File -FilePath $PidFile -Encoding ascii
  Write-Output "started PID $($proc.Id)"

  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    try {
      $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2
      if ($r.StatusCode -eq 200) {
        Write-Output "ready: http://127.0.0.1:$Port/"
        return
      }
    } catch {}
  }
  Write-Output "WARNING: health check timeout; see $ErrFile"
}

function Stop-Dev {
  $existing = Get-RunningPid
  if (-not $existing) { Write-Output 'not running'; return }
  try { Stop-Process -Id $existing -Force -ErrorAction Stop } catch {}
  Remove-Item $PidFile -ErrorAction SilentlyContinue
  Write-Output "stopped PID $existing"
}

function Show-Status {
  $existing = Get-RunningPid
  if ($existing) { Write-Output "running: PID $existing on http://127.0.0.1:$Port/" }
  else { Write-Output 'not running' }
}

function Show-Logs {
  if (Test-Path $LogFile) { Write-Output "--- stdout ---"; Get-Content $LogFile -Tail 40 }
  if (Test-Path $ErrFile) { Write-Output "--- stderr ---"; Get-Content $ErrFile -Tail 40 }
}

switch ($Action) {
  'start'   { Start-Dev }
  'stop'    { Stop-Dev }
  'restart' { Stop-Dev; Start-Dev }
  'status'  { Show-Status }
  'logs'    { Show-Logs }
}
