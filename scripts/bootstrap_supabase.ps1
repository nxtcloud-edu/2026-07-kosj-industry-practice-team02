param(
    [switch]$VerifyOnly,
    [string]$ArchivePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Throw-BootstrapFailure {
    param(
        [string]$Step,
        [string]$Reason,
        [int]$Code
    )

    $failure = New-Object System.Exception("controlled bootstrap failure")
    $failure.Data["step"] = $Step
    $failure.Data["reason"] = $Reason
    $failure.Data["code"] = $Code
    throw $failure
}

function Resolve-SafeChildPath {
    param(
        [string]$Root,
        [string]$Candidate
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root)
    $candidateFull = [System.IO.Path]::GetFullPath($Candidate)
    $rootPrefix = $rootFull.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidateFull.StartsWith(
        $rootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw New-Object System.InvalidOperationException("unsafe local tooling path")
    }
    return $candidateFull
}

function Remove-OwnedPath {
    param(
        [string]$Root,
        [string]$Candidate
    )

    $safePath = Resolve-SafeChildPath -Root $Root -Candidate $Candidate
    if (Test-Path -LiteralPath $safePath) {
        Remove-Item -LiteralPath $safePath -Recurse -Force -ErrorAction Stop
    }
}

function Test-SupabaseVersion {
    param(
        [string]$BinaryPath,
        [string]$ExpectedVersion
    )

    $process = $null
    try {
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $BinaryPath
        $startInfo.Arguments = "--version"
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true

        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            return $false
        }
        if (-not $process.WaitForExit(15000)) {
            try {
                $process.Kill()
            }
            catch {
                # The stable parent failure is sufficient; never expose child details.
            }
            return $false
        }

        $childOutput = $process.StandardOutput.ReadToEnd()
        $null = $process.StandardError.ReadToEnd()
        if ($process.ExitCode -ne 0) {
            return $false
        }
        return [string]::Equals(
            $childOutput.Trim(),
            $ExpectedVersion,
            [System.StringComparison]::Ordinal
        )
    }
    catch {
        return $false
    }
    finally {
        if ($null -ne $process) {
            $process.Dispose()
        }
    }
}

$scriptDirectory = [System.IO.Path]::GetFullPath($PSScriptRoot)
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory ".."))
$toolRoot = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot ".tools\supabase"))
$manifestPath = [System.IO.Path]::GetFullPath(
    (Join-Path $scriptDirectory "supabase-cli.version.json")
)
$ownedTempArchive = $null
$ownedTempDirectory = $null
$exitCode = 0
$outputLines = New-Object System.Collections.Generic.List[string]

