import subprocess
from pathlib import Path


CLI = Path(
    r"C:\Users\Brittain\spooky\wheel-test"
    r"\Scripts\spooky-eaf.exe"
)

HAPPY = Path(
    r"C:\Users\Brittain\spooky"
    r"\spooky-extracted\Happy.full.eaf"
)


def test_metadata_command():
    result = subprocess.run(
        [
            str(CLI),
            "metadata",
            str(HAPPY),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert '"frame": 42' in output
    assert '"valid": true' in output
    assert '"field_1": 1' in output
    assert '"text_length": 31' in output

    assert (
        "online convert 0.1.4_2025-09-01"
        in output
    )