# =============================================================================
#  Claude autonomous task runner — Windows PowerShell port of runner.sh
# -----------------------------------------------------------------------------
#  Reads task specs (.md) from .\pending\, runs each one through Claude in
#  headless mode (claude -p), writes artefacts into .\output\<task>\,
#  then moves the spec to .\completed\ or .\failed\.
#
#  USAGE
#  -----
#  Watch it run in this terminal:
#     cd C:\Users\Max\claude_agent\task_runner
#     pwsh -File runner.ps1
#
#  Run minimised in a separate window (returns immediately):
#     Start-Process pwsh -ArgumentList "-NonInteractive -File `"$PWD\runner.ps1`"" -WindowStyle Minimized
#
#  Watch live progress (from another terminal):
#     Get-Content .\logs\<task-name>.log -Wait
#
#  Stop early:
#     Get-Process pwsh | Where-Object CommandLine -like '*runner.ps1*' | Stop-Process
#
#  PREREQS
#  -------
#  - Claude Code CLI installed and logged in (claude must be on PATH).
#  - At least one .md spec inside .\pending\
# =============================================================================

param(
    [int]$TimeoutMinutes = 60   # override: pwsh -File runner.ps1 -TimeoutMinutes 120
)

$ErrorActionPreference = 'Stop'

$Root       = $PSScriptRoot
$Pending    = Join-Path $Root "pending"
$Completed  = Join-Path $Root "completed"
$Failed     = Join-Path $Root "failed"
$Logs       = Join-Path $Root "logs"
$Out        = Join-Path $Root "output"
$SharedFile = Join-Path $Root "SHARED_GUIDANCE.md"

foreach ($d in @($Pending, $Completed, $Failed, $Logs, $Out)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

# One-time wrapper script: reads prompt from a file, calls claude -p.
# Lives in TEMP so it can be reused across tasks without path issues.
# We write it fresh each run to stay up-to-date.
$wrapperPath = Join-Path $env:TEMP "claude_runner_invoke.ps1"
@'
param($PromptFile, $AllowedTools)
$p = Get-Content $PromptFile -Raw
& claude -p $p --permission-mode acceptEdits --allowed-tools $AllowedTools
'@ | Out-File $wrapperPath -Encoding utf8

# Tools Claude is allowed to use inside tasks (tightened for safety)
$allowedTools = "Read,Grep,Glob,Edit,Write,Task,WebSearch,WebFetch," +
    "PowerShell(Get-ChildItem:*),PowerShell(Get-Content:*),PowerShell(Select-String:*)," +
    "PowerShell(Measure-Object:*),PowerShell(Where-Object:*),PowerShell(Sort-Object:*)," +
    "PowerShell(Select-Object:*),PowerShell(Out-File:*),PowerShell(Set-Content:*)," +
    "PowerShell(New-Item:*),PowerShell(Copy-Item:*),PowerShell(Move-Item:*)," +
    "PowerShell(Get-Date:*),PowerShell(Write-Output:*),PowerShell(Write-Host:*)"

$startTs       = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$pendingCount  = @(Get-ChildItem "$Pending\*.md" -ErrorAction SilentlyContinue).Count
Write-Host "============================================="
Write-Host "  Claude task runner — start $startTs"
Write-Host "  Pending: $pendingCount task(s)"
Write-Host "  Timeout per task: $TimeoutMinutes min"
Write-Host "  Output dir: $Out"
Write-Host "============================================="

$shared = ""
if (Test-Path $SharedFile) { $shared = Get-Content $SharedFile -Raw }

while ($true) {
    $next = Get-ChildItem "$Pending\*.md" -ErrorAction SilentlyContinue |
            Sort-Object Name | Select-Object -First 1

    if (-not $next) {
        Write-Host ""
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] No more pending tasks. DONE."
        break
    }

    $name    = [System.IO.Path]::GetFileNameWithoutExtension($next.Name)
    $log     = Join-Path $Logs "$name.log"
    $logErr  = "$log.err"
    $taskOut = Join-Path $Out $name
    New-Item -ItemType Directory -Force -Path $taskOut | Out-Null

    Write-Host ""
    Write-Host "---------------------------------------------"
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] START  $name"
    Write-Host "  spec: $($next.FullName)"
    Write-Host "  out:  $taskOut"
    Write-Host "  log:  $log"
    Write-Host "---------------------------------------------"

    $spec = Get-Content $next.FullName -Raw

    $prompt = @"
You are an autonomous task runner. The human who queued this task is away and
will review your output later. Work end-to-end and produce finished artefacts.

OUTPUT DIRECTORY: $taskOut
Write ALL generated files there, using absolute paths. NEVER write outside it.
DO NOT publish anything, push to git, deploy, or hit live/production systems.
If something is ambiguous, make a sensible decision, note it, and keep going --
do not stop to ask questions (there is nobody to answer).

When finished:
1. Make sure every artefact is a complete file inside $taskOut.
2. Write $taskOut\SUMMARY.md describing what you did, decisions, and any TODOs.
3. Print "TASK COMPLETE" as the very LAST line of your reply.

============================================
SHARED GUIDANCE (applies to every task)
============================================

$shared

============================================
TASK SPEC
============================================

$spec
"@

    # Write the full prompt to a temp file. The wrapper script reads it back and
    # passes it to `claude -p` via PowerShell's call operator, which handles
    # multi-line strings reliably without Start-Process quoting issues.
    $promptFile = Join-Path $env:TEMP "claude_prompt_$name.txt"
    $prompt | Out-File $promptFile -Encoding utf8

    # Run the wrapper via pwsh so we can control timeout with WaitForExit
    $proc = Start-Process -FilePath "pwsh" `
        -ArgumentList @(
            "-NonInteractive",
            "-File", $wrapperPath,
            "-PromptFile", $promptFile,
            "-AllowedTools", $allowedTools
        ) `
        -RedirectStandardOutput $log `
        -RedirectStandardError  $logErr `
        -NoNewWindow `
        -PassThru

    $timeoutMs = $TimeoutMinutes * 60 * 1000
    $finished  = $proc.WaitForExit($timeoutMs)

    Remove-Item $promptFile -ErrorAction SilentlyContinue

    if (-not $finished) {
        try { $proc.Kill() } catch {}
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] TIMEOUT $name — killed after $TimeoutMinutes min"
        Move-Item $next.FullName $Failed
        continue
    }

    if ($proc.ExitCode -eq 0) {
        Move-Item $next.FullName $Completed
        $filesCount = @(Get-ChildItem $taskOut -Recurse -File -ErrorAction SilentlyContinue).Count
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] DONE   $name (exit 0, $filesCount file(s))"
    } else {
        Move-Item $next.FullName $Failed
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] FAILED $name (exit $($proc.ExitCode)) — see $log"
    }
}

$endTs       = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$doneCount   = @(Get-ChildItem "$Completed\*.md" -ErrorAction SilentlyContinue).Count
$failedCount = @(Get-ChildItem "$Failed\*.md" -ErrorAction SilentlyContinue).Count
Write-Host ""
Write-Host "============================================="
Write-Host "  Runner finished at $endTs"
Write-Host "  Completed: $doneCount"
Write-Host "  Failed:    $failedCount"
Write-Host "  Output:    $Out"
Write-Host "============================================="
