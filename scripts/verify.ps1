param(
    [switch]$Offline
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$script:CurrentStep = "BOOTSTRAP"
$script:FailureReported = $false


function Save-Environment {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Names
    )

    $snapshot = @()
    foreach ($name in $Names) {
        $value = [Environment]::GetEnvironmentVariable($name, "Process")
        $snapshot += [PSCustomObject]@{
            Name = $name
            Exists = $null -ne $value
            Value = $value
        }
    }
    return $snapshot
}


function Restore-Environment {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Snapshot
    )

    foreach ($entry in $Snapshot) {
        if ($entry.Exists) {
            [Environment]::SetEnvironmentVariable($entry.Name, $entry.Value, "Process")
        }
        else {
            [Environment]::SetEnvironmentVariable($entry.Name, $null, "Process")
        }
    }
}


function Assert-EnvironmentRestored {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Snapshot
    )

    foreach ($entry in $Snapshot) {
        $current = [Environment]::GetEnvironmentVariable($entry.Name, "Process")
        $exists = $null -ne $current
        if ($exists -ne $entry.Exists) {
            throw "VERIFY_ENVIRONMENT_RESTORE_FAILED"
        }
        if ($exists -and $current -cne $entry.Value) {
            throw "VERIFY_ENVIRONMENT_RESTORE_FAILED"
        }
    }
}


function Set-EnvironmentValue {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Names,

        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    foreach ($name in $Names) {
        [Environment]::SetEnvironmentVariable($name, $Value, "Process")
    }
}


function Enter-RunnerEnvironment {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$UseOffline
    )

    $names = @("PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN")
    if ($UseOffline) {
        $names += "PNPM_CONFIG_OFFLINE"
    }
    $snapshot = @(Save-Environment -Names $names)
    try {
        Set-EnvironmentValue -Names @("PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN") -Value "false"
        if ($UseOffline) {
            Set-EnvironmentValue -Names @("PNPM_CONFIG_OFFLINE") -Value "true"
        }
    }
    catch {
        Restore-Environment -Snapshot $snapshot
        Assert-EnvironmentRestored -Snapshot $snapshot
        throw
    }
    return $snapshot
}


function Exit-RunnerEnvironment {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Snapshot
    )

    Restore-Environment -Snapshot $Snapshot
    Assert-EnvironmentRestored -Snapshot $Snapshot
}


function Assert-PowerShellVersion {
    $stepId = "PREFLIGHT-POWERSHELL"
    $script:CurrentStep = $stepId
    Write-Output "[START] step=$stepId"
    if ($PSVersionTable.PSVersion -lt [version]"5.1") {
        throw "VERIFY_POWERSHELL_VERSION_UNSUPPORTED"
    }
    Write-Output "[PASS] step=$stepId"
}


function Invoke-NativeStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StepId,

        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [string[]]$Arguments = @(),

        [string]$ExpectedOutput,

        [string]$ExpectedPattern
    )

    $script:CurrentStep = $StepId
    Write-Output "[START] step=$StepId"

    $previousPreference = $ErrorActionPreference
    try {
        if ([IO.Path]::IsPathRooted($Executable) -or $Executable.Contains("\") -or $Executable.Contains("/")) {
            if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
                throw "VERIFY_EXECUTABLE_MISSING"
            }
            $resolvedExecutable = (Resolve-Path -LiteralPath $Executable).Path
        }
        else {
            $resolvedCommands = @(Get-Command $Executable -CommandType Application -ErrorAction Stop)
            $resolvedExecutable = $resolvedCommands[0].Source
        }

        $ErrorActionPreference = "SilentlyContinue"
        $global:LASTEXITCODE = $null
        $captured = @(& $resolvedExecutable @Arguments 2>&1)
        $childExitCode = $LASTEXITCODE
        if ($null -eq $childExitCode) {
            throw "VERIFY_INVOCATION_FAILED"
        }
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }

    if ($childExitCode -ne 0) {
        $script:FailureReported = $true
        Write-Output "[FAIL] step=$StepId reason=child-exit code=$childExitCode"
        $failure = New-Object System.Exception("VERIFY_NATIVE_STEP_FAILED")
        $failure.Data["VerifyExitCode"] = [int]$childExitCode
        throw $failure
    }

    if ($PSBoundParameters.ContainsKey("ExpectedOutput") -or $PSBoundParameters.ContainsKey("ExpectedPattern")) {
        $actualOutput = (($captured | ForEach-Object { $_.ToString() }) -join "`n").Trim()
        if ($PSBoundParameters.ContainsKey("ExpectedOutput")) {
            $matches = $actualOutput -ceq $ExpectedOutput
        }
        else {
            $matches = $actualOutput -cmatch $ExpectedPattern
        }
        if (-not $matches) {
            throw "VERIFY_VERSION_MISMATCH"
        }
    }

    Write-Output "[PASS] step=$StepId"
}


