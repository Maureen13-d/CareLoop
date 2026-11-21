"""Zip and landmark helpers stay on safe bytes. They do not unpickle."""

import io
import pickle
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ksl_dataset_index as index  # noqa: E402


def test_zip_index_reads_names_and_sizes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("Pose Data/Batch 1/7/Extract/Landmarks/HELP.npy", b"pose")
    rows = index.parse_zip_index(buffer.getvalue())
    assert rows[0]["name"].endswith("HELP.npy")
    assert rows[0]["size"] == 4


def test_channel_counts_do_not_need_numpy():
    frames = [
        {
            "pose": [(0.1, 0.2, 0.3), (0.4, 0.5, 0.6)],
            "left_hand": [],
            "right_hand": [(1.1, 1.2, 1.3)],
            "face": [(2.1, 2.2, 2.3)],
        },
        {
            "pose": [(3.1, 3.2, 3.3)],
            "left_hand": [(4.1, 4.2, 4.3)],
            "right_hand": [],
            "face": [(5.1, 5.2, 5.3), (5.4, 5.5, 5.6)],
        },
    ]
    counts = index.channel_counts(pickle.dumps(frames, protocol=4))
    assert counts == [
        {"pose": 2, "left_hand": 0, "right_hand": 1, "face": 1},
        {"pose": 1, "left_hand": 1, "right_hand": 0, "face": 2},
    ]


def test_landmark_frames_keep_the_coordinates():
    frame = {
        "pose": [(0.1, 0.2, 0.3), (0.4, 0.5, 0.6)],
        "left_hand": [],
        "right_hand": [(1.1, 1.2, 1.3)],
        "face": [(2.1, 2.2, 2.3)],
    }
    got = index.landmark_frames(pickle.dumps([frame], protocol=4))
    assert got[0]["pose"][0] == [0.1, 0.2, 0.3]
    assert got[0]["pose"][1] == [0.4, 0.5, 0.6]
    assert got[0]["left_hand"] == []
    assert got[0]["right_hand"] == [[1.1, 1.2, 1.3]]
    assert got[0]["face"] == [[2.1, 2.2, 2.3]]


def test_menu_summary_counts_exact_labels_only():
    rows = [
        {"name": "Pose Data/Batch 1/7/Extract/Landmarks/HELP.npy"},
        {"name": "Pose Data/Batch 1/7/Extract/Stickmans/HELP.mp4"},
        {"name": "Pose Data/Batch 1/8/Extract/Landmarks/INTERPRET.npy"},
        {"name": "Pose Data/Batch 1/8/Extract/Stickmans/INTERPRET.mp4"},
        {"name": "Pose Data/Batch 1/"},
    ]
    summary = index.summarise(rows)
    assert summary["menu"]["HELP"]["files"] == 1
    assert summary["menu"]["INTERPRETER"]["files"] == 0
    assert "INTERPRET" in summary["similar"]["INTERPRETER"]
    assert summary["paired_stickman_videos"] == 2
