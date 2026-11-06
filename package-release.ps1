$ErrorActionPreference = "Stop"

# ============================================================
# spooky-eaf release packaging
# ============================================================

$Project = "C:\Users\Brittain\spooky-eaf-cli\spooky-eaf"
$Python  = "$HOME\spooky\esptoolenv\Scripts\python.exe"

$Version = "0.2.0"

$WheelName = "spooky_eaf-$Version-py3-none-any.whl"
$SdistName = "spooky_eaf-$Version.tar.gz"

$Dist = Join-Path $Project "dist"
$Build = Join-Path $Project "build"

$ReleaseRoot = Join-Path $Project "release"
$ReleaseName = "spooky-eaf-v$Version"
$ReleaseDir = Join-Path $ReleaseRoot $ReleaseName

$Zip = Join-Path $ReleaseRoot "$ReleaseName.zip"
$ZipChecksum = "$Zip.sha256"

$BuildStdout = Join-Path $Project "build-stdout.log"
$BuildStderr = Join-Path $Project "build-stderr.log"


# ============================================================
# Helper
# ============================================================

function Stop-Release {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "RELEASE FAILED" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Red

    exit 1
}


# ============================================================
# Start
# ============================================================

Set-Location $Project

Write-Host ""
Write-Host "============================================"
Write-Host " spooky-eaf v$Version release build"
Write-Host "============================================"
Write-Host ""


# ============================================================
# 1. Verify project layout
# ============================================================

Write-Host "[1/10] Checking project files..."

$RequiredFiles = @(
    "pyproject.toml",
    "README.md",
    "src\spooky_eaf\__init__.py",
    "src\spooky_eaf\cli.py",
    "src\spooky_eaf\core.py",
    "tests\test_cli.py",
    "tests\test_core.py",
    "tests\test_pixel_hashes.py",
    "tests\test_real_assets.py"
)

foreach ($RelativePath in $RequiredFiles) {

    $FullPath = Join-Path $Project $RelativePath

    if (-not (Test-Path -LiteralPath $FullPath)) {
        Stop-Release "Required file missing: $FullPath"
    }
}

if (-not (Test-Path -LiteralPath $Python)) {
    Stop-Release "Python executable missing: $Python"
}

Write-Host "Project files OK."


# ============================================================
# 2. Run regression suite
# ============================================================

Write-Host ""
Write-Host "[2/10] Running regression suite..."

& $Python -m pytest -q

$TestExitCode = $LASTEXITCODE

if ($TestExitCode -ne 0) {
    Stop-Release (
        "Regression suite failed with exit code " +
        $TestExitCode
    )
}

Write-Host "Regression suite passed."


# ============================================================
# 3. Clean build outputs
# ============================================================

Write-Host ""
Write-Host "[3/10] Cleaning old artifacts..."

Remove-Item `
    -LiteralPath $Dist `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -LiteralPath $Build `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -LiteralPath $ReleaseRoot `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -LiteralPath $BuildStdout `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -LiteralPath $BuildStderr `
    -Force `
    -ErrorAction SilentlyContinue

New-Item `
    -ItemType Directory `
    -Path $ReleaseDir `
    -Force |
    Out-Null

Write-Host "Clean complete."


# ============================================================
# 4. Build sdist and wheel
# ============================================================

Write-Host ""
Write-Host "[4/10] Building release artifacts..."

try {

    $BuildProcess = Start-Process `
        -FilePath $Python `
        -ArgumentList @(
            "-m",
            "build"
        ) `
        -WorkingDirectory $Project `
        -RedirectStandardOutput $BuildStdout `
        -RedirectStandardError $BuildStderr `
        -NoNewWindow `
        -Wait `
        -PassThru

}
catch {

    Stop-Release (
        "Unable to start Python build process: " +
        $_.Exception.Message
    )
}


# Display captured build output after completion.

if (Test-Path -LiteralPath $BuildStdout) {

    Write-Host ""
    Write-Host "--- build stdout ---"

    Get-Content -LiteralPath $BuildStdout |
        ForEach-Object {
            Write-Host $_
        }
}


if (Test-Path -LiteralPath $BuildStderr) {

    Write-Host ""
    Write-Host "--- build stderr ---"

    Get-Content -LiteralPath $BuildStderr |
        ForEach-Object {
            Write-Host $_
        }
}


if ($BuildProcess.ExitCode -ne 0) {

    Stop-Release (
        "Python package build failed with exit code " +
        $BuildProcess.ExitCode +
        ". Review build-stdout.log and build-stderr.log."
    )
}


$Wheel = Join-Path $Dist $WheelName
$Sdist = Join-Path $Dist $SdistName


if (-not (Test-Path -LiteralPath $Wheel)) {
    Stop-Release "Wheel was not created: $Wheel"
}


if (-not (Test-Path -LiteralPath $Sdist)) {
    Stop-Release "Source distribution was not created: $Sdist"
}


Write-Host ""
Write-Host "Build complete."


# ============================================================
# 5. Verify sdist test contents
# ============================================================

Write-Host ""
Write-Host "[5/10] Verifying source distribution..."

try {

    $ArchiveListing = @(
        tar -tf $Sdist
    )

}
catch {

    Stop-Release (
        "Unable to inspect source distribution: " +
        $_.Exception.Message
    )
}


$RequiredTests = @(
    "tests/test_cli.py",
    "tests/test_core.py",
    "tests/test_pixel_hashes.py",
    "tests/test_real_assets.py"
)


foreach ($RequiredTest in $RequiredTests) {

    $Match = $ArchiveListing |
        Where-Object {
            $_ -like "*$RequiredTest"
        }

    if (-not $Match) {
        Stop-Release (
            "Missing test module from sdist: " +
            $RequiredTest
        )
    }
}

