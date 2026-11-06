# spooky-eaf

**Version:** 0.1.0  
**Status:** 12/12 recovered Spooky EAF containers validated | 41/41 project-local regression tests passing

`spooky-eaf` is a Python command-line tool for inspecting, scanning, decoding, and recovering EAF animation assets.

The project grew out of the recovery of animation data from `spooky-assets.bin` and packages the validated decoding logic into a reusable CLI.

## Features

- Scan binary asset images for checksum-valid EAF containers
- Inspect EAF frame counts, dimensions, and observed frame types
- Validate container checksums and frame boundaries
- Decode the 8-bit indexed `_S` frames found in the recovered Spooky assets
- Decode the RLE image blocks used by the recovered animation set
- Expand BGRA palette entries into RGBA image data
- Export decoded frames as PNG
- Assemble decoded frames into animated GIF files
- Parse the observed `_C` converter metadata structure
- Report truncated or malformed `_C` metadata without treating it as image data
- Produce human-readable or JSON EAF scan results

## Installation

Install the wheel:

```powershell
python -m pip install spooky_eaf-0.1.0-py3-none-any.whl
```

For development, install the source tree in editable mode:

```powershell
python -m pip install -e .
```

After installation:

```powershell
spooky-eaf --help
```

## CLI Commands

### Inspect an EAF

```powershell
spooky-eaf inspect animation.eaf
```

Example output from the recovered Happy animation:

```text
Format: EAF
Frames: 43
Checksum: VALID
Frame types: {'_S': 42, '_C': 1}
Dimensions: 125x160
Metadata: 'online convert 0.1.4_2025-09-01' valid=True
```

### Scan a binary for EAF containers

```powershell
spooky-eaf scan spooky-assets.bin
```

JSON output:

```powershell
spooky-eaf scan spooky-assets.bin --json
```

### Decode an EAF

```powershell
spooky-eaf decode animation.eaf -o recovered --fps 20
```

The current decoder writes recovered PNG frames under:

```text
recovered/frames/
```

and generates an animated GIF using the requested frame rate.

### Inspect `_C` metadata

```powershell
spooky-eaf metadata animation.eaf
```

For the recovered Spooky files containing `_C` metadata, the observed converter string is:

```text
online convert 0.1.4_2025-09-01
```

## Validated Spooky Animation Set

v0.1.0 was tested against 12 EAF containers recovered from the Spooky asset image:

| Animation | Container Frames | Decoded `_S` Frames | Dimensions |
|---|---:|---:|---:|
| Happy | 43 | 42 | 125x160 |
| Sad | 97 | 96 | 125x160 |
| angry | 51 | 50 | 125x160 |
| battery_connected | 41 | 41 | 125x160 |
| confused | 78 | 77 | 125x160 |
| cry | 44 | 43 | 125x160 |
| listen | 51 | 50 | 100x46 |
| low_battery | 48 | 48 | 125x160 |
| neutral | 89 | 88 | 125x160 |
| shocked | 35 | 34 | 125x160 |
| sleep | 119 | 118 | 125x160 |
| winking | 15 | 14 | 125x160 |

Ten of these containers include one `_C` metadata record. `battery_connected` and `low_battery` contain only the recovered image records.

## Regression Testing

The project-local v0.1.0 regression suite passed:

```text
Core unit tests:             2/2 PASS
Real-asset tests:           14/14 PASS
Pixel SHA-256 tests:        24/24 PASS
CLI metadata test:           1/1 PASS
-----------------------------------------
Project-local test suite:   41/41 PASS
```

Final recorded validation run:

```text
41 passed in 7.20s
```

The regression suite exercises:

- RLE decompression
- Valid `_C` metadata parsing
- EAF container discovery
- Container checksum validation
- Frame-table parsing
- `_S` frame decoding
- Recovered dimensions and pixel counts
- All 12 recovered Spooky EAF containers
- Known converter metadata
- Per-frame decoded RGBA comparisons
- Aggregate animation pixel-sequence comparisons
- Wheel-installed CLI metadata verification

## Pixel-Level Regression

The packaged decoder was compared with the previously validated PNG recovery set.

For every recovered image frame:

```text
EAF frame
   ↓
_S parsing
   ↓
RLE decompression
   ↓
palette expansion
   ↓
RGBA bytes
   ↓
SHA-256 comparison
```

