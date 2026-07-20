[CmdletBinding(DefaultParameterSetName = 'Explicit')]
param(
    [Parameter(ParameterSetName = 'Explicit', Position = 0)]
    [string[]]$Path,
    [Parameter(ParameterSetName = 'Explicit', ValueFromRemainingArguments = $true)]
    [string[]]$AdditionalPath,
    [Parameter(ParameterSetName = 'Repository', Mandatory = $true)]
    [string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $script:Utf8NoBom
$OutputEncoding = $script:Utf8NoBom
$script:InputPaths = @()
foreach ($inputPath in $Path) {
    $script:InputPaths += $inputPath
}
foreach ($inputPath in $AdditionalPath) {
    $script:InputPaths += $inputPath
}

$requestedRepositoryRoot = $RepositoryRoot
$script:DefaultRepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$script:RepositoryRoot = $script:DefaultRepositoryRoot
$script:RepositoryRootInvalid = $false
if ($PSCmdlet.ParameterSetName -eq 'Repository') {
    try {
        if ([string]::IsNullOrWhiteSpace($requestedRepositoryRoot)) {
            throw 'repository root is empty'
        }
        $repositoryItem = Get-Item -LiteralPath $requestedRepositoryRoot -Force
        if (-not $repositoryItem.PSIsContainer) {
            throw 'repository root is not a directory'
        }
        $script:RepositoryRoot = [System.IO.Path]::GetFullPath($repositoryItem.FullName)
    }
    catch {
        $script:RepositoryRootInvalid = $true
    }
}
$script:MaxGitOutputBytes = 32MB
$script:MaxGitErrorBytes = 1MB
$script:GitDeadlineMilliseconds = 60000
$script:MaxRepositoryFileBytes = 4MB
$script:MaxRepositoryScanBytes = 16MB
$script:RepositoryBytesScanned = [int64]0
$script:AggregateLimitExceeded = $false
$script:ExcludedSegments = @(
    '.git', '.mypy_cache', '.next', '.pytest_cache', '.ruff_cache', '.superpowers',
    '.tools', '.turbo', '.venv', '.worktrees', '__pycache__', 'artifacts', 'backups',
    'build', 'cache', 'coverage', 'dist', 'htmlcov', 'legacy', 'logs', 'node_modules',
    'out', 'playwright-report', 'quarantine', 'test-results', 'tmp', 'venv'
)
$script:PatternRules = @(
    @{ Id = 'AWS_ACCESS_KEY'; Pattern = '(?:AKIA|ASIA)[0-9A-Z]{16}' },
    @{
        Id = 'CREDENTIAL_URL'
        Pattern = '(?i)\b(?:https?|postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?)://[^/\s:@]+:[^/\s@]+@'
    },
    @{ Id = 'GITHUB_TOKEN'; Pattern = '(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})' },
    @{
        Id = 'PRIVATE_KEY_HEADER'
        Pattern = '-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'
    },
    @{ Id = 'PROVIDER_KEY'; Pattern = '\bsk-[A-Za-z0-9_-]{20,}\b' }
)
$script:SecretAssignmentNames = @(
    ('DATABASE_' + 'URL'),
    ('SUPABASE_' + 'SERVICE_ROLE_KEY'),
    ('LLM_' + 'API_KEY'),
    ('CONTEXT_TOKEN_' + 'SECRET'),
    ('DEEPSEEK_' + 'API_KEY')
)


function ConvertTo-SafeDisplayText {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value)

    $builder = New-Object System.Text.StringBuilder
    foreach ($character in $Value.ToCharArray()) {
        $code = [int][char]$character
        if ($code -lt 32 -or $code -eq 127 -or $code -eq 0x2028 -or $code -eq 0x2029) {
            [void]$builder.Append(('\u{0:X4}' -f $code))
        }
        else {
            [void]$builder.Append($character)
        }
    }
    $safe = $builder.ToString()
    if ($safe.StartsWith('::', [System.StringComparison]::Ordinal)) {
        return '\u003A\u003A' + $safe.Substring(2)
    }
    return $safe
}


function Get-DisplayPath {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)

    $fullPath = [System.IO.Path]::GetFullPath($LiteralPath)
    $rootPrefix = $script:RepositoryRoot.TrimEnd([char[]]@('\', '/')) + [System.IO.Path]::DirectorySeparatorChar
    if ($fullPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath.Substring($rootPrefix.Length).Replace('\', '/')
    }
    return $fullPath.Replace('\', '/')
}


function Test-IsExcludedRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $segments = $RelativePath.Replace('\', '/').Split('/')
    foreach ($segment in $segments) {
        foreach ($excluded in $script:ExcludedSegments) {
            if ($segment.Equals($excluded, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
    }
    return $false
}


function Add-Result {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$Results,
        [Parameter(Mandatory = $true)][string]$DisplayPath,
        [Parameter(Mandatory = $true)][string]$Rule,
        [Parameter(Mandatory = $true)][int]$Count
    )

    $safePath = ConvertTo-SafeDisplayText -Value $DisplayPath
    [void]$Results.Add([pscustomobject]@{
        Path = $safePath
        Rule = $Rule
        Count = $Count
        SortKey = $safePath + '|' + $Rule
    })
}


function Get-AssignmentCount {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)

    $count = 0
    foreach ($line in ($Content -split "`r?`n")) {
        $trimmed = $line.Trim()
        $commandParts = $trimmed -split '\s+', 2
        if (
            $commandParts.Count -eq 2 -and
            ($commandParts[0].Equals('export', [System.StringComparison]::OrdinalIgnoreCase) -or
                $commandParts[0].Equals('set', [System.StringComparison]::OrdinalIgnoreCase))
        ) {
            $trimmed = $commandParts[1].TrimStart()
        }
        $equalsIndex = $trimmed.IndexOf('=')
        if ($equalsIndex -lt 0) {
            continue
        }
        $assignmentName = $trimmed.Substring(0, $equalsIndex).Trim()
        if ($assignmentName.StartsWith('$env:', [System.StringComparison]::OrdinalIgnoreCase)) {
            $assignmentName = $assignmentName.Substring(5).TrimStart()
        }
        $value = $trimmed.Substring($equalsIndex + 1).Trim()
        foreach ($name in $script:SecretAssignmentNames) {
            if ($assignmentName.Equals($name, [System.StringComparison]::OrdinalIgnoreCase)) {
                if ($value.Length -gt 0 -and -not $value.StartsWith('#')) {
                    $unquoted = $value.Trim([char[]]@('"', "'"))
                    if ($unquoted.Length -gt 0) {
                        $count += 1
                    }
                }
                break
            }
        }
    }
    return $count
}


function Invoke-BoundedGit {
    param([Parameter(Mandatory = $true)][string]$Arguments)

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = 'git'
    $startInfo.Arguments = $Arguments
    $startInfo.WorkingDirectory = $script:RepositoryRoot
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $memory = New-Object System.IO.MemoryStream
    $processStarted = $false
    $stdoutTask = $null
    $stderrTask = $null
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        if (-not $process.Start()) {
            throw 'git process did not start'
        }
        $processStarted = $true
        $stdoutBuffer = New-Object byte[] 8192
        $stderrBuffer = New-Object byte[] 8192
        $stderrBytes = [int64]0
        $stdoutClosed = $false
        $stderrClosed = $false
        $stdoutTask = $process.StandardOutput.BaseStream.ReadAsync(
            $stdoutBuffer, 0, $stdoutBuffer.Length
        )
        $stderrTask = $process.StandardError.BaseStream.ReadAsync(
            $stderrBuffer, 0, $stderrBuffer.Length
        )

        while (-not ($stdoutClosed -and $stderrClosed -and $process.HasExited)) {
            if ($stopwatch.ElapsedMilliseconds -ge $script:GitDeadlineMilliseconds) {
                throw 'git discovery deadline exceeded'
            }

            $madeProgress = $false
            if (-not $stdoutClosed -and $stdoutTask.IsCompleted) {
                $read = [int]$stdoutTask.GetAwaiter().GetResult()
                if ($read -eq 0) {
                    $stdoutClosed = $true
                }
                else {
                    if (($memory.Length + $read) -gt $script:MaxGitOutputBytes) {
                        throw 'git stdout exceeded scanner limit'
                    }
                    $memory.Write($stdoutBuffer, 0, $read)
                    $stdoutTask = $process.StandardOutput.BaseStream.ReadAsync(
                        $stdoutBuffer, 0, $stdoutBuffer.Length
                    )
                }
                $madeProgress = $true
            }

            if (-not $stderrClosed -and $stderrTask.IsCompleted) {
                $read = [int]$stderrTask.GetAwaiter().GetResult()
                if ($read -eq 0) {
                    $stderrClosed = $true
                }
                else {
                    $stderrBytes += $read
                    if ($stderrBytes -gt $script:MaxGitErrorBytes) {
                        throw 'git stderr exceeded scanner limit'
                    }
                    $stderrTask = $process.StandardError.BaseStream.ReadAsync(
                        $stderrBuffer, 0, $stderrBuffer.Length
                    )
                }
                $madeProgress = $true
            }

            if (-not $madeProgress) {
                Start-Sleep -Milliseconds 10
            }
        }
        if ($process.ExitCode -ne 0) {
            throw 'git discovery failed'
        }
        return ,$memory.ToArray()
    }
    finally {
        if ($processStarted) {
            $shutdownStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            try {
                if (-not $process.HasExited) {
                    $process.Kill()
                }
            }
            catch { }
            try {
                $remaining = 1000 - [int]$shutdownStopwatch.ElapsedMilliseconds
                if ($remaining -gt 0 -and -not $process.HasExited) {
                    [void]$process.WaitForExit($remaining)
                }
            }
            catch { }
            foreach ($readTask in @($stdoutTask, $stderrTask)) {
                if ($null -eq $readTask) {
                    continue
                }
                try {
                    $remaining = 1000 - [int]$shutdownStopwatch.ElapsedMilliseconds
                    if ($remaining -gt 0) {
                        [void]$readTask.Wait($remaining)
                    }
                }
                catch { }
            }
        }
        $memory.Dispose()
        $process.Dispose()
    }
}


function ConvertFrom-StrictUtf8 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    $strictUtf8 = New-Object System.Text.UTF8Encoding($false, $true)
    return $strictUtf8.GetString($Bytes)
}


function Assert-RepositoryRoot {
    if ($script:RepositoryRootInvalid) {
        throw 'invalid repository root'
    }
    $bytes = Invoke-BoundedGit -Arguments 'rev-parse --show-toplevel'
    $topLevel = (ConvertFrom-StrictUtf8 -Bytes $bytes).TrimEnd([char[]]@("`r", "`n"))
    if ([string]::IsNullOrWhiteSpace($topLevel)) {
        throw 'git returned no repository root'
    }
    $resolvedTopLevel = [System.IO.Path]::GetFullPath($topLevel)
    if (-not $resolvedTopLevel.Equals($script:RepositoryRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'requested path is not the repository root'
    }
}


function Get-DefaultFiles {
    Assert-RepositoryRoot
    $bytes = Invoke-BoundedGit -Arguments '-c core.quotepath=false ls-files -co --exclude-standard -z'
    $relativeFiles = (ConvertFrom-StrictUtf8 -Bytes $bytes).Split([char]0)

    foreach ($relativePath in $relativeFiles) {
        if ($relativePath.Length -eq 0) {
            continue
        }
        if (Test-IsExcludedRelativePath -RelativePath $relativePath) {
            continue
        }
        if ([System.IO.Path]::IsPathRooted($relativePath)) {
            throw 'git returned a rooted path'
        }
        $literalPath = [System.IO.Path]::GetFullPath((Join-Path $script:RepositoryRoot $relativePath))
        $rootPrefix = $script:RepositoryRoot.TrimEnd([char[]]@('\', '/')) + [System.IO.Path]::DirectorySeparatorChar
        if (-not $literalPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'git returned a path outside the repository'
        }
        if (Test-Path -LiteralPath $literalPath -PathType Leaf) {
            $item = Get-Item -LiteralPath $literalPath -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
                Write-Output $item
            }
        }
    }
}


function Get-ExplicitFiles {
    param(
        [Parameter(Mandatory = $true)][string[]]$Inputs,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$OperationalResults
    )

    foreach ($inputPath in $Inputs) {
        if ([string]::IsNullOrWhiteSpace($inputPath) -or -not (Test-Path -LiteralPath $inputPath)) {
            $display = if ([string]::IsNullOrWhiteSpace($inputPath)) { '<empty>' } else { $inputPath }
            Add-Result -Results $OperationalResults -DisplayPath $display -Rule 'INPUT_MISSING' -Count 1
            continue
        }

        $item = Get-Item -LiteralPath $inputPath -Force
        if (-not $item.PSIsContainer) {
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
                Write-Output $item
            }
            continue
        }

        foreach ($file in (Get-ChildItem -LiteralPath $item.FullName -File -Recurse -Force)) {
            if (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
                Write-Output $file
            }
        }
    }
}


function Scan-File {
    param(
        [Parameter(Mandatory = $true)][System.IO.FileInfo]$File,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$Findings,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$OperationalResults
    )

    $displayPath = Get-DisplayPath -LiteralPath $File.FullName
    try {
        if ($script:InputPaths.Count -gt 0) {
            $bytes = [System.IO.File]::ReadAllBytes($File.FullName)
            $content = $script:Utf8NoBom.GetString($bytes)
        }
        else {
            if ($script:AggregateLimitExceeded) {
                return
            }
            $stream = [System.IO.File]::Open(
                $File.FullName,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite
            )
            try {
                $length = [int64]$stream.Length
                if ($length -gt $script:MaxRepositoryFileBytes) {
                    Add-Result -Results $OperationalResults -DisplayPath $displayPath -Rule 'FILE_SIZE_LIMIT' -Count 1
                    return
                }
                if ($script:RepositoryBytesScanned -gt ($script:MaxRepositoryScanBytes - $length)) {
                    Add-Result -Results $OperationalResults -DisplayPath '.' -Rule 'AGGREGATE_SCAN_LIMIT' -Count 1
                    $script:AggregateLimitExceeded = $true
                    return
                }

                $script:RepositoryBytesScanned += $length
                $bytes = New-Object byte[] ([int]$length)
                $offset = 0
                while ($offset -lt $bytes.Length) {
                    $read = $stream.Read($bytes, $offset, $bytes.Length - $offset)
                    if ($read -eq 0) {
                        throw 'file changed during scan'
                    }
                    $offset += $read
                }
                if ($stream.ReadByte() -ne -1) {
                    throw 'file changed during scan'
                }
                $content = $script:Utf8NoBom.GetString($bytes, 0, $bytes.Length)
            }
            finally {
                $stream.Dispose()
            }
        }
    }
    catch {
        Add-Result -Results $OperationalResults -DisplayPath $displayPath -Rule 'FILE_READ_ERROR' -Count 1
        return
    }

    foreach ($rule in $script:PatternRules) {
        $count = [regex]::Matches($content, [string]$rule.Pattern).Count
        if ($count -gt 0) {
            Add-Result -Results $Findings -DisplayPath $displayPath -Rule $rule.Id -Count $count
        }
    }

    $assignmentCount = Get-AssignmentCount -Content $content
    if ($assignmentCount -gt 0) {
        Add-Result -Results $Findings -DisplayPath $displayPath -Rule 'NONEMPTY_SECRET_ASSIGNMENT' -Count $assignmentCount
    }
}


function Write-ResultLines {
    param([Parameter(Mandatory = $true)][object[]]$Results)

    foreach ($result in ($Results | Sort-Object -Property SortKey)) {
        $line = '{0} rule={1} count={2}' -f $result.Path, $result.Rule, $result.Count
        [Console]::Out.WriteLine($line)
    }
}


$findings = New-Object 'System.Collections.Generic.List[object]'
$operationalResults = New-Object 'System.Collections.Generic.List[object]'

try {
    if ($script:InputPaths.Count -gt 0) {
        $files = @(Get-ExplicitFiles -Inputs $script:InputPaths -OperationalResults $operationalResults)
    }
    else {
        try {
            $files = @(Get-DefaultFiles)
        }
        catch {
            Add-Result -Results $operationalResults -DisplayPath '.' -Rule 'GIT_DISCOVERY_ERROR' -Count 1
            $files = @()
        }
    }

    $uniqueFiles = @{}
    foreach ($file in $files) {
        $uniqueFiles[$file.FullName] = $file
    }
    foreach ($file in ($uniqueFiles.Values | Sort-Object -Property FullName)) {
        Scan-File -File $file -Findings $findings -OperationalResults $operationalResults
    }

    $allResults = @()
    foreach ($result in $operationalResults) {
        $allResults += $result
    }
    foreach ($result in $findings) {
        $allResults += $result
    }
    if ($allResults.Count -gt 0) {
        Write-ResultLines -Results $allResults
    }
    if ($operationalResults.Count -gt 0) {
        exit 2
    }
    if ($findings.Count -gt 0) {
        exit 1
    }
    exit 0
}
catch {
    [Console]::Out.WriteLine('scripts/check_secret_patterns.ps1 rule=SCANNER_ERROR count=1')
    exit 2
}