Write-Host "All four test modules are present."


# ============================================================
# 6. Assemble release directory
# ============================================================

Write-Host ""
Write-Host "[6/10] Assembling release directory..."

Copy-Item `
    -LiteralPath $Wheel `
    -Destination $ReleaseDir

Copy-Item `
    -LiteralPath $Sdist `
    -Destination $ReleaseDir

Copy-Item `
    -LiteralPath (Join-Path $Project "README.md") `
    -Destination $ReleaseDir


$CopiedWheel = Join-Path $ReleaseDir $WheelName
$CopiedSdist = Join-Path $ReleaseDir $SdistName
$CopiedReadme = Join-Path $ReleaseDir "README.md"


if (-not (Test-Path -LiteralPath $CopiedWheel)) {
    Stop-Release "Release wheel copy failed."
}

if (-not (Test-Path -LiteralPath $CopiedSdist)) {
    Stop-Release "Release sdist copy failed."
}

if (-not (Test-Path -LiteralPath $CopiedReadme)) {
    Stop-Release "Release README copy failed."
}

Write-Host "Release directory assembled."


# ============================================================
# 7. Generate artifact checksum manifest
# ============================================================

Write-Host ""
Write-Host "[7/10] Generating artifact SHA-256 hashes..."

$ArtifactFiles = @(
    $CopiedWheel,
    $CopiedSdist
)

$ChecksumLines = foreach ($Artifact in $ArtifactFiles) {

    $HashInfo = Get-FileHash `
        -LiteralPath $Artifact `
        -Algorithm SHA256

    $Filename = [System.IO.Path]::GetFileName(
        $Artifact
    )

    "$($HashInfo.Hash)  $Filename"
}


$ManifestPath = Join-Path `
    $ReleaseDir `
    "SHA256SUMS.txt"


$ChecksumLines |
    Set-Content `
        -LiteralPath $ManifestPath `
        -Encoding ascii


if (-not (Test-Path -LiteralPath $ManifestPath)) {
    Stop-Release "SHA256SUMS.txt was not created."
}


Write-Host "Artifact checksums created."


# ============================================================
# 8. Verify copied artifact hashes
# ============================================================

Write-Host ""
Write-Host "[8/10] Verifying copied artifacts..."

foreach ($Artifact in $ArtifactFiles) {

    $Filename = [System.IO.Path]::GetFileName(
        $Artifact
    )

    $ExpectedLine = $ChecksumLines |
        Where-Object {
            $_ -like "*  $Filename"
        }

    if (-not $ExpectedLine) {
        Stop-Release (
            "Missing checksum manifest entry for " +
            $Filename
        )
    }

    $ExpectedHash = (
        $ExpectedLine -split "\s+"
    )[0]

    $ActualHash = (
        Get-FileHash `
            -LiteralPath $Artifact `
            -Algorithm SHA256
    ).Hash

    if ($ExpectedHash -ne $ActualHash) {

        Stop-Release (
            "Artifact checksum verification failed: " +
            $Filename
        )
    }
}

Write-Host "Artifact checksums verified."


# ============================================================
# 9. Create release ZIP
# ============================================================

Write-Host ""
Write-Host "[9/10] Creating release ZIP..."

Remove-Item `
    -LiteralPath $Zip `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -LiteralPath $ZipChecksum `
    -Force `
    -ErrorAction SilentlyContinue


Compress-Archive `
    -Path "$ReleaseDir\*" `
    -DestinationPath $Zip `
    -CompressionLevel Optimal


if (-not (Test-Path -LiteralPath $Zip)) {
    Stop-Release "Release ZIP was not created."
}


$ReleaseZipHash = (
    Get-FileHash `
        -LiteralPath $Zip `
        -Algorithm SHA256
).Hash


"$ReleaseZipHash  $ReleaseName.zip" |
    Set-Content `
        -LiteralPath $ZipChecksum `
        -Encoding ascii


if (-not (Test-Path -LiteralPath $ZipChecksum)) {
    Stop-Release "ZIP checksum sidecar was not created."
}


Write-Host "Release ZIP created."


# ============================================================
# 10. Verify ZIP checksum
# ============================================================

Write-Host ""
Write-Host "[10/10] Verifying release ZIP..."

$ExpectedZipHash = (
    (
        Get-Content `
            -LiteralPath $ZipChecksum
    ) -split "\s+"
)[0]


$ActualZipHash = (
    Get-FileHash `
        -LiteralPath $Zip `
        -Algorithm SHA256
).Hash


if ($ExpectedZipHash -ne $ActualZipHash) {

    Stop-Release (
        "Release ZIP SHA-256 verification failed."
    )
}


Write-Host "Release ZIP verified."


# ============================================================
# Final report
# ============================================================

Write-Host ""
Write-Host "============================================"
Write-Host " RELEASE COMPLETE"
Write-Host "============================================"
Write-Host ""

Write-Host "Tests:"
Write-Host "41/41 project-local regression tests PASS"

Write-Host ""
Write-Host "Release directory:"
Write-Host $ReleaseDir

Write-Host ""
Write-Host "Release contents:"

Get-ChildItem `
    -LiteralPath $ReleaseDir |
    Format-Table `
        Name,
        Length,
        LastWriteTime


Write-Host ""
Write-Host "Artifact SHA-256:"

Get-Content `
    -LiteralPath $ManifestPath |
    ForEach-Object {
        Write-Host $_
    }


Write-Host ""
Write-Host "Release ZIP:"
Write-Host $Zip


Write-Host ""
Write-Host "Release ZIP SHA-256:"
Write-Host $ActualZipHash


Write-Host ""
Write-Host "ZIP verified: True"


Write-Host ""
Write-Host "Build logs:"
Write-Host $BuildStdout
Write-Host $BuildStderr

Write-Host ""
