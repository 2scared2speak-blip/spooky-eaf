from pathlib import Path

import pytest

from spooky_eaf.core import (
    scan,
    get_frame,
    parse_c,
    decode_image,
)


ASSETS = Path(
    r"C:\Users\Brittain\spooky\spooky-assets.bin"
)


EXPECTED = [
    ("Happy", 43, 42, (125, 160)),
    ("Sad", 97, 96, (125, 160)),
    ("angry", 51, 50, (125, 160)),
    ("battery_connected", 41, 41, (125, 160)),
    ("confused", 78, 77, (125, 160)),
    ("cry", 44, 43, (125, 160)),
    ("listen", 51, 50, (100, 46)),
    ("low_battery", 48, 48, (125, 160)),
    ("neutral", 89, 88, (125, 160)),
    ("shocked", 35, 34, (125, 160)),
    ("sleep", 119, 118, (125, 160)),
    ("winking", 15, 14, (125, 160)),
]


@pytest.fixture(scope="module")
def assets():
    assert ASSETS.exists(), (
        f"Asset image missing: {ASSETS}"
    )

    return ASSETS.read_bytes()


@pytest.fixture(scope="module")
def containers(assets):
    found = scan(assets)

    assert len(found) == 12, (
        f"Expected 12 valid EAF containers, "
        f"found {len(found)}"
    )

    return found


@pytest.mark.parametrize(
    "container_index,name,expected_frames,"
    "expected_images,expected_size",
    [
        (
            index,
            name,
            frames,
            images,
            size,
        )
        for index, (
            name,
            frames,
            images,
            size,
        ) in enumerate(EXPECTED)
    ],
)
def test_container_full_decode(
    assets,
    containers,
    container_index,
    name,
    expected_frames,
    expected_images,
    expected_size,
):
    container = containers[container_index]

    assert container["frames"] == expected_frames

    image_count = 0
    metadata_count = 0

    for frame_index in range(
        container["frames"]
    ):
        frame = get_frame(
            assets,
            container,
            frame_index,
        )

        frame_type = frame[:2]

        if frame_type == b"_S":
            image, header = decode_image(frame)

            assert image.size == expected_size

            assert (
                header["width"],
                header["height"],
            ) == expected_size

            # Force Pillow to materialize the
            # complete decoded pixel buffer.
            rgba = image.convert("RGBA").tobytes()

            expected_bytes = (
                expected_size[0]
                * expected_size[1]
                * 4
            )

            assert len(rgba) == expected_bytes

            image_count += 1

        elif frame_type == b"_C":
            metadata = parse_c(frame)

            assert metadata["valid"], (
                f"{name} frame {frame_index}: "
                f"{metadata['error']}"
            )

            metadata_count += 1

        else:
            pytest.fail(
                f"{name} frame {frame_index}: "
                f"unexpected type {frame_type!r}"
            )

    assert image_count == expected_images

    expected_metadata = (
        expected_frames - expected_images
    )

    assert metadata_count == expected_metadata


def test_all_container_checksums_valid(
    containers,
):
    assert len(containers) == 12

    for container in containers:
        assert container["checksum"] >= 0


def test_known_metadata(
    assets,
    containers,
):
    metadata_records = []

    for container in containers:
        for frame_index in range(
            container["frames"]
        ):
            frame = get_frame(
                assets,
                container,
                frame_index,
            )

            if frame[:2] == b"_C":
                metadata_records.append(
                    parse_c(frame)
                )

    assert len(metadata_records) == 10

    for metadata in metadata_records:
        assert metadata["valid"]
        assert metadata["field_1"] == 1
        assert metadata["text_length"] == 31

        assert metadata["text"] == (
            "online convert "
            "0.1.4_2025-09-01"
        )