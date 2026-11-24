export function timeAgo(iso: string): string {
  const s = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return "just now";
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.round(h / 24);
  if (d < 30) return `${d}d ago`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function compact(n: number): string {
  if (n >= 1_000_000) return `${+(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1)}M`;
  return n >= 10_000 ? `${(n / 1000).toFixed(n >= 100_000 ? 0 : 1)}k` : n.toLocaleString();
}

const COVERS = [
  ["#14532d", "#4ade80"],
  ["#1e3a5f", "#60a5fa"],
  ["#4a1d4a", "#e879f9"],
  ["#5b2a0e", "#fb923c"],
  ["#3b2f0b", "#facc15"],
  ["#123b3b", "#2dd4bf"],
  ["#3a1420", "#fb7185"],
];

/** Deterministic cover gradient for a project, so each book gets its own color. */
export function coverFor(seed: string): string {
  let h = 0;
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const [a, b] = COVERS[h % COVERS.length];
  return `linear-gradient(135deg, ${a} 0%, ${a} 45%, ${b} 160%)`;
}
