# KSL Motion Packet (KMP)

Version `kmp-1`. 30 frames a second.

A packet is recorded motion. Nothing in this format generates a sign from text.

## Channels on every frame

- **Body quaternions:** hips, spine, spine2, chest, neck, head, both shoulders, both upper arms, both lower arms, both wrists.
- **Hands:** 21 joints on each hand, as quaternions. Handshape is meaning, so these are not simplified to a fist pose.
- **Face:** 52 blendshape weights, ARKit names, from 0 to 1.
- **Gaze:** a direction for each eye.
- **Head pose:** a quaternion kept apart from the neck joint, so a nod stays on the head channel.

## Metadata

`clip_id`, `template_id`, `source_text_hash`, `signer_pseudonym`, `capture_method`, `label`, `fps`, `frame_count`, `duration_ms`, `rig_version`, `quality_score`.

`label` is `TEST_MOTION_NOT_SIGN` for the procedural wave used in development. That clip is not KSL. Production mode refuses it.

## Compression

`delta-int16-v1`. Quaternions and gaze are stored as deltas of signed 16-bit values scaled by 32767. Face weights are deltas of signed 8-bit values scaled by 127, so a full blink fits in one step. The bytes are base64 in `payload_b64`.

A 3 second wave-and-blink clip must stay under 150 KB. `backend/tests/test_ksl_kmp.py` checks that.

The checked-in file is `assets/ksl/placeholders/test_motion.json`.
