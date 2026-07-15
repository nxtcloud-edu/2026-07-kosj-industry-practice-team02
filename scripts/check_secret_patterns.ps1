[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string[]]$Path,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AdditionalPath
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

$script:RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
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

    [void]$Results.Add([pscustomobject]@{
        Path = $DisplayPath
        Rule = $Rule
        Count = $Count
        SortKey = $DisplayPath + '|' + $Rule
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


function Get-DefaultFiles {
    $relativeFiles = @(
        & git -C $script:RepositoryRoot -c core.quotepath=false ls-files -co --exclude-standard 2>$null
    )
    $gitExitCode = $LASTEXITCODE
    if ($gitExitCode -ne 0) {
        throw 'git discovery failed'
    }

    foreach ($relativePath in $relativeFiles) {
        if ([string]::IsNullOrWhiteSpace($relativePath)) {
            continue
        }
        if (Test-IsExcludedRelativePath -RelativePath $relativePath) {
            continue
        }
        $literalPath = Join-Path $script:RepositoryRoot $relativePath
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
        $bytes = [System.IO.File]::ReadAllBytes($File.FullName)
        $content = $script:Utf8NoBom.GetString($bytes)
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
