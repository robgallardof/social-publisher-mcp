<#
.SYNOPSIS
  Registers the Windows scheduled tasks that publish the queue every day.

  "CM - publicar" runs `social-forge run-due` at 05:00 (from config post_time) plus retries at +20 min,
  +1 h and +2 h. The runner is idempotent: retries only touch what failed or is still pending.
  The task wakes the PC from sleep and runs as soon as possible if 05:00 was missed.

  -WithAgentPrep also adds "CM - preparar" at 21:00: a headless Claude Code run of the community
  manager that writes missing copy for tomorrow's videos (needs the `claude` CLI logged in).

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 -WithAgentPrep
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 -Remove
#>
param([switch]$WithAgentPrep, [switch]$Remove, [string]$PostTime = "")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$forge = Join-Path $root "mcp\social-forge"
$names = @("CM - publicar", "CM - preparar")

if ($Remove) {
    foreach ($n in $names) { Unregister-ScheduledTask -TaskName $n -Confirm:$false -ErrorAction SilentlyContinue }
    Write-Host "Tareas eliminadas."; exit 0
}

if (-not $PostTime) {
    $cfg = Join-Path $root "config\social.yaml"
    if (-not (Test-Path $cfg)) { $cfg = Join-Path $root "config\social.example.yaml" }
    $line = Select-String -Path $cfg -Pattern '^post_time:\s*"?(\d{1,2}:\d{2})' | Select-Object -First 1
    $PostTime = if ($line) { $line.Matches[0].Groups[1].Value } else { "05:00" }
}
$first = [datetime]::ParseExact($PostTime.PadLeft(5, "0"), "HH:mm", $null)

$uv = (Get-Command uv).Source
$run = New-ScheduledTaskAction -Execute $uv -WorkingDirectory $forge `
    -Argument "run --quiet --no-sync --directory `"$forge`" social-forge run-due"
$triggers = @(0, 20, 60, 120) | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $first.AddMinutes($_) }
$opts = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
# Interactive: the browser backend needs your desktop session (it opens a visible Chrome).
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
Register-ScheduledTask -TaskName $names[0] -Action $run -Trigger $triggers -Settings $opts -Principal $principal `
    -Description "Publica los videos del dia (content/queue) - social-publisher-mcp" -Force | Out-Null
Write-Host "OK '$($names[0])' a las $PostTime (+ reintentos 20 min, 1 h, 2 h). Log: $root\logs\social-forge.log"

if ($WithAgentPrep) {
    $claude = (Get-Command claude).Source
    $prompt = "Act as the community-manager agent (.agents/agents/community-manager.md). Daily prep: run queue_status; " +
              "for every video due tomorrow without copy, watch/inspect it and write_post following brand/ and the " +
              "platform-copywriting skill; run publish_due(dry_run=true) and write a short report to logs/prep-latest.md."
    $prep = New-ScheduledTaskAction -Execute $claude -WorkingDirectory $root `
        -Argument "-p `"$prompt`" --permission-mode acceptEdits --allowedTools `"mcp__social-forge__*,Read,Write,Glob,Grep`""
    Register-ScheduledTask -TaskName $names[1] -Action $prep -Trigger (New-ScheduledTaskTrigger -Daily -At 21:00) `
        -Settings $opts -Principal $principal -Description "Escribe copys faltantes para manana" -Force | Out-Null
    Write-Host "OK '$($names[1])' a las 21:00."
}
Write-Host "Recuerda: Configuracion > Energia > permitir temporizadores de reactivacion, o la PC no despertara."
