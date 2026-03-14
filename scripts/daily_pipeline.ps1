param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonCommand,
    [switch]$SkipGenerate,
    [switch]$SkipReleaseCheck,
    [switch]$SkipPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Resolve-PythonSpec {
    if ($PythonCommand) {
        return @{
            Command = $PythonCommand
            PrefixArgs = @()
        }
    }

    $candidatePaths = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidatePaths) {
        if (Test-Path $candidate) {
            return @{
                Command = $candidate
                PrefixArgs = @()
            }
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{
            Command = $python.Source
            PrefixArgs = @()
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @{
            Command = $pyLauncher.Source
            PrefixArgs = @("-3")
        }
    }

    throw "Python was not found. Install Python first, or pass the interpreter path with -PythonCommand."
}

function Invoke-RepoPython {
    param(
        [hashtable]$PythonSpec,
        [string[]]$Arguments
    )

    & $PythonSpec.Command @($PythonSpec.PrefixArgs) @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $($Arguments -join ' ')"
    }
}

function Assert-GitOrigin {
    $null = & git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Git remote origin is not configured. Run: git remote add origin <your-github-repo-url>"
    }
}

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
Set-Location $resolvedRepoRoot

$pythonSpec = Resolve-PythonSpec
Write-Step "Repository: $resolvedRepoRoot"
Write-Step "Python: $($pythonSpec.Command)"

if (-not $SkipGenerate) {
    Write-Step "Running generate_daily_report.py"
    Invoke-RepoPython -PythonSpec $pythonSpec -Arguments @("generate_daily_report.py")
}

if (-not $SkipReleaseCheck) {
    Write-Step "Running release_check.py"
    Invoke-RepoPython -PythonSpec $pythonSpec -Arguments @("release_check.py")
}

Write-Step "Staging pages/data"
& git add --all -- pages/data
if ($LASTEXITCODE -ne 0) {
    throw "git add pages/data failed."
}

$pendingPagesChanges = (& git status --porcelain -- pages/data)
if (-not $pendingPagesChanges) {
    Write-Step "No changes detected in pages/data. Skipping commit and push."
    exit 0
}

Write-Step "Committing pages/data updates"
& git commit -m "chore: update pages data" -- pages/data
if ($LASTEXITCODE -ne 0) {
    throw "git commit failed."
}

if ($SkipPush) {
    Write-Step "Skipping git push as requested."
    exit 0
}

Write-Step "Checking Git remote and branch"
Assert-GitOrigin
$branch = (& git branch --show-current).Trim()
if (-not $branch) {
    throw "Could not detect the current branch. Check out a local branch first."
}

$null = & git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
$hasUpstream = ($LASTEXITCODE -eq 0)

if ($hasUpstream) {
    Write-Step "Pushing to the configured upstream branch"
    & git push
}
else {
    Write-Step "Pushing to origin/$branch for the first time"
    & git push -u origin $branch
}

if ($LASTEXITCODE -ne 0) {
    throw "git push failed."
}

Write-Step "Daily pipeline completed."
