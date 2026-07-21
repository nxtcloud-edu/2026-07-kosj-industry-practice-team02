param(
    [string]$ReleaseVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Throw-DataSeedFailure {
    param(
        [string]$Step,
        [string]$Reason,
        [int]$Code
    )

    $failure = New-Object System.InvalidOperationException("controlled data seed gate failure")
    $failure.Data["step"] = $Step
    $failure.Data["reason"] = $Reason
    $failure.Data["code"] = $Code
    throw $failure
}

function ConvertTo-DataSeedArgument {
    param([string]$Value)

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }
    $builder = New-Object System.Text.StringBuilder
    $null = $builder.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq [char]92) {
            $backslashes += 1
            continue
        }
        if ($character -eq [char]34) {
            $null = $builder.Append(([string][char]92) * (($backslashes * 2) + 1))
            $null = $builder.Append([char]34)
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            $null = $builder.Append(([string][char]92) * $backslashes)
            $backslashes = 0
        }
        $null = $builder.Append($character)
    }
    if ($backslashes -gt 0) {
        $null = $builder.Append(([string][char]92) * ($backslashes * 2))
    }
    $null = $builder.Append('"')
    return $builder.ToString()
}

function Stop-DataSeedProcessTree {
    param([System.Diagnostics.Process]$Process)

    if ($null -eq $Process -or $Process.HasExited) {
        return
    }
    $taskkill = Join-Path $env:SystemRoot "System32\taskkill.exe"
    if (Test-Path -LiteralPath $taskkill -PathType Leaf) {
        try {
            $killerInfo = New-Object System.Diagnostics.ProcessStartInfo
            $killerInfo.FileName = $taskkill
            $killerInfo.Arguments = "/PID " + $Process.Id + " /T /F"
            $killerInfo.UseShellExecute = $false
            $killerInfo.CreateNoWindow = $true
            $killerInfo.RedirectStandardOutput = $true
            $killerInfo.RedirectStandardError = $true
            $killer = New-Object System.Diagnostics.Process
            $killer.StartInfo = $killerInfo
            $null = $killer.Start()
            $null = $killer.StandardOutput.ReadToEndAsync()
            $null = $killer.StandardError.ReadToEndAsync()
            $null = $killer.WaitForExit(5000)
            $killer.Dispose()
        }
        catch {
            # The fallback below still terminates the direct child.
        }
    }
    if (-not $Process.HasExited) {
        try {
            $Process.Kill()
            $null = $Process.WaitForExit(5000)
        }
        catch {
            # The caller reports timeout without relaying OS or child detail.
        }
    }
}

function Invoke-DataSeedChild {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [int]$TimeoutMilliseconds = 900000
    )

    if (
        $TimeoutMilliseconds -le 0 -or
        -not [System.IO.Path]::IsPathRooted($FilePath) -or
        -not (Test-Path -LiteralPath $FilePath -PathType Leaf) -or
        -not [System.IO.Path]::IsPathRooted($WorkingDirectory) -or
        -not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)
    ) {
        Throw-DataSeedFailure -Step "DATA-SEED-CHILD" -Reason "invalid" -Code 2
    }

    $argumentValues = New-Object System.Collections.Generic.List[string]
    foreach ($argument in @($Arguments)) {
        $argumentValues.Add((ConvertTo-DataSeedArgument -Value ([string]$argument)))
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.Arguments = $argumentValues -join " "
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false, $false)
    $startInfo.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false, $false)

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            Throw-DataSeedFailure -Step "DATA-SEED-CHILD" -Reason "operational" -Code 2
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            Stop-DataSeedProcessTree -Process $process
            Throw-DataSeedFailure -Step "DATA-SEED-CHILD" -Reason "timeout" -Code 2
        }
        $tasks = [System.Threading.Tasks.Task[]]@($stdoutTask, $stderrTask)
        if (-not [System.Threading.Tasks.Task]::WaitAll($tasks, 5000)) {
            Stop-DataSeedProcessTree -Process $process
            Throw-DataSeedFailure -Step "DATA-SEED-CHILD" -Reason "timeout" -Code 2
        }
        return [pscustomobject]@{
            ExitCode = [int]$process.ExitCode
            Output = [string]$stdoutTask.Result
        }
    }
    catch {
        if ($_.Exception.Data.Contains("step")) {
            throw
        }
        Stop-DataSeedProcessTree -Process $process
        Throw-DataSeedFailure -Step "DATA-SEED-CHILD" -Reason "operational" -Code 2
    }
    finally {
        $process.Dispose()
    }
}

