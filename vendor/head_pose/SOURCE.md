# vendor/head_pose: source https://github.com/yakhyo/head-pose-estimation @ 0aad20b23a48526605d4e185de0d45ab05914ba2

| file | sha256 |
|---|---|
| models/head_pose/resnet18.onnx (release 'weights') | 61c34e877989412980d1ea80c52391250b074abc00d19a6100de5c8e999212ee |
| models/head_pose/det_10g.onnx (release 'weights') | 5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91 |
| vendor/head_pose/head_pose_onnx.py | b99f3fbf6ad236e7acf906d75dd47fe918d5d090bcff6bf44c7150c1d9434417 |
| vendor/head_pose/scrfd.py | eb7b154f6435d59c3b5d9579b979a3eb1fc00b95c0a05ceb0feb5aeee12377e2 |
| vendor/head_pose/LICENSE | a4f7998feb5c90555daae4329db61caf7049e6b2706991dc1d9eb2a0923847ae |

Weights: https://github.com/yakhyo/head-pose-estimation/releases/download/weights/resnet18.onnx and .../det_10g.onnx (models/ is gitignored).
Used record-only by headpose.py: the measured head turn is written into a recipe's face-choice evidence; it never changes which references are chosen.
Fit check 2026-10-07: SCRFD found the bowed faces of pins 5 and 6 that YuNet misses; on goals where both detectors work, the readings agree
within about 1 degree; keypoint crops (without a face detector) flipped the yaw sign on 2 of 5 goals, so they are not used.
