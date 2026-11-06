from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image

from spooky_eaf.core import (
    decode_image,
    get_frame,
    scan,
)


ASSETS = Path(
    r"C:\Users\Brittain\spooky\spooky-assets.bin"
)

REFERENCE_ROOT = Path(
    r"C:\Users\Brittain\spooky\Spooky-Animations"
)


ANIMATIONS = [
    "Happy",
    "Sad",
    "angry",
    "battery_connected",
    "confused",
    "cry",
    "listen",
    "low_battery",
    "neutral",
    "shocked",
    "sleep",
    "winking",
]


def rgba_sha256(image):
    rgba_bytes = image.convert("RGBA").tobytes()

    return sha256(rgba_bytes).hexdigest()


@pytest.fixture(scope="module")
def asset_data():
    assert ASSETS.exists(), (
        f"Asset image not found: {ASSETS}"
    )

    return ASSETS.read_bytes()


@pytest.fixture(scope="module")
def containers(asset_data):
    discovered = scan(asset_data)

    assert len(discovered) == len(ANIMATIONS), (
        f"Expected {len(ANIMATIONS)} containers, "
        f"found {len(discovered)}"
    )

    return discovered


@pytest.mark.parametrize(
    "container_index,name",
    list(enumerate(ANIMATIONS)),
)
def test_all_decoded_pixels_match_reference_pngs(
    asset_data,
    containers,
    container_index,
    name,
):
    container = containers[container_index]

    reference_frames = (
        REFERENCE_ROOT
        / name
        / "frames"
    )

    assert reference_frames.exists(), (
        f"Reference folder missing: "
        f"{reference_frames}"
    )

    decoded_count = 0

    for frame_index in range(
        container["frames"]
    ):
        frame = get_frame(
            asset_data,
            container,
            frame_index,
        )

        if frame[:2] != b"_S":
            continue

        decoded_image, header = decode_image(
            frame
        )

        reference_path = (
            reference_frames
            / f"frame_{frame_index:03d}.png"
        )

        assert reference_path.exists(), (
            f"{name} frame {frame_index}: "
            f"reference PNG missing: "
            f"{reference_path}"
        )

        with Image.open(reference_path) as reference:
            reference_rgba = (
                reference.convert("RGBA")
            )

            assert decoded_image.size == (
                reference_rgba.size
            ), (
                f"{name} frame {frame_index}: "
                f"dimension mismatch, "
                f"decoded={decoded_image.size}, "
                f"reference={reference_rgba.size}"
            )

            decoded_hash = rgba_sha256(
                decoded_image
            )

            reference_hash = rgba_sha256(
                reference_rgba
            )

        assert decoded_hash == reference_hash, (
            f"{name} frame {frame_index}: "
            "RGBA SHA-256 mismatch\n"
            f"decoded:   {decoded_hash}\n"
            f"reference: {reference_hash}"
        )

        assert header["width"] == decoded_image.width
        assert header["height"] == decoded_image.height

        decoded_count += 1

    expected_pngs = sorted(
        reference_frames.glob(
            "frame_*.png"
        )
    )

    assert decoded_count == len(expected_pngs), (
        f"{name}: decoded {decoded_count} "
        f"image frames but found "
        f"{len(expected_pngs)} reference PNGs"
    )


@pytest.mark.parametrize(
    "container_index,name",
    list(enumerate(ANIMATIONS)),
)
def test_animation_pixel_sequence_hash(
    asset_data,
    containers,
    container_index,
    name,
):
    """
    Produce one aggregate SHA-256 for each
    animation's complete RGBA frame sequence.
    """

    container = containers[container_index]

    decoded_sequence = sha256()
    reference_sequence = sha256()

    image_count = 0

    reference_frames = (
        REFERENCE_ROOT
        / name
        / "frames"
    )

    for frame_index in range(
        container["frames"]
    ):
        frame = get_frame(
            asset_data,
            container,
            frame_index,
        )

        if frame[:2] != b"_S":
            continue

        decoded_image, _ = decode_image(
            frame
        )

        reference_path = (
            reference_frames
            / f"frame_{frame_index:03d}.png"
        )

        assert reference_path.exists()

        decoded_rgba = (
            decoded_image
            .convert("RGBA")
            .tobytes()
        )

        with Image.open(reference_path) as reference:
            reference_rgba = (
                reference
                .convert("RGBA")
                .tobytes()
            )

        # Include dimensions and frame index so
        # structural changes also affect the hash.
        descriptor = (
            f"{frame_index}:"
            f"{decoded_image.width}x"
            f"{decoded_image.height}:"
        ).encode("ascii")

        decoded_sequence.update(descriptor)
        decoded_sequence.update(decoded_rgba)

        reference_sequence.update(descriptor)
        reference_sequence.update(reference_rgba)

        image_count += 1

    assert image_count > 0

    decoded_digest = (
        decoded_sequence.hexdigest()
    )

    reference_digest = (
        reference_sequence.hexdigest()
    )

    assert decoded_digest == reference_digest, (
        f"{name}: aggregate pixel-sequence "
        "SHA-256 mismatch\n"
        f"decoded:   {decoded_digest}\n"
        f"reference: {reference_digest}"
    )