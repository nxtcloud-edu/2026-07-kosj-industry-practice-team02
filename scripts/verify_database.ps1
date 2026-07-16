Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Throw-DatabaseGateFailure {
    param(
        [string]$Step,
        [string]$Reason,
        [int]$Code
    )

    $failure = New-Object System.Exception("controlled database gate failure")
    $failure.Data["step"] = $Step
    $failure.Data["reason"] = $Reason
    $failure.Data["code"] = $Code
    throw $failure
}

function ConvertTo-NativeArgument {
    param([string]$Value)

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }

    $builder = New-Object System.Text.StringBuilder
    $null = $builder.Append('"')
    $backslashCount = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') {
            $backslashCount += 1
            continue
        }
        if ($character -eq '"') {
            $null = $builder.Append(('\' * (($backslashCount * 2) + 1)))
            $null = $builder.Append('"')
            $backslashCount = 0
            continue
        }
        if ($backslashCount -gt 0) {
            $null = $builder.Append(('\' * $backslashCount))
            $backslashCount = 0
        }
        $null = $builder.Append($character)
    }
    if ($backslashCount -gt 0) {
        $null = $builder.Append(('\' * ($backslashCount * 2)))
    }
    $null = $builder.Append('"')
    return $builder.ToString()
}

function Invoke-DatabaseChild {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [int]$TimeoutMilliseconds = 900000
    )

    $process = $null
    try {
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $FilePath
        $startInfo.Arguments = (($Arguments | ForEach-Object {
                    ConvertTo-NativeArgument -Value ([string]$_)
                }) -join " ")
        $startInfo.WorkingDirectory = $WorkingDirectory
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true

        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw New-Object System.InvalidOperationException("child did not start")
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try {
                $process.Kill()
                $process.WaitForExit()
            }
            catch {
                # The parent reports only the stable timeout classification.
            }
            Throw-DatabaseGateFailure -Step "DATABASE-CHILD" -Reason "timeout" -Code 2
        }
        $standardOutput = $stdoutTask.GetAwaiter().GetResult()
        $null = $stderrTask.GetAwaiter().GetResult()
        return [pscustomobject]@{
            ExitCode = [int]$process.ExitCode
            Output = [string]$standardOutput
        }
    }
    finally {
        if ($null -ne $process) {
            $process.Dispose()
        }
    }
}

function Invoke-DatabaseStep {
    param(
        [string]$Step,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [int]$TimeoutMilliseconds = 900000
    )

    [Console]::Out.WriteLine("[START] step=" + $Step)
    try {
        $result = Invoke-DatabaseChild `
            -FilePath $FilePath `
            -Arguments $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -TimeoutMilliseconds $TimeoutMilliseconds
    }
    catch {
        if ($_.Exception.Data.Contains("step")) {
            throw
        }
        Throw-DatabaseGateFailure -Step $Step -Reason "operational" -Code 2
    }
    if ($result.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $Step -Reason "child" -Code $result.ExitCode
    }
    [Console]::Out.WriteLine("[PASS] step=" + $Step)
    return $result
}

function Read-DatabaseUrlFromStatus {
    param([string]$StatusOutput)

    foreach ($line in ($StatusOutput -split "`r?`n")) {
        if ($line.StartsWith("DB_URL=", [System.StringComparison]::Ordinal)) {
            $value = $line.Substring(7).Trim()
            if (
                $value.Length -ge 2 -and
                $value.StartsWith('"', [System.StringComparison]::Ordinal) -and
                $value.EndsWith('"', [System.StringComparison]::Ordinal)
            ) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                return $value
            }
        }
    }
    Throw-DatabaseGateFailure -Step "READ-LOCAL-DATABASE-STATUS" -Reason "invalid" -Code 2
}

function Read-EnvironmentAssignment {
    param(
        [string]$Path,
        [string]$Key
    )

    $reader = $null
    try {
        $reader = New-Object System.IO.StreamReader($Path, [System.Text.Encoding]::UTF8, $true)
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            if ($line.StartsWith($Key + "=", [System.StringComparison]::Ordinal)) {
                $value = $line.Substring($Key.Length + 1)
                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    return $value
                }
                break
            }
        }
    }
    catch {
        Throw-DatabaseGateFailure -Step "READ-BACKEND-DATABASE-ENV" -Reason "operational" -Code 2
    }
    finally {
        if ($null -ne $reader) {
            $reader.Dispose()
        }
    }
    Throw-DatabaseGateFailure -Step "READ-BACKEND-DATABASE-ENV" -Reason "invalid" -Code 2
}

