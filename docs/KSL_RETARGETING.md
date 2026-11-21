# KSL research retargeting

This mapping is for the dev research page. It is a stylized pose, not a reviewed Kenyan Sign Language performance.

The public archive stores MediaPipe landmarks and does not store a frame rate. A packet keeps `fps` empty. Playback uses 12 frames per second only so a person can watch the clip. That number is not a measurement.

Left and right are not mirrored. Pose index 11 is the subject's left shoulder and index 12 is the right, in MediaPipe order. `left_hand` and `right_hand` stay under those names. Image x increases to the right and image y increases downward. After the shoulders are centered and the width is divided out, a point above the shoulders has a negative y. Drawing `origin + y * scale` on a canvas that points downward puts that point above the shoulders.

Normalization centers each frame on the shoulder midpoint and scales by shoulder width. A frame with a missing pose, or a shoulder width near zero, is dropped. Gaps of at most two frames are filled from the frames on either side. Smoothing is an exponential average: pose follows the new sample less than the hands do. Idle frames at the ends are trimmed when the wrists barely move. A clip is dropped when both hands are missing on more than 80 percent of the remaining frames. The quality number is hand coverage plus a cap on wrist motion. It is not a Deaf review and it is not a confidence score from the dataset. These files have no confidence channel.

Arms are a direction from the shoulder to the elbow and from the elbow to the wrist, written as a quaternion from the rest direction `(0, 1, 0)`. Hands follow the 21 MediaPipe bones. Each bend is clamped to 80 degrees. Face weights use a few mesh distances (mouth, eye span, lids, brow) and only when 468 face points are present. A missing channel holds the last good pose. It does not snap back to the identity pose.

The stickman is the normalized landmark x and y. The avatar uses fixed bone lengths along those quaternions, so the two pictures are not the same drawing.

Every research frame, including an exported SVG, carries this text: `RESEARCH SAMPLE: single word. Not a patient message. Not reviewed.` The citation is Maina et al., Data in Brief 60:111502 (2025), doi:10.1016/j.dib.2025.111502, and Zenodo doi:10.5281/zenodo.14974973.

Words are not chained into sentences. The patient clip route does not serve these packets.