function Invoke-SentinelWebBuild {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sentinel,

        [Parameter(Mandatory = $true)]
        [string]$StepId
    )

    $names = @(
        "SEJONG_WEB_SECRET_SENTINEL",
        "DATABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "LLM_API_KEY",
        "CONTEXT_TOKEN_SECRET",
        "DEEPSEEK_API_KEY"
    )
    $snapshot = @(Save-Environment -Names $names)
    try {
        Set-EnvironmentValue -Names $names -Value $Sentinel
        Invoke-NativeStep -StepId $StepId -Executable "corepack.cmd" -Arguments @(
            "pnpm", "--filter", "@sejong-ai/web", "build"
        )
    }
    finally {
        Restore-Environment -Snapshot $snapshot
        Assert-EnvironmentRestored -Snapshot $snapshot
    }
}


function Invoke-SentinelBundleScan {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sentinel,

        [Parameter(Mandatory = $true)]
        [string]$StepId
    )

    $names = @("SEJONG_WEB_SECRET_SENTINEL")
    $snapshot = @(Save-Environment -Names $names)
    try {
        Set-EnvironmentValue -Names $names -Value $Sentinel
        Invoke-NativeStep -StepId $StepId -Executable "node" -Arguments @(
            "scripts/check_web_bundle_secrets.mjs", "apps/web/.next"
        )
    }
    finally {
        Restore-Environment -Snapshot $snapshot
        Assert-EnvironmentRestored -Snapshot $snapshot
    }
}


if ($args.Count -ne 0) {
    Write-Output "[FAIL] step=VALIDATE-ARGUMENTS reason=exception code=2"
    exit 2
}

if ($MyInvocation.InvocationName -eq ".") {
    return
}


$exitCode = 0
$locationPushed = $false
$runnerEnvironmentSnapshot = @()

