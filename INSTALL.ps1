param(
    [ValidateSet("IDE","CLI","Both")]
    [string]$Target = "IDE"
)

$ErrorActionPreference = "Stop"
$Source = Join-Path $PSScriptRoot "thalarch-mode"

if (-not (Test-Path $Source)) {
    throw "Plugin folder not found: $Source"
}

function Install-Ide {
    $Root = Join-Path $HOME ".gemini\config\plugins"
    $Dest = Join-Path $Root "thalarch-mode"
    New-Item -ItemType Directory -Force -Path $Root | Out-Null

    if (Test-Path $Dest) {
        $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $Backup = "$Dest.backup-$Stamp"
        Move-Item $Dest $Backup
        Write-Host "Existing Thalarch Mode backed up to: $Backup"
    }

    Copy-Item $Source $Dest -Recurse -Force
    Write-Host "Installed Thalarch 2.0 for Antigravity IDE/2.0:"
    Write-Host "  $Dest"
}

function Install-Cli {
    $Agy = Get-Command agy -ErrorAction SilentlyContinue
    if (-not $Agy) {
        throw "The 'agy' command was not found in PATH. Install/use Antigravity CLI or run with -Target IDE."
    }

    & agy plugin install $Source
    if ($LASTEXITCODE -ne 0) {
        throw "agy plugin install failed with exit code $LASTEXITCODE"
    }
    Write-Host "Installed Thalarch 2.0 for Antigravity CLI."
    & agy plugin list
}

switch ($Target) {
    "IDE"  { Install-Ide }
    "CLI"  { Install-Cli }
    "Both" { Install-Ide; Install-Cli }
}

Write-Host ""
Write-Host "Next:"
Write-Host "1. Restart/reload Antigravity."
Write-Host "2. Open the Agents panel and look for 'thalarch-orchestrator'."
Write-Host "3. Ask: 'Use Thalarch Mode for this task.'"