function Invoke-DataSeedStep {
    param(
        [string]$Step,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [int]$TimeoutMilliseconds = 900000,
        [switch]$SuppressPass
    )

    [Console]::Out.WriteLine("[START] step=" + $Step)
    try {
        $result = Invoke-DataSeedChild `
            -FilePath $FilePath `
            -Arguments $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -TimeoutMilliseconds $TimeoutMilliseconds
    }
    catch {
        if ($_.Exception.Data.Contains("step") -and $_.Exception.Data["reason"] -eq "timeout") {
            Throw-DataSeedFailure -Step $Step -Reason "timeout" -Code 2
        }
        if ($_.Exception.Data.Contains("step")) {
            Throw-DataSeedFailure -Step $Step -Reason "operational" -Code 2
        }
        throw
    }
    if ($result.ExitCode -ne 0) {
        $childCode = [int]$result.ExitCode
        if ($childCode -le 0) {
            $childCode = 2
        }
        Throw-DataSeedFailure -Step $Step -Reason "child" -Code $childCode
    }
    if (-not $SuppressPass) {
        [Console]::Out.WriteLine("[PASS] step=" + $Step)
    }
    return $result
}

function Save-DataSeedEnvironment {
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

function Get-DataSeedLibpqEnvironmentNames {
    $names = New-Object System.Collections.Generic.List[string]
    foreach ($key in [Environment]::GetEnvironmentVariables("Process").Keys) {
        $name = [string]$key
        if ($name.StartsWith("PG", [System.StringComparison]::OrdinalIgnoreCase)) {
            $names.Add($name)
        }
    }
    return @($names | Sort-Object -Unique)
}

function Clear-DataSeedEnvironment {
    param([string[]]$Names)

    foreach ($name in $Names) {
        [Environment]::SetEnvironmentVariable($name, $null, "Process")
    }
}

function Restore-DataSeedEnvironment {
    param([hashtable]$Saved)

    foreach ($name in $Saved.Keys) {
        if ($Saved[$name].Existed) {
            [Environment]::SetEnvironmentVariable(
                $name,
                $Saved[$name].Value,
                "Process"
            )
        }
        else {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
    }
}

function Read-DataSeedDatabaseUrl {
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
    Throw-DataSeedFailure -Step "READ-LOCAL-DATABASE-STATUS" -Reason "invalid" -Code 2
}

function Write-DataSeedEvidence {
    param(
        [string]$Step,
        [string]$Output
    )

    $patterns = @{
        "VERIFY-DATA-SEED-IDENTITY" = '^\[PASS\] step=VERIFY-DATA-SEED-IDENTITY release=0\.1\.0-initial\.2 identity=exact$'
        "VERIFY-DATA-SEED-FAILURE-ROLLBACK" = '^\[PASS\] step=VERIFY-DATA-SEED-FAILURE-ROLLBACK release=0\.1\.0-initial\.2 tables=8 partial=0$'
        "VERIFY-DATA-SEED-CONCURRENCY-A" = '^\[PASS\] step=VERIFY-DATA-SEED-CONCURRENCY-A release=0\.1\.0-initial\.2 ordering=capability-before-lock seed_rows=0 capability_rows=1$'
        "VERIFY-DATA-SEED-CONCURRENCY-B" = '^\[PASS\] step=VERIFY-DATA-SEED-CONCURRENCY-B release=0\.1\.0-initial\.2 ordering=lock-before-capability seed_complete=1 capability_rows=1$'
        "VERIFY-DATA-SEED-SEED-CYCLE" = '^\[PASS\] step=VERIFY-DATA-SEED-SEED-CYCLE release=0\.1\.0-initial\.2 kb=19 office=3 mapping=10 replay=1 second_seed=blocked compensation_guard=blocked semantic_sha256=[0-9a-f]{64}$'
        "VERIFY-DATA-SEED-FINAL" = '^\[PASS\] step=VERIFY-DATA-SEED-FINAL release=0\.1\.0-initial\.2 kb=19 office=3 mapping=10 citizen=19 exclusions=0 operational=0 semantic_sha256=[0-9a-f]{64}$'
    }
    if (-not $patterns.ContainsKey($Step)) {
        Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
    }
    $lines = @(
        $Output -split "`r?`n" |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    if ($lines.Count -ne 1 -or $lines[0] -cnotmatch $patterns[$Step]) {
        Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
    }
    [Console]::Out.WriteLine($lines[0])
}

function Invoke-DataSeedEvidenceStep {
    param(
        [string]$Step,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [int]$TimeoutMilliseconds
    )

    $result = Invoke-DataSeedStep `
        -Step $Step `
        -FilePath $FilePath `
        -Arguments $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds $TimeoutMilliseconds `
        -SuppressPass
    Write-DataSeedEvidence -Step $Step -Output $result.Output
}

function Invoke-DataSeedRuntimeChild {
    param(
        [string]$Step,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [int]$TimeoutMilliseconds
    )

    try {
        $result = Invoke-DataSeedChild `
            -FilePath $FilePath `
            -Arguments $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -TimeoutMilliseconds $TimeoutMilliseconds
    }
    catch {
        if (
            $_.Exception.Data.Contains("reason") -and
            $_.Exception.Data["reason"] -ceq "timeout"
        ) {
            Throw-DataSeedFailure -Step $Step -Reason "timeout" -Code 2
        }
        Throw-DataSeedFailure -Step $Step -Reason "operational" -Code 2
    }
    if ($result.ExitCode -ne 0) {
        $childCode = [int]$result.ExitCode
        if ($childCode -le 0) {
            $childCode = 2
        }
        Throw-DataSeedFailure -Step $Step -Reason "child" -Code $childCode
    }
    return $result
}

function Get-DataSeedOwnedContainerIds {
    param(
        [string]$Step,
        [string]$DockerPath,
        [string]$ProjectId,
        [string]$WorkingDirectory
    )

    $listResult = Invoke-DataSeedRuntimeChild `
        -Step $Step `
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
    $containerIds = @(
        $listResult.Output -split "`r?`n" |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    foreach ($containerId in $containerIds) {
        if ($containerId -cnotmatch '^[0-9a-f]{12,64}$') {
            Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
        }
    }
    return @($containerIds)
}

function Get-DataSeedListenerCount {
    param(
        [int]$Port,
        [string]$Step
    )

    try {
        $listeners = @(
            [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() |
                Where-Object { $_.Port -eq $Port }
        )
        return [int]$listeners.Count
    }
    catch {
        Throw-DataSeedFailure `
            -Step $Step `
            -Reason "operational" `
            -Code 2
    }
}

function Assert-DataSeedRuntimeAbsent {
    param(
        [string]$DockerPath,
        [string]$ProjectId,
        [string]$WorkingDirectory
    )

    $step = "VERIFY-DATA-SEED-RUNTIME-ABSENT"
    [Console]::Out.WriteLine("[START] step=" + $step)
    $containerIds = @(
        Get-DataSeedOwnedContainerIds `
            -Step $step `
            -DockerPath $DockerPath `
            -ProjectId $ProjectId `
            -WorkingDirectory $WorkingDirectory
    )
    $listenerCount = Get-DataSeedListenerCount -Port 54322 -Step $step
    if ($containerIds.Count -ne 0 -or $listenerCount -ne 0) {
        Throw-DataSeedFailure -Step $step -Reason "invalid" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=" + $step)
}

function Test-DataSeedLoopbackPortBinding {
    param([object]$Ports)

    if ($null -eq $Ports) {
        return $false
    }
    $publishedPorts = @($Ports.PSObject.Properties)
    if ($publishedPorts.Count -ne 1 -or $publishedPorts[0].Name -cne "5432/tcp") {
        return $false
    }
    $bindings = @($publishedPorts[0].Value)
    return (
        $bindings.Count -eq 1 -and
        $null -ne $bindings[0] -and
        [string]$bindings[0].HostIp -ceq "127.0.0.1" -and
        [string]$bindings[0].HostPort -ceq "54322"
    )
}

function Assert-DataSeedOwnedRuntime {
    param(
        [string]$Step,
        [string]$DockerPath,
        [string]$ContainerId,
        [string]$ProjectId,
        [string]$NetworkName,
        [string]$ExpectedContainerName,
        [string]$WorkingDirectory
    )

    $inspectResult = Invoke-DataSeedRuntimeChild `
        -Step $Step `
        -FilePath $DockerPath `
        -Arguments @("inspect", $ContainerId, "--format", "{{json .}}") `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds 30000
    try {
        $container = $inspectResult.Output | ConvertFrom-Json -ErrorAction Stop
        if ($container -is [System.Array]) {
            Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
        }
        $actualName = [string]$container.Name
        if ($actualName.StartsWith("/", [System.StringComparison]::Ordinal)) {
            $actualName = $actualName.Substring(1)
        }
        if (
            $actualName -cne $ExpectedContainerName -or
            $null -eq $container.State -or
            $null -eq $container.Config -or
            $null -eq $container.Config.Labels -or
            $null -eq $container.HostConfig -or
            $container.HostConfig.NetworkMode -cne $NetworkName -or
            -not (Test-DataSeedLoopbackPortBinding -Ports $container.HostConfig.PortBindings)
        ) {
            Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
        }
        $runningProperty = $container.State.PSObject.Properties["Running"]
        $statusProperty = $container.State.PSObject.Properties["Status"]
        if (
            $null -eq $runningProperty -or
            $runningProperty.Value -isnot [bool] -or
            $null -eq $statusProperty
        ) {
            Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
        }
        $running = [bool]$runningProperty.Value
        $status = [string]$statusProperty.Value
        if (
            ($running -and $status -cne "running") -or
            (
                -not $running -and
                $status -cnotin @("created", "exited", "dead")
            )
        ) {
            Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
        }
        $projectLabel = $container.Config.Labels.PSObject.Properties[
            "com.supabase.cli.project"
        ]
        if ($null -eq $projectLabel -or $projectLabel.Value -cne $ProjectId) {
            Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
        }
        if ($running) {
            if (
                $null -eq $container.NetworkSettings -or
                $null -eq $container.NetworkSettings.Networks -or
                -not (Test-DataSeedLoopbackPortBinding -Ports $container.NetworkSettings.Ports)
            ) {
                Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
            }
            $networks = @($container.NetworkSettings.Networks.PSObject.Properties)
            if ($networks.Count -ne 1 -or $networks[0].Name -cne $NetworkName) {
                Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
            }
        }
    }
    catch {
        if ($_.Exception.Data.Contains("step")) {
            throw
        }
        Throw-DataSeedFailure -Step $Step -Reason "invalid" -Code 2
    }
}

function Remove-DataSeedOwnedRuntime {
    param(
        [string]$SupabasePath,
        [string]$DockerPath,
        [string]$ProjectId,
        [string]$NetworkName,
        [string]$ExpectedContainerName,
        [string]$WorkingDirectory
    )

    $step = "CLEANUP-DATA-SEED-RUNTIME"
    [Console]::Out.WriteLine("[START] step=" + $step)
    $containerIds = @(
        Get-DataSeedOwnedContainerIds `
            -Step $step `
            -DockerPath $DockerPath `
            -ProjectId $ProjectId `
            -WorkingDirectory $WorkingDirectory
    )
    if ($containerIds.Count -eq 0) {
        if ((Get-DataSeedListenerCount -Port 54322 -Step $step) -ne 0) {
            Throw-DataSeedFailure -Step $step -Reason "invalid" -Code 2
        }
        [Console]::Out.WriteLine("[PASS] step=" + $step)
        return
    }
    if ($containerIds.Count -ne 1) {
        Throw-DataSeedFailure -Step $step -Reason "invalid" -Code 2
    }
    Assert-DataSeedOwnedRuntime `
        -Step $step `
        -DockerPath $DockerPath `
        -ContainerId $containerIds[0] `
        -ProjectId $ProjectId `
        -NetworkName $NetworkName `
        -ExpectedContainerName $ExpectedContainerName `
        -WorkingDirectory $WorkingDirectory
    $null = Invoke-DataSeedRuntimeChild `
        -Step $step `
        -FilePath $SupabasePath `
        -Arguments @("stop", "--project-id", $ProjectId) `
        -WorkingDirectory $WorkingDirectory `
        -TimeoutMilliseconds 120000
    $remainingContainerIds = @(
        Get-DataSeedOwnedContainerIds `
            -Step $step `
            -DockerPath $DockerPath `
            -ProjectId $ProjectId `
            -WorkingDirectory $WorkingDirectory
    )
    if (
        $remainingContainerIds.Count -ne 0 -or
        (Get-DataSeedListenerCount -Port 54322 -Step $step) -ne 0
    ) {
        Throw-DataSeedFailure -Step $step -Reason "invalid" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=" + $step)
}

function Complete-DataSeedRuntimeAttempt {
    param(
        [string]$SupabasePath,
        [string]$DockerPath,
        [string]$ProjectId,
        [string]$NetworkName,
        [string]$ExpectedContainerName,
        [string]$WorkingDirectory,
        [System.Exception]$PrimaryFailure
    )

    try {
        Remove-DataSeedOwnedRuntime `
            -SupabasePath $SupabasePath `
            -DockerPath $DockerPath `
            -ProjectId $ProjectId `
            -NetworkName $NetworkName `
            -ExpectedContainerName $ExpectedContainerName `
            -WorkingDirectory $WorkingDirectory
    }
    catch {
        $cleanupFailure = $_.Exception
        if ($null -eq $PrimaryFailure) {
            return $cleanupFailure
        }
        if (
            $cleanupFailure.Data.Contains("step") -and
            $cleanupFailure.Data.Contains("reason") -and
            $cleanupFailure.Data.Contains("code")
        ) {
            $PrimaryFailure.Data["cleanup_step"] = [string]$cleanupFailure.Data["step"]
            $PrimaryFailure.Data["cleanup_reason"] = [string]$cleanupFailure.Data["reason"]
            $PrimaryFailure.Data["cleanup_code"] = [int]$cleanupFailure.Data["code"]
        }
        else {
            $PrimaryFailure.Data["cleanup_step"] = "CLEANUP-DATA-SEED-RUNTIME"
            $PrimaryFailure.Data["cleanup_reason"] = "operational"
            $PrimaryFailure.Data["cleanup_code"] = 2
        }
    }
    return $PrimaryFailure
}

function Write-DataSeedFailureEvidence {
    param([System.Exception]$Failure)

    if (
        $Failure.Data.Contains("step") -and
        $Failure.Data.Contains("reason") -and
        $Failure.Data.Contains("code")
    ) {
        [Console]::Out.WriteLine(
            "[FAIL] step=" + [string]$Failure.Data["step"] +
            " reason=" + [string]$Failure.Data["reason"] +
            " code=" + [string]$Failure.Data["code"]
        )
    }
    else {
        [Console]::Out.WriteLine(
            "[FAIL] step=VERIFY-DATA-SEED reason=operational code=2"
        )
    }
    foreach ($secondary in @(
            @("cleanup", "CLEANUP-DATA-SEED-RUNTIME"),
            @("restore", "RESTORE-DATA-SEED-ENVIRONMENT")
        )) {
        $prefix = $secondary[0]
        $stepKey = $prefix + "_step"
        if (-not $Failure.Data.Contains($stepKey)) {
            continue
        }
        $reasonKey = $prefix + "_reason"
        $codeKey = $prefix + "_code"
        $step = [string]$Failure.Data[$stepKey]
        $reason = "operational"
        $code = 2
        if ($Failure.Data.Contains($reasonKey)) {
            $reason = [string]$Failure.Data[$reasonKey]
        }
        if ($Failure.Data.Contains($codeKey)) {
            $code = [int]$Failure.Data[$codeKey]
        }
        if ([string]::IsNullOrWhiteSpace($step)) {
            $step = $secondary[1]
        }
        [Console]::Out.WriteLine(
            "[FAIL] step=" + $step +
            " reason=" + $reason +
            " code=" + [string]$code
        )
    }
}

function Assert-DataSeedPatchedRuntime {
    param(
        [string]$RepositoryRoot,
        [string]$RuntimeManifestPath,
        [string]$SupabaseBinary
    )

    $step = "VERIFY-DATA-SEED-PATCHED-RUNTIME"
    [Console]::Out.WriteLine("[START] step=" + $step)
    try {
        $raw = [System.IO.File]::ReadAllText(
            $RuntimeManifestPath,
            [System.Text.Encoding]::UTF8
        )
        $manifest = $raw | ConvertFrom-Json -ErrorAction Stop
        $properties = @($manifest.PSObject.Properties.Name)
        $expectedProperties = @(
            "schema_version",
            "source_manifest_sha256",
            "version",
            "platform",
            "relative_path",
            "sha256"
        )
        $propertyDiff = @(
            Compare-Object `
                -ReferenceObject $expectedProperties `
                -DifferenceObject $properties `
                -CaseSensitive
        )
        if (
            $properties.Count -ne $expectedProperties.Count -or
            $propertyDiff.Count -ne 0 -or
            $manifest.schema_version -ne 1 -or
            $manifest.source_manifest_sha256 -cne "c293e5ac32bae030eadf383d8d9511dc16eac834e51e996273ae8b7e39616657" -or
            $manifest.version -cne "2.109.1" -or
            $manifest.platform -cne "windows-amd64" -or
            $manifest.relative_path -cne ".tools/supabase/v2.109.1-sejong-loopback/supabase.exe" -or
            $manifest.sha256 -cne "751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c"
        ) {
            Throw-DataSeedFailure -Step $step -Reason "invalid" -Code 2
        }
        $expectedBinary = [System.IO.Path]::GetFullPath(
            (Join-Path $RepositoryRoot ".tools\supabase\v2.109.1-sejong-loopback\supabase.exe")
        )
        if (
            $SupabaseBinary -cne $expectedBinary -or
            -not (Test-Path -LiteralPath $SupabaseBinary -PathType Leaf) -or
            (Get-FileHash -LiteralPath $SupabaseBinary -Algorithm SHA256).Hash.ToLowerInvariant() -cne
                "751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c"
        ) {
            Throw-DataSeedFailure -Step $step -Reason "integrity" -Code 2
        }
    }
    catch {
        if ($_.Exception.Data.Contains("step")) {
            throw
        }
        Throw-DataSeedFailure -Step $step -Reason "operational" -Code 2
    }
    $versionResult = Invoke-DataSeedChild `
        -FilePath $SupabaseBinary `
        -Arguments @("--version") `
        -WorkingDirectory $RepositoryRoot `
        -TimeoutMilliseconds 15000
    if ($versionResult.ExitCode -ne 0 -or $versionResult.Output.Trim() -cne "2.109.1") {
        Throw-DataSeedFailure -Step $step -Reason "version" -Code 2
    }
    [Console]::Out.WriteLine("[PASS] step=" + $step)
}

# DATA-SEED-RUNNER-MAIN

$exitCode = 0
$savedEnvironment = $null
$failure = $null
$baselineAttempted = $false
$repositoryRoot = $null
$supabaseBinary = $null
$dockerPath = $null
$localProjectId = "sejong-ai-local"
$localNetworkName = "sejong-ai-local-loopback"
$localDatabaseContainerName = "supabase_db_sejong-ai-local"

try {
    $libpqEnvironmentNames = @(Get-DataSeedLibpqEnvironmentNames)
    $savedEnvironment = Save-DataSeedEnvironment `
        -Names (@("SEJONG_ADMIN_DATABASE_URL") + $libpqEnvironmentNames)
    Clear-DataSeedEnvironment -Names $libpqEnvironmentNames

    if ($ReleaseVersion -cne "0.1.0-initial.2") {
        Throw-DataSeedFailure -Step "VALIDATE-DATA-SEED-ARGUMENTS" -Reason "RELEASE-VERSION-INVALID" -Code 2
    }
    if ($args.Count -ne 0) {
        Throw-DataSeedFailure -Step "VALIDATE-DATA-SEED-ARGUMENTS" -Reason "invalid" -Code 2
    }
    if (
        $PSVersionTable.PSVersion.Major -lt 5 -or
        (
            $PSVersionTable.PSVersion.Major -eq 5 -and
            $PSVersionTable.PSVersion.Minor -lt 1
        )
    ) {
        Throw-DataSeedFailure -Step "PREFLIGHT-POWERSHELL" -Reason "version" -Code 2
    }

    $scriptDirectory = [System.IO.Path]::GetFullPath($PSScriptRoot)
    $repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory ".."))
    $powerShellBinary = Join-Path $PSHOME "powershell.exe"
    $pythonBinary = Join-Path $repositoryRoot "apps\api\.venv\Scripts\python.exe"
    $databaseRunner = Join-Path $repositoryRoot "scripts\verify_database.ps1"
    $databaseVerifier = Join-Path $repositoryRoot "scripts\verify_data_seed_db.py"
    $concurrencyProbe = Join-Path $repositoryRoot "scripts\test_data_seed_concurrency.py"
    $supabaseBinary = Join-Path $repositoryRoot ".tools\supabase\v2.109.1-sejong-loopback\supabase.exe"
    $runtimeManifest = Join-Path $repositoryRoot "scripts\supabase-cli.local-patch.runtime.json"
    foreach ($requiredFile in @(
            $powerShellBinary,
            $pythonBinary,
            $databaseRunner,
            $databaseVerifier,
            $concurrencyProbe,
            $supabaseBinary,
            $runtimeManifest
        )) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            Throw-DataSeedFailure -Step "PREFLIGHT-DATA-SEED-FILES" -Reason "missing" -Code 2
        }
    }

    [Console]::Out.WriteLine("[START] step=PREFLIGHT-DATA-SEED-DOCKER")
    $dockerCommand = Get-Command "docker.exe" -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $dockerCommand) {
        $dockerCommand = Get-Command "docker" -CommandType Application -ErrorAction SilentlyContinue
    }
    if ($null -eq $dockerCommand) {
        Throw-DataSeedFailure -Step "PREFLIGHT-DATA-SEED-DOCKER" -Reason "missing" -Code 2
    }
    $dockerPath = [System.IO.Path]::GetFullPath($dockerCommand.Source)
    [Console]::Out.WriteLine("[PASS] step=PREFLIGHT-DATA-SEED-DOCKER")

    Assert-DataSeedRuntimeAbsent `
        -DockerPath $dockerPath `
        -ProjectId $localProjectId `
        -WorkingDirectory $repositoryRoot

    $baselineAttempted = $true
    $null = Invoke-DataSeedStep `
        -Step "VERIFY-DATABASE-BASELINE" `
        -FilePath $powerShellBinary `
        -Arguments @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            $databaseRunner
        ) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 1800000

    Assert-DataSeedPatchedRuntime `
        -RepositoryRoot $repositoryRoot `
        -RuntimeManifestPath $runtimeManifest `
        -SupabaseBinary $supabaseBinary

    [Console]::Out.WriteLine("[START] step=READ-LOCAL-DATABASE-STATUS")
    $statusResult = Invoke-DataSeedChild `
        -FilePath $supabaseBinary `
        -Arguments @("status", "-o", "env") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 30000
    if ($statusResult.ExitCode -ne 0) {
        Throw-DataSeedFailure -Step "READ-LOCAL-DATABASE-STATUS" -Reason "child" -Code $statusResult.ExitCode
    }
    $adminDsn = Read-DataSeedDatabaseUrl -StatusOutput $statusResult.Output
    [Environment]::SetEnvironmentVariable(
        "SEJONG_ADMIN_DATABASE_URL",
        $adminDsn,
        "Process"
    )
    [Console]::Out.WriteLine("[PASS] step=READ-LOCAL-DATABASE-STATUS")

    Invoke-DataSeedEvidenceStep `
        -Step "VERIFY-DATA-SEED-IDENTITY" `
        -FilePath $pythonBinary `
        -Arguments @("-B", $databaseVerifier, "identity", "--release-version", $ReleaseVersion) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 30000

    $null = Invoke-DataSeedStep `
        -Step "RESET-BEFORE-FAILURE-ROLLBACK" `
        -FilePath $supabaseBinary `
        -Arguments @("db", "reset", "--local") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 300000
    Invoke-DataSeedEvidenceStep `
        -Step "VERIFY-DATA-SEED-FAILURE-ROLLBACK" `
        -FilePath $pythonBinary `
        -Arguments @("-B", $databaseVerifier, "failure-rollback", "--release-version", $ReleaseVersion) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 60000

    $null = Invoke-DataSeedStep `
        -Step "RESET-BEFORE-CONCURRENCY-A" `
        -FilePath $supabaseBinary `
        -Arguments @("db", "reset", "--local") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 300000
    Invoke-DataSeedEvidenceStep `
        -Step "VERIFY-DATA-SEED-CONCURRENCY-A" `
        -FilePath $pythonBinary `
        -Arguments @(
            "-B",
            $concurrencyProbe,
            "--scenario",
            "capability-before-seed",
            "--release-version",
            $ReleaseVersion
        ) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 60000

    $null = Invoke-DataSeedStep `
        -Step "RESET-BEFORE-CONCURRENCY-B" `
        -FilePath $supabaseBinary `
        -Arguments @("db", "reset", "--local") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 300000
    Invoke-DataSeedEvidenceStep `
        -Step "VERIFY-DATA-SEED-CONCURRENCY-B" `
        -FilePath $pythonBinary `
        -Arguments @(
            "-B",
            $concurrencyProbe,
            "--scenario",
            "seed-before-capability",
            "--release-version",
            $ReleaseVersion
        ) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 60000

    $null = Invoke-DataSeedStep `
        -Step "RESET-BEFORE-SEED-CYCLE" `
        -FilePath $supabaseBinary `
        -Arguments @("db", "reset", "--local") `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 300000
    Invoke-DataSeedEvidenceStep `
        -Step "VERIFY-DATA-SEED-SEED-CYCLE" `
        -FilePath $pythonBinary `
        -Arguments @("-B", $databaseVerifier, "seed-cycle", "--release-version", $ReleaseVersion) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 120000
    Invoke-DataSeedEvidenceStep `
        -Step "VERIFY-DATA-SEED-FINAL" `
        -FilePath $pythonBinary `
        -Arguments @("-B", $databaseVerifier, "verify-final", "--release-version", $ReleaseVersion) `
        -WorkingDirectory $repositoryRoot `
        -TimeoutMilliseconds 60000
}
catch {
    $failure = $_.Exception
    if (
        $failure.Data.Contains("step") -and
        $failure.Data.Contains("reason") -and
        $failure.Data.Contains("code")
    ) {
        $exitCode = [int]$failure.Data["code"]
    }
    else {
        $exitCode = 2
    }
}
finally {
    if ($baselineAttempted) {
        $failureBeforeCleanup = $failure
        $failure = Complete-DataSeedRuntimeAttempt `
            -SupabasePath $supabaseBinary `
            -DockerPath $dockerPath `
            -ProjectId $localProjectId `
            -NetworkName $localNetworkName `
            -ExpectedContainerName $localDatabaseContainerName `
            -WorkingDirectory $repositoryRoot `
            -PrimaryFailure $failure
        if ($null -eq $failureBeforeCleanup -and $null -ne $failure) {
            if ($failure.Data.Contains("code")) {
                $exitCode = [int]$failure.Data["code"]
            }
            else {
                $exitCode = 2
            }
        }
    }
    try {
        if ($null -ne $savedEnvironment) {
            Restore-DataSeedEnvironment -Saved $savedEnvironment
        }
    }
    catch {
        if ($null -eq $failure) {
            try {
                Throw-DataSeedFailure `
                    -Step "RESTORE-DATA-SEED-ENVIRONMENT" `
                    -Reason "operational" `
                    -Code 2
            }
            catch {
                $failure = $_.Exception
            }
            $exitCode = 2
        }
        else {
            $failure.Data["restore_step"] = "RESTORE-DATA-SEED-ENVIRONMENT"
            $failure.Data["restore_reason"] = "operational"
            $failure.Data["restore_code"] = 2
        }
    }
}

if ($null -ne $failure) {
    Write-DataSeedFailureEvidence -Failure $failure
}
else {
    [Console]::Out.WriteLine(
        "[PASS] step=VERIFY-DATA-SEED release=0.1.0-initial.2"
    )
}
exit $exitCode
