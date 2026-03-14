param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonCommand,
    [string]$LogDir,
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

function Invoke-Git {
    param(
        [string[]]$Arguments,
        [string]$ErrorMessage
    )

    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw $ErrorMessage
    }
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

function Get-CurrentBranch {
    $branch = (& git branch --show-current).Trim()
    if (-not $branch) {
        throw "Could not detect the current branch. Check out a local branch first."
    }
    return $branch
}

function Get-UpstreamStatus {
    param([string]$Branch)

    $null = & git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
    $hasUpstream = ($LASTEXITCODE -eq 0)
    if (-not $hasUpstream) {
        return @{
            HasUpstream = $false
            Ahead = 0
            Behind = 0
        }
    }

    Invoke-Git -Arguments @("fetch", "origin", $Branch) -ErrorMessage "git fetch failed."
    $counts = (& git rev-list --left-right --count "HEAD...origin/$Branch").Trim()
    if (-not $counts) {
        throw "Could not determine branch divergence against origin/$Branch."
    }

    $parts = $counts -split "\s+"
    if ($parts.Length -lt 2) {
        throw "Unexpected git rev-list output: $counts"
    }

    return @{
        HasUpstream = $true
        Ahead = [int]$parts[0]
        Behind = [int]$parts[1]
    }
}

function Assert-UpstreamSynced {
    param(
        [string]$Branch,
        [string]$Phase,
        [switch]$AllowAhead
    )

    $status = Get-UpstreamStatus -Branch $Branch
    if (-not $status.HasUpstream) {
        return
    }

    $hasBlockingAhead = (-not $AllowAhead) -and ($status.Ahead -gt 0)
    if ($hasBlockingAhead -or $status.Behind -gt 0) {
        throw "Local branch is not in sync with origin/$Branch during $Phase (ahead=$($status.Ahead), behind=$($status.Behind)). Resolve it manually before running the daily pipeline."
    }
}

function Invoke-Main {
    param(
        [string]$ResolvedRepoRoot,
        [hashtable]$PythonSpec
    )

    Set-Location $ResolvedRepoRoot

    Write-Step "Repository: $ResolvedRepoRoot"
    Write-Step "Python: $($PythonSpec.Command)"

    $branch = $null
    if (-not $SkipPush) {
        Write-Step "Checking Git remote and upstream before generation"
        Assert-GitOrigin
        $branch = Get-CurrentBranch
        Assert-UpstreamSynced -Branch $branch -Phase "preflight"
    }

    if (-not $SkipGenerate) {
        Write-Step "Running generate_daily_report.py"
        Invoke-RepoPython -PythonSpec $PythonSpec -Arguments @("generate_daily_report.py")
    }

    if (-not $SkipReleaseCheck) {
        Write-Step "Running release_check.py"
        Invoke-RepoPython -PythonSpec $PythonSpec -Arguments @("release_check.py")
    }

    Write-Step "Staging pages/data"
    Invoke-Git -Arguments @("add", "--all", "--", "pages/data") -ErrorMessage "git add pages/data failed."

    $pendingPagesChanges = (& git status --porcelain -- pages/data)
    if (-not $pendingPagesChanges) {
        Write-Step "No changes detected in pages/data. Nothing to commit."
        return 0
    }

    Write-Step "Committing pages/data updates"
    Invoke-Git -Arguments @("commit", "-m", "chore: update pages data", "--", "pages/data") -ErrorMessage "git commit failed."

    if ($SkipPush) {
        Write-Step "Skipping git push as requested."
        return 0
    }

    Write-Step "Checking Git remote and upstream before push"
    Assert-GitOrigin
    if (-not $branch) {
        $branch = Get-CurrentBranch
    }
    Assert-UpstreamSynced -Branch $branch -Phase "pre-push" -AllowAhead

    $status = Get-UpstreamStatus -Branch $branch
    if ($status.HasUpstream) {
        Write-Step "Pushing to the configured upstream branch"
        Invoke-Git -Arguments @("push") -ErrorMessage "git push failed."
    }
    else {
        Write-Step "Pushing to origin/$branch for the first time"
        Invoke-Git -Arguments @("push", "-u", "origin", $branch) -ErrorMessage "git push failed."
    }

    Write-Step "Daily pipeline completed."
    return 0
}

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
$pythonSpec = Resolve-PythonSpec
$resolvedLogDir = if ($LogDir) {
    $LogDir
}
else {
    Join-Path $resolvedRepoRoot "logs"
}
$resolvedLogDir = [System.IO.Path]::GetFullPath($resolvedLogDir)
[System.IO.Directory]::CreateDirectory($resolvedLogDir) | Out-Null
$logPath = Join-Path $resolvedLogDir ("daily_pipeline_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$transcriptStarted = $false
$exitCode = 1

try {
    Start-Transcript -Path $logPath -Append | Out-Null
    $transcriptStarted = $true
    Write-Step "Log file: $logPath"
    $exitCode = Invoke-Main -ResolvedRepoRoot $resolvedRepoRoot -PythonSpec $pythonSpec
}
catch {
    Write-Error $_
    $exitCode = 1
}
finally {
    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
    }
}

exit $exitCode