try {
    if ($args.Count -ne 0) {
        Throw-BootstrapFailure -Step "VALIDATE-SUPABASE-ARGUMENTS" -Reason "invalid" -Code 2
    }

    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch {
        Throw-BootstrapFailure -Step "LOAD-SUPABASE-MANIFEST" -Reason "operational" -Code 2
    }

    $requiredProperties = @(
        "version",
        "release",
        "published_at",
        "asset",
        "size_bytes",
        "url",
        "sha256"
    )
    $manifestProperties = @($manifest.PSObject.Properties.Name)
    foreach ($property in $requiredProperties) {
        if ($property -notin $manifestProperties) {
            Throw-BootstrapFailure -Step "VALIDATE-SUPABASE-MANIFEST" -Reason "invalid" -Code 2
        }
    }

    $approvedVersion = "2.109.1"
    $approvedRelease = "v2.109.1"
    $approvedPublishedAt = "2026-07-07T09:00:28Z"
    $approvedAsset = "supabase_2.109.1_windows_amd64.zip"
    $approvedSize = [int64]75309565
    $approvedSha256 = "d0d270692cf78b8aa56545461f02cdf929ce9bb94e95e5e66404fd0e7d2c0c16"
    $approvedUrl = (
        "https://github.com/supabase/cli/releases/download/v2.109.1/" +
        "supabase_2.109.1_windows_amd64.zip"
    )

    if (
        ([string]$manifest.version -cne $approvedVersion) -or
        ([string]$manifest.release -cne $approvedRelease) -or
        ([string]$manifest.published_at -cne $approvedPublishedAt) -or
        ([string]$manifest.asset -cne $approvedAsset) -or
        ([int64]$manifest.size_bytes -ne $approvedSize) -or
        ([string]$manifest.sha256 -cne $approvedSha256)
    ) {
        Throw-BootstrapFailure -Step "VALIDATE-SUPABASE-MANIFEST" -Reason "unapproved-pin" -Code 2
    }

    $manifestUri = $null
    if (-not [System.Uri]::TryCreate(
        [string]$manifest.url,
        [System.UriKind]::Absolute,
        [ref]$manifestUri
    )) {
        Throw-BootstrapFailure -Step "VALIDATE-SUPABASE-MANIFEST" -Reason "unapproved-source" -Code 2
    }
    if (
        ($manifestUri.Scheme -cne "https") -or
        ($manifestUri.Host -cne "github.com") -or
        ([string]$manifest.url -cne $approvedUrl)
    ) {
        Throw-BootstrapFailure -Step "VALIDATE-SUPABASE-MANIFEST" -Reason "unapproved-source" -Code 2
    }
    $manifestDownloadUrl = [string]$manifest.url

    $versionDirectory = Resolve-SafeChildPath -Root $toolRoot -Candidate (
        Join-Path $toolRoot $approvedRelease
    )
    $binaryPath = Resolve-SafeChildPath -Root $toolRoot -Candidate (
        Join-Path $versionDirectory "supabase.exe"
    )

    if ($VerifyOnly) {
        if (-not [string]::IsNullOrWhiteSpace($ArchivePath)) {
            Throw-BootstrapFailure -Step "VALIDATE-SUPABASE-ARGUMENTS" -Reason "invalid" -Code 2
        }
        if (-not (Test-Path -LiteralPath $binaryPath -PathType Leaf)) {
            Throw-BootstrapFailure -Step "VERIFY-SUPABASE-BINARY" -Reason "missing" -Code 2
        }

        $outputLines.Add("[START] step=VERIFY-SUPABASE-VERSION") | Out-Null
        if (-not (Test-SupabaseVersion -BinaryPath $binaryPath -ExpectedVersion $approvedVersion)) {
            Throw-BootstrapFailure -Step "VERIFY-SUPABASE-VERSION" -Reason "child" -Code 1
        }
        $outputLines.Add("[PASS] step=VERIFY-SUPABASE-VERSION") | Out-Null
    }
    elseif (
        (Test-Path -LiteralPath $binaryPath -PathType Leaf) -and
        [string]::IsNullOrWhiteSpace($ArchivePath)
    ) {
        $outputLines.Add("[START] step=VERIFY-SUPABASE-VERSION") | Out-Null
        if (-not (Test-SupabaseVersion -BinaryPath $binaryPath -ExpectedVersion $approvedVersion)) {
            Throw-BootstrapFailure -Step "VERIFY-SUPABASE-VERSION" -Reason "child" -Code 1
        }
        $outputLines.Add("[PASS] step=VERIFY-SUPABASE-VERSION") | Out-Null
    }
    else {
        $archiveToVerify = $null
        if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
            $null = New-Item -ItemType Directory -Path $toolRoot -Force
            $ownedTempArchive = Resolve-SafeChildPath -Root $toolRoot -Candidate (
                Join-Path $toolRoot (
                    ".supabase-download-" + [guid]::NewGuid().ToString("N") + ".zip"
                )
            )
            $outputLines.Add("[START] step=DOWNLOAD-SUPABASE-ARCHIVE") | Out-Null
            try {
                $null = Invoke-WebRequest -UseBasicParsing -Uri $manifestDownloadUrl -OutFile $ownedTempArchive
            }
            catch {
                Throw-BootstrapFailure -Step "DOWNLOAD-SUPABASE-ARCHIVE" -Reason "operational" -Code 2
            }
            $outputLines.Add("[PASS] step=DOWNLOAD-SUPABASE-ARCHIVE") | Out-Null
            $archiveToVerify = $ownedTempArchive
        }
        else {
            if ([System.IO.Path]::IsPathRooted($ArchivePath)) {
                $archiveToVerify = [System.IO.Path]::GetFullPath($ArchivePath)
            }
            else {
                $archiveToVerify = [System.IO.Path]::GetFullPath(
                    (Join-Path $scriptDirectory $ArchivePath)
                )
            }
            if (-not (Test-Path -LiteralPath $archiveToVerify -PathType Leaf)) {
                Throw-BootstrapFailure -Step "LOAD-SUPABASE-ARCHIVE" -Reason "missing" -Code 2
            }
        }

        $outputLines.Add("[START] step=VERIFY-SUPABASE-ARCHIVE") | Out-Null
        try {
            $archiveInfo = Get-Item -LiteralPath $archiveToVerify -Force
            $archiveHash = Get-FileHash -LiteralPath $archiveToVerify -Algorithm SHA256
        }
        catch {
            Throw-BootstrapFailure -Step "VERIFY-SUPABASE-ARCHIVE" -Reason "operational" -Code 2
        }
        if (
            ([int64]$archiveInfo.Length -ne $approvedSize) -or
            (-not [string]::Equals(
                [string]$archiveHash.Hash,
                $approvedSha256,
                [System.StringComparison]::OrdinalIgnoreCase
            ))
        ) {
            Throw-BootstrapFailure -Step "VERIFY-SUPABASE-ARCHIVE" -Reason "integrity" -Code 1
        }

        if (Test-Path -LiteralPath $binaryPath -PathType Leaf) {
            $outputLines.Add("[START] step=VERIFY-SUPABASE-VERSION") | Out-Null
            if (-not (Test-SupabaseVersion -BinaryPath $binaryPath -ExpectedVersion $approvedVersion)) {
                Throw-BootstrapFailure -Step "VERIFY-SUPABASE-VERSION" -Reason "child" -Code 1
            }
        }
        else {
            if (Test-Path -LiteralPath $versionDirectory) {
                Throw-BootstrapFailure -Step "INSTALL-SUPABASE-BINARY" -Reason "operational" -Code 2
            }
            $null = New-Item -ItemType Directory -Path $toolRoot -Force
            $ownedTempDirectory = Resolve-SafeChildPath -Root $toolRoot -Candidate (
                Join-Path $toolRoot (
                    "." + $approvedRelease + "-" + [guid]::NewGuid().ToString("N") + ".tmp"
                )
            )
            $null = New-Item -ItemType Directory -Path $ownedTempDirectory
            try {
                Expand-Archive -LiteralPath $archiveToVerify -DestinationPath $ownedTempDirectory
            }
            catch {
                Throw-BootstrapFailure -Step "VERIFY-SUPABASE-ARCHIVE" -Reason "integrity" -Code 1
            }

            $stagedBinary = Resolve-SafeChildPath -Root $toolRoot -Candidate (
                Join-Path $ownedTempDirectory "supabase.exe"
            )
            if (-not (Test-Path -LiteralPath $stagedBinary -PathType Leaf)) {
                Throw-BootstrapFailure -Step "VERIFY-SUPABASE-ARCHIVE" -Reason "integrity" -Code 1
            }
            $outputLines.Add("[START] step=VERIFY-SUPABASE-VERSION") | Out-Null
            if (-not (Test-SupabaseVersion -BinaryPath $stagedBinary -ExpectedVersion $approvedVersion)) {
                Throw-BootstrapFailure -Step "VERIFY-SUPABASE-VERSION" -Reason "child" -Code 1
            }

            Move-Item -LiteralPath $ownedTempDirectory -Destination $versionDirectory
            $ownedTempDirectory = $null
        }

        $outputLines.Add("[PASS] step=VERIFY-SUPABASE-ARCHIVE") | Out-Null
        $outputLines.Add("[PASS] step=VERIFY-SUPABASE-VERSION") | Out-Null
    }
}
catch {
    $failure = $_.Exception
    if (
        $failure.Data.Contains("step") -and
        $failure.Data.Contains("reason") -and
        $failure.Data.Contains("code")
    ) {
        $exitCode = [int]$failure.Data["code"]
        $outputLines.Add(
            "[FAIL] step=" + [string]$failure.Data["step"] +
            " reason=" + [string]$failure.Data["reason"] +
            " code=" + [string]$failure.Data["code"]
        ) | Out-Null
    }
    else {
        $exitCode = 2
        $outputLines.Add("[FAIL] step=BOOTSTRAP-SUPABASE reason=operational code=2") | Out-Null
    }
}
finally {
    try {
        if ($null -ne $ownedTempDirectory) {
            Remove-OwnedPath -Root $toolRoot -Candidate $ownedTempDirectory
        }
        if ($null -ne $ownedTempArchive) {
            Remove-OwnedPath -Root $toolRoot -Candidate $ownedTempArchive
        }
    }
    catch {
        if ($exitCode -eq 0) {
            $exitCode = 2
            $outputLines.Add("[FAIL] step=CLEANUP-SUPABASE-TEMP reason=operational code=2") |
                Out-Null
        }
    }
}

foreach ($line in $outputLines) {
    [Console]::Out.WriteLine($line)
}
exit $exitCode
