/**
 * The CareLoop pathway drawn as a loop: from a concerning check to the hospital
 * taking over, with the loop closing once care has started. Decorative; the same
 * steps are described in text beside it.
 */
const STEPS = [
  "Check needs a closer look",
  "Joins on any phone",
  "Names what is in the way",
  "A navigator helps",
  "Visit is booked",
  "Arrives at the clinic",
  "Hospital team takes over",
];

export function JourneyLoop({ className }: { className?: string }) {
  const cx = 210;
  const cy = 210;
  const r = 150;
  // seven stops around most of the circle, leaving a gap where the loop closes
  const start = -200;
  const sweep = 300;
  const points = STEPS.map((label, index) => {
    const angle = ((start + (sweep * index) / (STEPS.length - 1)) * Math.PI) / 180;
    return { label, x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), angle };
  });
  const arcStart = points[0];
  const arcEnd = points[points.length - 1];

  return (
    <svg viewBox="-185 -6 790 432" aria-hidden="true" className={className}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgb(255 255 255 / 0.08)" strokeWidth="26" />
      <path
        d={`M ${arcStart.x} ${arcStart.y} A ${r} ${r} 0 1 1 ${arcEnd.x} ${arcEnd.y}`}
        fill="none"
        stroke="var(--teal)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      {/* the closing stretch: dashed, because CareLoop only watches it lightly */}
      <path
        d={`M ${arcEnd.x} ${arcEnd.y} A ${r} ${r} 0 0 1 ${arcStart.x} ${arcStart.y}`}
        fill="none"
        stroke="rgb(231 245 241 / 0.45)"
        strokeWidth="2"
        strokeDasharray="3 7"
        strokeLinecap="round"
      />
      {points.map((point, index) => (
        <g key={point.label}>
          <circle cx={point.x} cy={point.y} r={index === 0 ? 9 : 7} fill={index === 0 ? "var(--on-dark)" : "var(--emerald)"} stroke="var(--teal)" strokeWidth="3" />
          <text
            x={cx + (r + 34) * Math.cos(point.angle)}
            y={cy + (r + 34) * Math.sin(point.angle)}
            fill="rgb(231 245 241 / 0.82)"
            fontSize="16"
            textAnchor={Math.cos(point.angle) > 0.25 ? "start" : Math.cos(point.angle) < -0.25 ? "end" : "middle"}
            dominantBaseline="central"
          >
            {point.label}
          </text>
        </g>
      ))}
      <text x={cx} y={cy - 8} textAnchor="middle" fill="white" fontSize="30" fontWeight="600">
        No one lost
      </text>
      <text x={cx} y={cy + 24} textAnchor="middle" fill="rgb(231 245 241 / 0.7)" fontSize="16">
        between the check and the visit
      </text>
    </svg>
  );
}