try {
    $repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
    Push-Location -LiteralPath $repoRoot
    $locationPushed = $true

    $runnerEnvironmentSnapshot = @(Enter-RunnerEnvironment -UseOffline ([bool]$Offline))

    Assert-PowerShellVersion
    Invoke-NativeStep -StepId "PREFLIGHT-NODE" -Executable "node" -Arguments @(
        "--version"
    ) -ExpectedOutput "v24.12.0"
    Invoke-NativeStep -StepId "PREFLIGHT-PNPM" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--version"
    ) -ExpectedOutput "11.13.0"

    $repoUv = Join-Path $repoRoot ".tools\uv\uv.exe"
    if (Test-Path -LiteralPath $repoUv -PathType Leaf) {
        $uvExecutable = $repoUv
    }
    else {
        $uvExecutable = "uv"
    }
    $expectedUvVersion = "uv 0.11.28"
    $uvVersionPattern = "^" + [regex]::Escape($expectedUvVersion) + " \([0-9A-Za-z.-]+ [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9A-Za-z_.-]+\)$"
    Invoke-NativeStep -StepId "PREFLIGHT-UV" -Executable $uvExecutable -Arguments @(
        "--version"
    ) -ExpectedPattern $uvVersionPattern

    $PnpmInstallArguments = @("pnpm", "install", "--frozen-lockfile", "--ignore-scripts")
    if ($Offline) {
        $PnpmInstallArguments += "--offline"
    }
    Invoke-NativeStep -StepId "INSTALL-PNPM" -Executable "corepack.cmd" -Arguments $PnpmInstallArguments

    $UvSyncArguments = @("sync", "--project", "apps/api", "--frozen")
    if ($Offline) {
        $UvSyncArguments += "--offline"
    }
    Invoke-NativeStep -StepId "SYNC-API" -Executable $uvExecutable -Arguments $UvSyncArguments

    $apiPython = Join-Path $repoRoot "apps\api\.venv\Scripts\python.exe"
    Invoke-NativeStep -StepId "PREFLIGHT-API-PYTHON" -Executable $apiPython -Arguments @(
        "--version"
    ) -ExpectedOutput "Python 3.12.13"

    Invoke-NativeStep -StepId "TEST-ROOT" -Executable $apiPython -Arguments @(
        "-B", "-m", "unittest", "discover", "-s", "scripts/tests", "-p", "test_*.py", "-v"
    )
    $data001DraftDirectory = Join-Path $repoRoot "data\staging\data-001\0.1.0-draft.1"
    $data001CanonicalMarker = Join-Path $repoRoot "data\schemas\data-001\v1\approved-source-matrix.json"
    $data001CanonicalSchema = Join-Path $repoRoot "data\schemas\data-001\v1\approval-manifest.schema.json"
    if (
        -not (Test-Path -LiteralPath $data001DraftDirectory -PathType Container) -or
        -not (Test-Path -LiteralPath $data001CanonicalMarker -PathType Leaf) -or
        -not (Test-Path -LiteralPath $data001CanonicalSchema -PathType Leaf)
    ) {
        throw "[FAIL] step=VALIDATE-DATA-001 reason=DATA-001 canonical marker/schema missing"
    }
    Write-Output "[PASS] step=VALIDATE-DATA-001 reason=DATA-001 canonical marker/schema present"
    Invoke-NativeStep -StepId "VALIDATE-DATA-001" -Executable $apiPython -Arguments @(
        "-B", "scripts/validate_data_staging.py", "validate", "--draft-dir", $data001DraftDirectory
    )
    Invoke-NativeStep -StepId "LINT-WEB" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--filter", "@sejong-ai/web", "lint"
    )
    Invoke-NativeStep -StepId "TYPECHECK-WEB" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--filter", "@sejong-ai/web", "typecheck"
    )
    Invoke-NativeStep -StepId "TEST-WEB" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--filter", "@sejong-ai/web", "test"
    )
    $webE2eInstallArguments = @(
        "pnpm", "--dir", "tools/web-e2e", "install", "--frozen-lockfile", "--ignore-scripts"
    )
    if ($Offline) {
        $webE2eInstallArguments += "--offline"
    }
    Invoke-NativeStep -StepId "INSTALL-WEB-E2E" -Executable "corepack.cmd" -Arguments $webE2eInstallArguments
    Invoke-NativeStep -StepId "CHECK-WEB-PROD-DEPENDENCY-BOUNDARY" -Executable "node" -Arguments @(
        "scripts/check_web_prod_dependency_boundary.mjs"
    )

    $syntheticSentinel = "sejong-web-build-boundary-sentinel-v1"
    Invoke-SentinelWebBuild -Sentinel $syntheticSentinel -StepId "BUILD-WEB-SENTINEL"

    $uvRunArguments = @("run", "--directory", "apps/api", "--frozen")
    if ($Offline) {
        $uvRunArguments += "--offline"
    }
    Invoke-NativeStep -StepId "FORMAT-API" -Executable $uvExecutable -Arguments (
        $uvRunArguments + @("ruff", "format", "--check", "src", "tests")
    )
    Invoke-NativeStep -StepId "LINT-API" -Executable $uvExecutable -Arguments (
        $uvRunArguments + @("ruff", "check", "src", "tests")
    )
    Invoke-NativeStep -StepId "TYPECHECK-API" -Executable $uvExecutable -Arguments (
        $uvRunArguments + @("mypy", "src", "tests")
    )
    Invoke-NativeStep -StepId "TEST-API" -Executable $uvExecutable -Arguments (
        $uvRunArguments + @("pytest", "-q", "-p", "no:cacheprovider")
    )

    Invoke-NativeStep -StepId "CHECK-CONTRACT-GENERATED" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--filter", "@sejong-ai/shared-contracts", "generate:check"
    )
    Invoke-NativeStep -StepId "GENERATE-CONTRACT" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--filter", "@sejong-ai/shared-contracts", "generate"
    )
    Invoke-NativeStep -StepId "DIFF-CONTRACT-GENERATED" -Executable "git" -Arguments @(
        "diff", "--exit-code", "--", "packages/shared-contracts/src/generated/api.ts"
    )
    Invoke-NativeStep -StepId "TEST-CONTRACT" -Executable "corepack.cmd" -Arguments @(
        "pnpm", "--filter", "@sejong-ai/shared-contracts", "test"
    )

    Invoke-NativeStep -StepId "SCAN-REPOSITORY-SECRETS" -Executable "powershell.exe" -Arguments @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/check_secret_patterns.ps1"
    )
    Invoke-SentinelBundleScan -Sentinel $syntheticSentinel -StepId "SCAN-WEB-BUNDLE"
    Invoke-NativeStep -StepId "VALIDATE-PACKAGE" -Executable $apiPython -Arguments @(
        "-B", "scripts/validate_codex_package.py"
    )
    Invoke-NativeStep -StepId "CHECK-DIFF" -Executable "git" -Arguments @(
        "diff", "--check"
    )

}
catch {
    if ($_.Exception.Data.Contains("VerifyExitCode")) {
        $exitCode = [int]$_.Exception.Data["VerifyExitCode"]
    }
    else {
        $exitCode = 2
        if (-not $script:FailureReported) {
            Write-Output "[FAIL] step=$script:CurrentStep reason=exception code=2"
            $script:FailureReported = $true
        }
    }
}
finally {
    if ($runnerEnvironmentSnapshot.Count -gt 0) {
        try {
            Exit-RunnerEnvironment -Snapshot $runnerEnvironmentSnapshot
        }
        catch {
            $exitCode = 2
            Write-Output "[FAIL] step=RESTORE-RUNNER-ENV reason=exception code=2"
        }
    }
    if ($locationPushed) {
        try {
            Pop-Location
        }
        catch {
            $exitCode = 2
            Write-Output "[FAIL] step=RESTORE-LOCATION reason=exception code=2"
        }
    }
}

if ($exitCode -eq 0) {
    Write-Output "[PASS] verification=complete"
}

exit $exitCode
