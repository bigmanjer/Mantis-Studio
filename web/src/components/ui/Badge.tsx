const TONES = {
  neutral: "bg-panel-2 text-muted border-line",
  accent: "bg-accent-soft text-accent border-accent/25",
  danger: "bg-danger-soft text-danger border-danger/25",
} as const;

export default function Badge({
  tone = "neutral",
  children,
  className = "",
}: {
  tone?: keyof typeof TONES;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${TONES[tone]} ${className}`}>
      {children}
    </span>
  );
}
