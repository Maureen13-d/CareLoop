/** Skeleton for the first 55 How2Sign-MV3D joints. Body, then two hands. */

export const ASL_LABEL =
  "ASL RESEARCH: How2Sign sentence. Not a patient message. Not reviewed.";

const BODY = [
  [0, 1],
  [1, 4],
  [4, 7],
  [7, 10],
  [0, 2],
  [2, 5],
  [5, 8],
  [8, 11],
  [0, 3],
  [3, 6],
  [6, 9],
  [9, 12],
  [12, 15],
  [9, 13],
  [13, 16],
  [16, 18],
  [18, 20],
  [9, 14],
  [14, 17],
  [17, 19],
  [19, 21],
];

function chains(wrist, start) {
  const lines = [];
  for (let finger = 0; finger < 5; finger += 1) {
    const joint = start + finger * 3;
    lines.push([wrist, joint], [joint, joint + 1], [joint + 1, joint + 2]);
  }
  return lines;
}

export const ASL_EDGES = [...BODY, ...chains(20, 25), ...chains(21, 40)];

export function frameLines(points, skipLeft, skipRight) {
  const hidden = new Set();
  if (skipLeft) {
    for (let joint = 25; joint <= 39; joint += 1) hidden.add(joint);
  }
  if (skipRight) {
    for (let joint = 40; joint <= 54; joint += 1) hidden.add(joint);
  }
  return ASL_EDGES.filter(([start, end]) => !hidden.has(start) && !hidden.has(end)).map(
    ([start, end]) => [points[start][0], points[start][1], points[end][0], points[end][1]],
  );
}
