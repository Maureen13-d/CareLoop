"""The asset policy rejects raw footage and oversized binaries."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_ksl_assets as policy  # noqa: E402


LFS = b"version https://git-lfs.github.com/spec/v1\n"


def test_placeholder_motion_file_is_allowed():
    assert policy.reasons("assets/ksl/placeholders/wave.json", 1200, b"{") == []


def test_video_outside_approved_packs_is_refused():
    found = policy.reasons("demo/clip.mp4", 1000, b"\x00\x00")
    assert "video outside approved packs" in found


def test_raw_mocap_is_refused():
    assert "raw mocap" in policy.reasons("takes/session.bvh", 100, b"HIERARCHY")


def test_signer_photo_under_ksl_assets_is_refused():
    found = policy.reasons("assets/ksl/approved/signer.png", 100, b"\x89PNG")
    assert "signer photo" in found


def test_raw_capture_directory_is_refused():
    assert "raw capture path" in policy.reasons("capture/take1.txt", 10, b"x")


def test_approved_video_must_be_an_lfs_pointer():
    raw = policy.reasons("assets/ksl/approved/clip.mp4", 500, b"\x00\x00\x00")
    assert "approved video must be a Git LFS pointer" in raw
    assert policy.reasons("assets/ksl/approved/clip.mp4", 80, LFS) == []


def test_camera_originals_are_not_an_approved_pack():
    found = policy.reasons("assets/ksl/approved/take.mov", 80, LFS)
    assert "camera video is not an approved pack" in found


def test_placeholder_cannot_hide_a_video_or_grow_past_200kb():
    assert policy.reasons("assets/ksl/placeholders/clip.mp4", 100, b"\x00")
    assert "placeholder over 200 KB" in policy.reasons(
        "assets/ksl/placeholders/big.json",
        policy.PLACEHOLDER_MAX + 1,
        b"{",
    )


def test_oversized_binary_is_refused_unless_it_is_an_lfs_pointer():
    assert policy.reasons("rigs/avatar.glb", policy.MAX_BYTES + 1, b"glTF")
    assert policy.reasons("rigs/avatar.glb", policy.MAX_BYTES + 1, LFS) == []


def test_dataset_files_are_refused():
    pose = policy.reasons("data/external/ksl_pose/word.npy", 100, b"\x93NUMPY")
    assert "external dataset" in pose
    assert "numpy dataset file" in pose


def test_gitignore_blocks_raw_video_and_keeps_placeholder_notes():
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "capture/take1.mp4"],
        cwd=ROOT,
        check=False,
    )
    note = subprocess.run(
        ["git", "check-ignore", "-q", "assets/ksl/placeholders/README.md"],
        cwd=ROOT,
        check=False,
    )
    dataset = subprocess.run(
        ["git", "check-ignore", "-q", "data/external/ksl_pose/sample.npy"],
        cwd=ROOT,
        check=False,
    )
    assert ignored.returncode == 0
    assert note.returncode == 1
    assert dataset.returncode == 0


def test_tracked_tree_passes_the_policy():
    assert policy.scan(ROOT) == []
