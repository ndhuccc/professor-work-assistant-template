<#
.SYNOPSIS
  Register Windows Task Scheduler jobs that run repo_check.py around an assignment deadline.

.DESCRIPTION
  Runs on the TEACHER'S computer (the server holds no GitHub credentials).
  Schedule: every 5 minutes from 10 minutes before the deadline until the deadline, at the deadline,
  then +5 minutes and +6 hours (GitHub events can arrive up to 6 hours late).
  Result files are written to -OutDir (must be OUTSIDE any git repository); upload them to LabTube
  (作業 -> Repo -> 上傳查核結果) whenever convenient.

.PARAMETER Roster   roster_hwNN.json downloaded from LabTube
.PARAMETER DueLocal Deadline in Taipei time, e.g. "2026-10-20 23:59"
.PARAMETER OutDir   Folder for result files (outside git)
.PARAMETER Remove   Remove the jobs created for this roster instead of creating them

.EXAMPLE
  .\schedule_repo_check.ps1 -Roster C:\labtube\roster_hw01.json -DueLocal "2026-10-20 23:59" -OutDir C:\labtube\outbox
#>
param(
  [Parameter(Mandatory = $true)][string]$Roster,
  [Parameter(Mandatory = $true)][string]$DueLocal,
  [Parameter(Mandatory = $true)][string]$OutDir,
  [string]$Python = "python",
  [switch]$Remove
)

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "repo_check.py"
$rosterFull = (Resolve-Path $Roster).Path
$prefix = "LabTube-repocheck-" + [IO.Path]::GetFileNameWithoutExtension($rosterFull)

if ($Remove) {
  Get-ScheduledTask | Where-Object { $_.TaskName -like "$prefix*" } | Unregister-ScheduledTask -Confirm:$false
  Write-Host "Removed jobs starting with $prefix"
  return
}

$due = [datetime]::ParseExact($DueLocal, "yyyy-MM-dd HH:mm", $null)
$times = @()
for ($m = -10; $m -le 0; $m += 5) { $times += $due.AddMinutes($m) }
$times += $due.AddMinutes(5)
$times += $due.AddHours(6)
$times = $times | Where-Object { $_ -gt (Get-Date) } | Sort-Object -Unique
if (-not $times) { throw "All scheduled times are already in the past." }

$null = New-Item -ItemType Directory -Force -Path $OutDir
$n = 0
foreach ($t in $times) {
  $n++
  $action = New-ScheduledTaskAction -Execute $Python `
    -Argument "`"$script`" --roster `"$rosterFull`" --out `"$OutDir`""
  $trigger = New-ScheduledTaskTrigger -Once -At $t
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
  Register-ScheduledTask -TaskName ("{0}-{1:00}" -f $prefix, $n) -Action $action -Trigger $trigger `
    -Settings $settings -Force | Out-Null
  Write-Host ("Scheduled {0:yyyy-MM-dd HH:mm}" -f $t)
}
Write-Host "Done. $n jobs registered. The computer must be on and connected at those times (StartWhenAvailable runs missed jobs once it wakes)."
Write-Host "Check 'gh auth status' works in the same user account the jobs run as."
