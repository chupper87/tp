interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export default function ScoreRing({
  score,
  size = 56,
  strokeWidth = 3,
  label,
}: ScoreRingProps) {
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - score);
  const color =
    score >= 0.8
      ? "var(--color-glow)"
      : score >= 0.5
        ? "var(--color-sun)"
        : "var(--color-coral)";

  return (
    <div
      className="relative"
      style={{ width: size, height: size }}
      title={label}
    >
      <svg className="w-full h-full -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-reef)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center font-data font-600"
        style={{ color, fontSize: size * 0.28 }}
      >
        {Math.round(score * 100)}
      </span>
    </div>
  );
}