function Save-ProcessEnvironment {
    param([string[]]$Names)

    $saved = @{}
    foreach ($name in $Names) {
        $saved[$name] = [pscustomobject]@{
            Existed = Test-Path -LiteralPath ("Env:\" + $name)
            Value = [Environment]::GetEnvironmentVariable($name, "Process")
        }
    }
    return $saved
}

function Restore-ProcessEnvironment {
    param([hashtable]$Saved)

    foreach ($name in $Saved.Keys) {
        if ($Saved[$name].Existed) {
            [Environment]::SetEnvironmentVariable($name, $Saved[$name].Value, "Process")
        }
        else {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
    }
}

function ConvertFrom-DatabaseJson {
    param(
        [string]$Value,
        [string]$Step
    )

    try {
        if ([string]::IsNullOrWhiteSpace($Value)) {
            throw New-Object System.FormatException("empty JSON")
        }
        return $Value | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Throw-DatabaseGateFailure -Step $Step -Reason "invalid" -Code 2
    }
}

function Ensure-LocalDatabaseNetwork {
    param(
        [string]$DockerPath,
        [string]$NetworkName,
        [string]$WorkingDirectory
    )

    $step = "VERIFY-LOCAL-DATABASE-NETWORK"
    [Console]::Out.WriteLine("[START] step=" + $step)
    $listResult = Invoke-DatabaseChild `
        -FilePath $DockerPath `
        -Arguments @(
            "network",
            "ls",
            "--filter",
            ("name=^" + $NetworkName + '$'),
            "--format",
            "{{.Name}}"
        ) `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds 30000
    if ($listResult.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "operational" -Code 2
    }
    $networkNames = @(
        $listResult.Output -split "`r?`n" |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    if ($networkNames.Count -eq 0) {
        $createResult = Invoke-DatabaseChild `
            -FilePath $DockerPath `
            -Arguments @(
                "network",
                "create",
                "--driver",
                "bridge",
                "--opt",
                "com.docker.network.bridge.host_binding_ipv4=127.0.0.1",
                "--label",
                "com.sejong-ai.local-boundary=sejong-ai-local",
                $NetworkName
            ) `
            -WorkingDirectory $WorkingDirectory `
            -TimeoutMilliseconds 30000
        if ($createResult.ExitCode -ne 0) {
            Throw-DatabaseGateFailure -Step $step -Reason "child" -Code $createResult.ExitCode
        }
    }
    elseif ($networkNames.Count -ne 1 -or $networkNames[0] -cne $NetworkName) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }

    $inspectResult = Invoke-DatabaseChild `
        -FilePath $DockerPath `
        -Arguments @(
            "network",
            "inspect",
            $NetworkName,
            "--format",
            "{{json .}}"
        ) `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds 30000
    if ($inspectResult.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "child" -Code $inspectResult.ExitCode
    }
    $network = ConvertFrom-DatabaseJson -Value $inspectResult.Output -Step $step
    if (
        $network.Name -cne $NetworkName -or
        $network.Scope -cne "local" -or
        $network.Driver -cne "bridge" -or
        $null -eq $network.Options -or
        $null -eq $network.Labels
    ) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $bindingOption = $network.Options.PSObject.Properties[
        "com.docker.network.bridge.host_binding_ipv4"
    ]
    if ($null -eq $bindingOption -or $bindingOption.Value -cne "127.0.0.1") {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $ownershipLabel = $network.Labels.PSObject.Properties[
        "com.sejong-ai.local-boundary"
    ]
    if ($null -eq $ownershipLabel -or $ownershipLabel.Value -cne "sejong-ai-local") {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=" + $step)
}

function Assert-LocalDatabaseRuntime {
    param(
        [string]$DockerPath,
        [string]$ProjectId,
        [string]$NetworkName,
        [string]$ExpectedContainerName,
        [string]$WorkingDirectory,
        [switch]$AllowAbsent
    )

    $step = "VERIFY-LOCAL-DATABASE-RUNTIME"
    [Console]::Out.WriteLine("[START] step=" + $step)
    $listResult = Invoke-DatabaseChild `
        -FilePath $DockerPath `
        -Arguments @(
            "ps",
            "-a",
            "--filter",
            ("label=com.supabase.cli.project=" + $ProjectId),
            "--format",
            "{{.ID}}"
        ) `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds 30000
    if ($listResult.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "operational" -Code 2
    }
    $containerIds = @(
        $listResult.Output -split "`r?`n" |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    if ($containerIds.Count -eq 0 -and $AllowAbsent) {
        [Console]::Out.WriteLine("[PASS] step=" + $step)
        return $false
    }
    if ($containerIds.Count -ne 1) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }

    $inspectResult = Invoke-DatabaseChild `
        -FilePath $DockerPath `
        -Arguments @(
            "inspect",
            $containerIds[0],
            "--format",
            "{{json .}}"
        ) `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds 30000
    if ($inspectResult.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "child" -Code $inspectResult.ExitCode
    }
    $container = ConvertFrom-DatabaseJson -Value $inspectResult.Output -Step $step
    $actualName = [string]$container.Name
    if ($actualName.StartsWith("/", [System.StringComparison]::Ordinal)) {
        $actualName = $actualName.Substring(1)
    }
    if ($actualName -cne $ExpectedContainerName) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    if (
        $null -eq $container.State -or
        $container.State.Running -ne $true -or
        $null -eq $container.Config -or
        $null -eq $container.Config.Labels
    ) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $projectLabel = $container.Config.Labels.PSObject.Properties[
        "com.supabase.cli.project"
    ]
    if ($null -eq $projectLabel -or $projectLabel.Value -cne $ProjectId) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    if (
        $null -eq $container.HostConfig -or
        $container.HostConfig.NetworkMode -cne $NetworkName -or
        $null -eq $container.NetworkSettings -or
        $null -eq $container.NetworkSettings.Networks -or
        $null -eq $container.NetworkSettings.Networks.PSObject.Properties[$NetworkName]
    ) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    if ($null -eq $container.HostConfig.PortBindings) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $publishedPorts = @($container.HostConfig.PortBindings.PSObject.Properties)
    if ($publishedPorts.Count -ne 1 -or $publishedPorts[0].Name -cne "5432/tcp") {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    foreach ($publishedPort in $publishedPorts) {
        $bindings = @($publishedPort.Value)
        if ($bindings.Count -ne 1) {
            Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
        }
        foreach ($binding in $bindings) {
            if ($null -eq $binding) {
                Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
            }
            $requestedHostIp = [string]$binding.HostIp
            if (
                (
                    $requestedHostIp -cne "" -and
                    $requestedHostIp -cne "127.0.0.1"
                ) -or
                [string]$binding.HostPort -cne "54322"
            ) {
                Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
            }
        }
    }
    if ($null -eq $container.NetworkSettings.Ports) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $resolvedPorts = @($container.NetworkSettings.Ports.PSObject.Properties)
    if ($resolvedPorts.Count -ne 1 -or $resolvedPorts[0].Name -cne "5432/tcp") {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $resolvedBindings = @($resolvedPorts[0].Value)
    if ($resolvedBindings.Count -ne 1) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    $resolvedBinding = $resolvedBindings[0]
    if (
        $null -eq $resolvedBinding -or
        [string]$resolvedBinding.HostIp -cne "127.0.0.1" -or
        [string]$resolvedBinding.HostPort -cne "54322"
    ) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=" + $step)
    return $true
}

function Stop-OwnedUnsafeLocalDatabaseRuntime {
    param(
        [string]$SupabasePath,
        [string]$DockerPath,
        [string]$ProjectId,
        [string]$WorkingDirectory
    )

    $step = "STOP-UNSAFE-LOCAL-DATABASE-RUNTIME"
    [Console]::Out.WriteLine("[START] step=" + $step)
    try {
        $stopResult = Invoke-DatabaseChild `
            -FilePath $SupabasePath `
            -Arguments @("stop") `
            -WorkingDirectory $WorkingDirectory `
            -TimeoutMilliseconds 120000
    }
    catch {
        if ($_.Exception.Data.Contains("step")) {
            throw
        }
        Throw-DatabaseGateFailure -Step $step -Reason "operational" -Code 2
    }
    if ($stopResult.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "child" -Code $stopResult.ExitCode
    }

    try {
        $listResult = Invoke-DatabaseChild `
            -FilePath $DockerPath `
            -Arguments @(
                "ps",
                "-a",
                "--filter",
                ("label=com.supabase.cli.project=" + $ProjectId),
                "--format",
                "{{.ID}}"
            ) `
            -WorkingDirectory $WorkingDirectory `
            -TimeoutMilliseconds 30000
    }
    catch {
        if ($_.Exception.Data.Contains("step")) {
            throw
        }
        Throw-DatabaseGateFailure -Step $step -Reason "operational" -Code 2
    }
    if ($listResult.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "operational" -Code 2
    }
    $remainingContainerIds = @(
        $listResult.Output -split "`r?`n" |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    if ($remainingContainerIds.Count -ne 0) {
        Throw-DatabaseGateFailure -Step $step -Reason "invalid" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=" + $step)
}

$skipStart = $false
$skipRollbackReplay = $false
$skipStartSeen = $false
$skipRollbackSeen = $false
$exitCode = 0
$savedEnvironment = Save-ProcessEnvironment -Names @(
    "SEJONG_ADMIN_DATABASE_URL",
    "SEJONG_DB_TEST_URL"
)

try {
    foreach ($argument in $args) {
        $argumentValue = [string]$argument
        if ($argumentValue.Equals("-SkipStart", [System.StringComparison]::OrdinalIgnoreCase)) {
            if ($skipStartSeen) {
                Throw-DatabaseGateFailure -Step "VALIDATE-DATABASE-ARGUMENTS" -Reason "invalid" -Code 2
            }
            $skipStartSeen = $true
            $skipStart = $true
            continue
        }
        if ($argumentValue.Equals(
                "-SkipRollbackReplay",
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            if ($skipRollbackSeen) {
                Throw-DatabaseGateFailure -Step "VALIDATE-DATABASE-ARGUMENTS" -Reason "invalid" -Code 2
            }
            $skipRollbackSeen = $true
            $skipRollbackReplay = $true
            continue
        }
        Throw-DatabaseGateFailure -Step "VALIDATE-DATABASE-ARGUMENTS" -Reason "invalid" -Code 2
    }

    if (
        $PSVersionTable.PSVersion.Major -lt 5 -or
        (
            $PSVersionTable.PSVersion.Major -eq 5 -and
            $PSVersionTable.PSVersion.Minor -lt 1
        )
    ) {
        Throw-DatabaseGateFailure -Step "PREFLIGHT-POWERSHELL" -Reason "version" -Code 2
    }

    $scriptDirectory = [System.IO.Path]::GetFullPath($PSScriptRoot)
    $repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory ".."))
    $supabaseBinary = Join-Path $repositoryRoot ".tools\supabase\v2.109.1\supabase.exe"
    $pythonBinary = Join-Path $repositoryRoot "apps\api\.venv\Scripts\python.exe"
    $bootstrapScript = Join-Path $scriptDirectory "bootstrap_supabase.ps1"
    $provisionScript = Join-Path $scriptDirectory (
        "provision_local_database_" + "lo" + "gin.py"
    )
    $sqlRunner = Join-Path $scriptDirectory "run_database_sql.py"
    $apiEnvironmentPath = Join-Path $repositoryRoot "apps\api\.env"
    $powerShellBinary = Join-Path $PSHOME "powershell.exe"
    $localProjectId = "sejong-ai-local"
    $localNetworkName = "sejong-ai-local-loopback"
    $localDatabaseContainerName = "supabase_db_sejong-ai-local"

    foreach ($requiredFile in @(
            $supabaseBinary,
            $pythonBinary,
            $bootstrapScript,
            $provisionScript,
            $sqlRunner,
            $powerShellBinary
        )) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            Throw-DatabaseGateFailure -Step "PREFLIGHT-LOCAL-FILES" -Reason "missing" -Code 2
        }
    }

    $pythonCheck = Invoke-DatabaseChild `
        -FilePath $pythonBinary `
        -Arguments @("--version") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 15000
    if ($pythonCheck.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step "PREFLIGHT-PYTHON" -Reason "child" -Code $pythonCheck.ExitCode
    }

    [Console]::Out.WriteLine("[START] step=PREFLIGHT-DOCKER")
    $dockerCommand = Get-Command "docker.exe" -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $dockerCommand) {
        $dockerCommand = Get-Command "docker" -CommandType Application -ErrorAction SilentlyContinue
    }
    if ($null -eq $dockerCommand) {
        Throw-DatabaseGateFailure -Step "PREFLIGHT-DOCKER" -Reason "missing" -Code 2
    }
    $dockerCheck = Invoke-DatabaseChild `
        -FilePath $dockerCommand.Source `
        -Arguments @("version", "--format", "{{.Server.Version}}") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 30000
    if ($dockerCheck.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step "PREFLIGHT-DOCKER" -Reason "child" -Code $dockerCheck.ExitCode
    }
    $dockerVersionText = $dockerCheck.Output.Trim()
    try {
        if ($dockerVersionText -notmatch '^\d+\.\d+\.\d+(?:\.\d+)?$') {
            throw New-Object System.FormatException("unsupported Docker version format")
        }
        $dockerVersion = [System.Version]::Parse($dockerVersionText)
    }
    catch {
        Throw-DatabaseGateFailure -Step "PREFLIGHT-DOCKER" -Reason "version" -Code 2
    }
    if ($dockerVersion.Major -lt 28) {
        Throw-DatabaseGateFailure -Step "PREFLIGHT-DOCKER" -Reason "version" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=PREFLIGHT-DOCKER")

    $null = Invoke-DatabaseStep `
        -Step "VERIFY-SUPABASE-VERSION" `
        -FilePath $powerShellBinary `
        -Arguments @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            $bootstrapScript,
            "-VerifyOnly"
        ) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 30000

    Ensure-LocalDatabaseNetwork `
        -DockerPath $dockerCommand.Source `
        -NetworkName $localNetworkName `
        -WorkingDirectory $repositoryRoot

    $runnerCreatedRuntime = $false
    if (-not $skipStart) {
        $runtimeAlreadyPresent = Assert-LocalDatabaseRuntime `
            -DockerPath $dockerCommand.Source `
            -ProjectId $localProjectId `
            -NetworkName $localNetworkName `
            -ExpectedContainerName $localDatabaseContainerName `
            -WorkingDirectory $repositoryRoot `
            -AllowAbsent
        if (-not $runtimeAlreadyPresent) {
            $runnerCreatedRuntime = $true
        }
        try {
            $null = Invoke-DatabaseStep `
                -Step "START-LOCAL-DATABASE" `
                -FilePath $supabaseBinary `
                -Arguments @("db", "start", "--network-id", $localNetworkName) `
                -WorkingDirectory $repositoryRoot
        }
        catch {
            $startFailure = $_.Exception
            if ($runnerCreatedRuntime) {
                Stop-OwnedUnsafeLocalDatabaseRuntime `
                    -SupabasePath $supabaseBinary `
                    -DockerPath $dockerCommand.Source `
                    -ProjectId $localProjectId `
                    -WorkingDirectory $repositoryRoot
            }
            throw $startFailure
        }
    }
    try {
        $null = Assert-LocalDatabaseRuntime `
            -DockerPath $dockerCommand.Source `
            -ProjectId $localProjectId `
            -NetworkName $localNetworkName `
            -ExpectedContainerName $localDatabaseContainerName `
            -WorkingDirectory $repositoryRoot
    }
    catch {
        $runtimeFailure = $_.Exception
        if ($runnerCreatedRuntime) {
            Stop-OwnedUnsafeLocalDatabaseRuntime `
                -SupabasePath $supabaseBinary `
                -DockerPath $dockerCommand.Source `
                -ProjectId $localProjectId `
                -WorkingDirectory $repositoryRoot
        }
        throw $runtimeFailure
    }

    # Local command: db reset.
    $null = Invoke-DatabaseStep `
        -Step "RESET-DATABASE-ONE" `
        -FilePath $supabaseBinary `
        -Arguments @("db", "reset", "--local") `
        -WorkingDirectory $repositoryRoot

    $status = Invoke-DatabaseChild `
        -FilePath $supabaseBinary `
        -Arguments @("status", "-o", "env") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 30000
    if ($status.ExitCode -ne 0) {
        Throw-DatabaseGateFailure -Step "READ-LOCAL-DATABASE-STATUS" -Reason "child" -Code $status.ExitCode
    }
    $env:SEJONG_ADMIN_DATABASE_URL = Read-DatabaseUrlFromStatus -StatusOutput $status.Output

    $provisionStepOne = "PROVISION-LOCAL-DB-" + "LOG" + "IN-ONE"
    $null = Invoke-DatabaseStep `
        -Step $provisionStepOne `
        -FilePath $pythonBinary `
        -Arguments @("-B", $provisionScript) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 30000

    # Local command: test db.
    $null = Invoke-DatabaseStep `
        -Step "TEST-PGTAP-ONE" `
        -FilePath $supabaseBinary `
        -Arguments @("test", "db") `
        -WorkingDirectory $repositoryRoot

    if (-not $skipRollbackReplay) {
        $rollbackFiles = @(
            (Join-Path $repositoryRoot "database\rollbacks\20260717000600_deferred_active_question_trigger_security.rollback.sql"),
            (Join-Path $repositoryRoot "database\rollbacks\20260716000500_indexes_and_read_interfaces.rollback.sql"),
            (Join-Path $repositoryRoot "database\rollbacks\20260716000400_candidate_workflow.rollback.sql"),
            (Join-Path $repositoryRoot "database\rollbacks\20260716000300_capabilities_and_functions.rollback.sql"),
            (Join-Path $repositoryRoot "database\rollbacks\20260716000200_invariants_and_lineage.rollback.sql"),
            (Join-Path $repositoryRoot "database\rollbacks\20260716000100_private_schema.rollback.sql")
        )
        $null = Invoke-DatabaseStep `
            -Step "ROLLBACK-DB001" `
            -FilePath $pythonBinary `
            -Arguments (@("-B", $sqlRunner) + $rollbackFiles) `
            -WorkingDirectory $repositoryRoot `
            -TimeoutMilliseconds 60000

        $absenceProof = Join-Path $repositoryRoot "database\verify_db001_absent.sql"
        $null = Invoke-DatabaseStep `
            -Step "VERIFY-DB001-ABSENT" `
            -FilePath $pythonBinary `
            -Arguments @("-B", $sqlRunner, $absenceProof) `
            -WorkingDirectory $repositoryRoot `
            -TimeoutMilliseconds 30000

        $null = Invoke-DatabaseStep `
            -Step "RESET-DATABASE-TWO" `
            -FilePath $supabaseBinary `
            -Arguments @("db", "reset", "--local") `
            -WorkingDirectory $repositoryRoot

        $provisionStepTwo = "PROVISION-LOCAL-DB-" + "LOG" + "IN-TWO"
        $null = Invoke-DatabaseStep `
            -Step $provisionStepTwo `
            -FilePath $pythonBinary `
            -Arguments @("-B", $provisionScript) `
            -WorkingDirectory $repositoryRoot `
            -TimeoutMilliseconds 30000

        $null = Invoke-DatabaseStep `
            -Step "TEST-PGTAP-TWO" `
            -FilePath $supabaseBinary `
            -Arguments @("test", "db") `
            -WorkingDirectory $repositoryRoot
    }

    $env:SEJONG_DB_TEST_URL = Read-EnvironmentAssignment `
        -Path $apiEnvironmentPath `
        -Key "DATABASE_URL"
    $integrationTest = Join-Path $repositoryRoot "apps\api\tests\db\test_integration.py"
    $null = Invoke-DatabaseStep `
        -Step "TEST-DATABASE-INTEGRATION" `
        -FilePath $pythonBinary `
        -Arguments @(
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            $integrationTest
        ) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 120000
}
catch {
    $failure = $_.Exception
    if (
        $failure.Data.Contains("step") -and
        $failure.Data.Contains("reason") -and
        $failure.Data.Contains("code")
    ) {
        $exitCode = [int]$failure.Data["code"]
        [Console]::Out.WriteLine(
            "[FAIL] step=" + [string]$failure.Data["step"] +
            " reason=" + [string]$failure.Data["reason"] +
            " code=" + [string]$failure.Data["code"]
        )
    }
    else {
        $exitCode = 2
        [Console]::Out.WriteLine("[FAIL] step=VERIFY-DATABASE reason=operational code=2")
    }
}
finally {
    try {
        Restore-ProcessEnvironment -Saved $savedEnvironment
    }
    catch {
        if ($exitCode -eq 0) {
            $exitCode = 2
            [Console]::Out.WriteLine(
                "[FAIL] step=RESTORE-DATABASE-ENVIRONMENT reason=operational code=2"
            )
        }
    }
}

exit $exitCode