All 12 recovered animations passed the per-frame pixel regression.

The tests also construct an aggregate pixel-sequence digest for each animation so that changes in decoded frame data, frame ordering, dimensions, or frame indices affect the regression result.

## Test Files

The source distribution includes:

```text
tests/test_cli.py
tests/test_core.py
tests/test_pixel_hashes.py
tests/test_real_assets.py
```

Some real-asset regression tests depend on the locally recovered Spooky binary, reference PNG files, and project-specific Windows paths.

They are included as recovery-validation tests rather than as a fully self-contained public fixture suite.

## Wheel Validation

The v0.1.0 wheel was installed into a clean Python 3.13 virtual environment.

The wheel-installed CLI successfully:

- displayed command help
- inspected `Happy.full.eaf`
- validated its EAF checksum
- identified 42 `_S` frames and one `_C` record
- reported its 125x160 dimensions
- parsed its converter metadata
- passed the installed metadata-command integration test

## Observed EAF Container Structure

The recovered containers use the following outer structure:

```text
Offset  Size     Description
0x00    1        Magic: 0x89
0x01    3        Format: EAF
0x04    4        Total frame count
0x08    4        Additive checksum
0x0C    4        Length of frame table + frame data
0x10    N        Frame table
0x10+N  M        Frame region
```

Each observed frame-table entry contains:

```text
uint32 frame_size
uint32 frame_offset
```

Recovered frames begin with the marker:

```text
5A 5A
```

followed by the frame payload.

## `_S` Image Records

The recovered Spooky `_S` image records tested for v0.1.0 use:

- 8-bit indexed color
- 256-entry palettes
- four stored bytes per palette entry
- alpha values in the palette data
- block-based image storage
- RLE compression for the recovered image blocks

For the recovered RLE blocks, encoding identifier `0` was observed.

Decoded image values are palette indices that are expanded into RGBA output.

## `_C` Metadata

Ten recovered containers contain the same `_C` metadata payload.

Observed converter text:

```text
online convert 0.1.4_2025-09-01
```

Observed fields include:

```text
field_1 = 1
text_length = 31
```

The meaning of `field_1` has not been established.

v0.1.0 therefore preserves it under the neutral name `field_1` instead of assigning it an undocumented semantic meaning.

## Validated Format Scope

This release implements the EAF behavior required by the recovered Spooky animation set.

The format observations in this project should not yet be treated as a complete specification for every possible EAF variant.

In particular, v0.1.0's validated image-decoding scope is the 8-bit indexed, RLE-compressed `_S` data present in the recovered Spooky animations.

## Building From Source

Install the development dependencies used by the project, then run:

```powershell
python -m pytest -q
```

For the validated project environment, the expected regression result was:

```text
41 passed
```

Build the distributions with:

```powershell
python -m build
```

The release process produces:

```text
dist/
├── spooky_eaf-0.1.0-py3-none-any.whl
└── spooky_eaf-0.1.0.tar.gz
```

## Release Packaging

The project release workflow:

1. verifies required project files
2. runs the project-local regression suite
3. cleans previous build artifacts
4. builds the source distribution and wheel
5. verifies the expected test modules are present in the source distribution
6. assembles the release directory
7. generates SHA-256 hashes
8. verifies the copied artifacts
9. creates the release ZIP
10. verifies the release ZIP checksum

The release packaging script is:

```text
package-release.ps1
```

## Release Status

At the v0.1.0 validation checkpoint:

```text
12/12 recovered EAF containers decoded     PASS
41/41 project-local regression tests       PASS
Per-frame RGBA pixel regression            PASS
12 aggregate animation regressions         PASS
CLI metadata integration test              PASS
Source distribution build                  PASS
Wheel built from source distribution       PASS
Clean wheel installation                   PASS
Real EAF inspection                        PASS
Four test modules included in sdist        PASS
Release ZIP integrity verification         PASS
```

## Release Checksums

The release packaging workflow generates the canonical artifact hashes in:

```text
SHA256SUMS.txt
```

and a separate checksum sidecar for:

```text
spooky-eaf-v0.1.0.zip
```

Because packaging metadata and documentation affect distribution bytes, the checksums from the final successful packaging run should be treated as authoritative.

---

`spooky-eaf v0.1.0` establishes the first frozen and regression-tested baseline for continued Spooky EAF recovery and format research.