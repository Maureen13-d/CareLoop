# KSL dataset inspection

Inspected on 21 Nov 2026 from the Zenodo API. No dataset file is in git. The archive was not saved: it is 1,539,828,602 bytes and this machine had about 148 MB free. The directory and ten landmark samples were read with HTTP range requests. Landmark files were not unpickled.

## Which record

The DOI in the prompt, `10.5281/zenodo.14974973`, is the latest version. Its API metadata says `access_right: restricted` and lists no public files. A full-file checksum of that version could not be run.

The public file is the earlier version `10.5281/zenodo.14338329`, title `KSL POSE DATASET`, licence `cc-by-4.0`, one file `Pose Data.zip`. Zenodo publishes `md5:3cf8e3b30583ea1be34a65d285099b65`. A streaming check of that md5 started and the connection dropped, so the checksum is not confirmed on this machine. The central directory of that URL did parse as a zip of 3,153 members.

## What is in the open zip

| Item | Count |
|---|---|
| Members, including directories | 3,153 |
| Directories | 163 |
| Landmark files (`.npy`) | 1,495 |
| Stickman videos (`.mp4`) | 1,495 |
| Pairs with the same batch, folder, and gloss | 1,495 |
| Distinct glosses | 728 |
| Recording folders | 40 |
| Batch 1 landmark files | 623 |
| Batch 2 landmark files | 872 |

Uncompressed sizes from the zip directory: landmark files about 830 MB, stickman videos about 5.6 GB. The videos are compressed inside the 1.54 GB zip. File members use deflate. This inspection did not decode the videos.

The paper is described as citing both about 20,000 and about 30,000 videos. This public zip has 1,495 videos. The restricted newer record was not available, so its count is unknown.

Paths look like:

`Pose Data/Batch 1/196/Extract/Landmarks/BETTER.npy`

`Pose Data/Batch 1/196/Extract/Stickmans/BETTER.mp4`

The folder numbers are `65`, `76`, `91`, `103`, `112`, `119`, `129`, `131`, `132`, `135`, `140`, `146`, `147`, `148`, `149`, `154`, `160`, `161`, `162`, `165`, `166`, `167`, `173`, `174`, `196`, `198`, `201`, `203`, `204`, `205`, `206`, `207`, `208`, `232`, `233`, `234`, `235`, `238`, `251`, and `264`. Nothing in the path says these are signer ids. They are recording folders only.

Some names are not single clean words. Nine files are named `.mp4.npy`. Others include `0`, `4`, `10`, `24`, `MY ` with a trailing space, `BOY THAT`, and `NICE TWIST`.

## What one landmark file contains

The files are NumPy format 1.0 object arrays (`descr: |O`). The array body is a pickle. This inspection walked the pickle opcodes and did not call `pickle.loads` or `numpy.load`.

Each array is one clip. Its length is the frame count. A frame is a dict with four keys: `pose`, `left_hand`, `right_hand`, and `face`. Each value is a list of 3-number points. On the sampled frames the full lists are 33 pose points, 21 points a hand, and 468 face points. That is the MediaPipe layout. The file does not store frames per second, a signer id, or a confidence channel.

The first file for each menu word that exists was read. Frame count matched the array shape in every sample. Pose and face were present on every sampled frame. Hands were often an empty list. "Empty" here means a missing list for that frame, not a low confidence score. There is no confidence score in the file.

| Gloss | File | Frames | Frames missing left hand | Frames missing right hand |
|---|---|---|---|---|
| NO | Batch 2/148 | 16 | 16 | 0 |
| SAME | Batch 1/201 | 20 | 3 | 13 |
| BETTER | Batch 1/196 | 35 | 0 | 9 |
| HELP | Batch 1/201 | 21 | 7 | 11 |
| HOSPITAL | Batch 2/91 | 30 | 23 | 0 |
| GO | Batch 1/201 | 20 | 0 | 13 |
| PAIN | Batch 1/205 | 38 | 3 | 2 |
| MONEY | Batch 1/238 | 40 | 40 | 19 |
| TRANSPORT | Batch 1/201 | 61 | 21 | 21 |
| STOP | Batch 1/251 | 36 | 30 | 0 |

These ten files are a sample, one per gloss. The other copies of the same gloss were not opened. Missing-hand rates for the whole 1,495 are not known.

## What this does not support yet

The bytes are still pickled object arrays. They must be converted to plain numbers in an isolated environment before the app reads them. Faces must not be reconstructed to identify anyone. No frames-per-second value was in the files. No quality score from the later normalizer exists yet.
