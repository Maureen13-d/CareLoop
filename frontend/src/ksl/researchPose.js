/** Draw helpers for one research word. The stickman uses landmark x,y.
 * The avatar uses fixed-length bones along the retargeted directions.
 */

export const BANNER_COLOR = "#7a1f1f";
export const PLAYBACK_FPS = 12;

const POSE_EDGES = [
  [11, 12],
  [11, 13],
  [13, 15],
  [12, 14],
  [14, 16],
  [11, 23],
  [12, 24],
  [23, 24],
  [23, 25],
  [25, 27],
  [24, 26],
  [26, 28],
];

const HAND_CHAINS = [
  [0, 1, 2, 3, 4],
  [0, 5, 6, 7, 8],
  [0, 9, 10, 11, 12],
  [0, 13, 14, 15, 16],
  [0, 17, 18, 19, 20],
];

const FINGERS = ["thumb_mcp", "index_mcp", "middle_mcp", "ring_mcp", "pinky_mcp"];

export function rotateVector(quat, vector) {
  const [qx, qy, qz, qw] = quat;
  const [vx, vy, vz] = vector;
  const tx = 2 * (qy * vz - qz * vy);
  const ty = 2 * (qz * vx - qx * vz);
  const tz = 2 * (qx * vy - qy * vx);
  return [
    vx + qw * tx + (qy * tz - qz * ty),
    vy + qw * ty + (qz * tx - qx * tz),
    vz + qw * tz + (qx * ty - qy * tx),
  ];
}

export function boneEnd(origin, quat, length) {
  const direction = rotateVector(quat, [0, 1, 0]);
  return [origin[0] + direction[0] * length, origin[1] + direction[1] * length];
}

function chainSegments(points, chains) {
  const lines = [];
  for (const chain of chains) {
    for (let index = 0; index < chain.length - 1; index += 1) {
      const start = points[chain[index]];
      const end = points[chain[index + 1]];
      if (!start || !end) continue;
      lines.push([start[0], start[1], end[0], end[1]]);
    }
  }
  return lines;
}

export function stickSegments(frame) {
  const pose = frame?.pose || [];
  const lines = [];
  for (const [start, end] of POSE_EDGES) {
    if (!pose[start] || !pose[end]) continue;
    lines.push([pose[start][0], pose[start][1], pose[end][0], pose[end][1]]);
  }
  lines.push(...chainSegments(frame?.left_hand || [], HAND_CHAINS));
  lines.push(...chainSegments(frame?.right_hand || [], HAND_CHAINS));
  return lines;
}

function armBones(shoulder, rig) {
  if (!rig?.upper || !rig?.lower) return [];
  const elbow = boneEnd(shoulder, rig.upper, 0.72);
  const wrist = boneEnd(elbow, rig.lower, 0.64);
  const lines = [
    [shoulder[0], shoulder[1], elbow[0], elbow[1]],
    [elbow[0], elbow[1], wrist[0], wrist[1]],
  ];
  const hand = rig.hand || {};
  for (const name of FINGERS) {
    if (!hand[name]) continue;
    const tip = boneEnd(wrist, hand[name], 0.28);
    lines.push([wrist[0], wrist[1], tip[0], tip[1]]);
  }
  return lines;
}

export function avatarSegments(frame) {
  const left = [-0.55, 0];
  const right = [0.55, 0];
  const lines = [
    [left[0], left[1], right[0], right[1]],
    [0, 0, 0, 0.95],
    [-0.28, 0.95, 0.28, 0.95],
  ];
  const arms = frame?.arms || {};
  lines.push(...armBones(left, { ...arms.left, hand: frame?.hands?.left }));
  lines.push(...armBones(right, { ...arms.right, hand: frame?.hands?.right }));
  return lines;
}

export function project(x, y, originX, originY, scale) {
  return [originX + x * scale, originY + y * scale];
}
