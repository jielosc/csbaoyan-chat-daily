param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonCommand,
    [string]$LogDir,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PipelineArgs
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

    $previousPythonUnbuffered = $env:PYTHONUNBUFFERED
    $previousPythonIOEncoding = $env:PYTHONIOENCODING
    $previousConsoleOutputEncoding = [Console]::OutputEncoding
    $previousConsoleInputEncoding = [Console]::InputEncoding
    $previousOutputEncoding = $OutputEncoding
    $exitCode = 0
 
    try {
        $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
        [Console]::OutputEncoding = $utf8NoBom
        [Console]::InputEncoding = $utf8NoBom
        $OutputEncoding = $utf8NoBom

        $env:PYTHONUNBUFFERED = "1"
        $env:PYTHONIOENCODING = "utf-8"
        & $PythonSpec.Command @($PythonSpec.PrefixArgs) @Arguments 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.ToString()
            }
            else {
                Write-Host $_
            }
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        if ($null -eq $previousPythonUnbuffered) {
            Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue
        }
        else {
            $env:PYTHONUNBUFFERED = $previousPythonUnbuffered
        }

        if ($null -eq $previousPythonIOEncoding) {
            Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
        }
        else {
            $env:PYTHONIOENCODING = $previousPythonIOEncoding
        }

        [Console]::OutputEncoding = $previousConsoleOutputEncoding
        [Console]::InputEncoding = $previousConsoleInputEncoding
        $OutputEncoding = $previousOutputEncoding
    }

    if ($exitCode -ne 0) {
        throw "Command failed: $($Arguments -join ' ')"
    }
}

function Invoke-Main {
    param(
        [string]$ResolvedRepoRoot,
        [hashtable]$PythonSpec,
        [string[]]$ForwardedArgs
    )

    Set-Location $ResolvedRepoRoot

    Write-Step "Repository: $ResolvedRepoRoot"
    Write-Step "Python: $($PythonSpec.Command)"
    Write-Step "Delegating to Python CLI"
    $previousPythonPath = $env:PYTHONPATH
    $pythonPathPrefix = Join-Path $ResolvedRepoRoot "src"
    $env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($previousPythonPath)) {
        $pythonPathPrefix
    }
    else {
        "$pythonPathPrefix$([IO.Path]::PathSeparator)$previousPythonPath"
    }
    try {
        Invoke-RepoPython -PythonSpec $PythonSpec -Arguments @("-m", "csbaoyan_daily.cli", "pipeline", "--repo-root", $ResolvedRepoRoot) + $ForwardedArgs
    }
    finally {
        if ([string]::IsNullOrWhiteSpace($previousPythonPath)) {
            Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
        }
        else {
            $env:PYTHONPATH = $previousPythonPath
        }
    }
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
    $exitCode = Invoke-Main -ResolvedRepoRoot $resolvedRepoRoot -PythonSpec $pythonSpec -ForwardedArgs $PipelineArgs
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
