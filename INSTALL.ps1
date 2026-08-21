param(
    [ValidateSet("IDE","CLI","Both")]
    [string]$Target = "IDE"
)

$ErrorActionPreference = "Stop"
$Source = Join-Path $PSScriptRoot "thalarch-mode"
$LockTool = Join-Path $PSScriptRoot "scripts\security\behavior_lock.py"

if (-not (Test-Path $Source)) {
    throw "Plugin folder not found: $Source"
}

function Test-Python3 {
    foreach ($candidate in @("python3", "python")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                & $candidate -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
                if ($LASTEXITCODE -eq 0) { return $true }
            } catch {}
        }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
            if ($LASTEXITCODE -eq 0) { return $true }
        } catch {}
    }
    return $false
}

function Invoke-ThalarchPython {
    param([string[]]$Arguments)
    foreach ($candidate in @("python3", "python")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            & $candidate @Arguments
            if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
            return
        }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 @Arguments
        if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
        return
    }
    throw "Python 3 was not found."
}

if (-not (Test-Python3)) {
    throw "Thalarch 1.0.0 requires Python 3.10+ for its hard anti-hallucination hooks. Install Python 3 and rerun this installer."
}
if (-not (Test-Path $LockTool)) {
    throw "Behavior-lock tool not found: $LockTool"
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
    Invoke-ThalarchPython @($LockTool, "write", $Dest)
    Invoke-ThalarchPython @($LockTool, "verify", $Dest)
    Write-Host "Installed Thalarch 1.0.0 for Antigravity IDE:"
    Write-Host "  $Dest"
    Write-Host "Hard anti-hallucination evidence gates: ENABLED"
    Write-Host "Behavior integrity lock: VERIFIED"
}

function Install-Cli {
    $Agy = Get-Command agy -ErrorAction SilentlyContinue
    if (-not $Agy) {
        throw "The 'agy' command was not found in PATH. Install/use Antigravity CLI or run with -Target IDE."
    }

    $SourceLock = Join-Path $Source "behavior-lock.json"
    if (Test-Path $SourceLock) {
        throw "Refusing to overwrite an existing source behavior-lock.json: $SourceLock"
    }

    Invoke-ThalarchPython @($LockTool, "write", $Source, "--output", $SourceLock)
    try {
        & agy plugin install $Source
        if ($LASTEXITCODE -ne 0) {
            throw "agy plugin install failed with exit code $LASTEXITCODE"
        }
    } finally {
        Remove-Item $SourceLock -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Installed Thalarch 1.0.0 for Antigravity CLI."
    Write-Host "Hard anti-hallucination evidence gates: ENABLED"
    Write-Host "Behavior integrity lock: STAGED WITH PLUGIN"
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
Write-Host "2. Select 'thalarch-orchestrator' as the primary agent."
Write-Host "3. Ask: 'Use Thalarch for this task.'"
