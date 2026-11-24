import { Check, Minus } from "lucide-react";

// Deliberately compares against tool *types*, not named competitors, so it never goes stale or misstates anyone's pricing.
const ROWS: [string, boolean | string, boolean | string, boolean | string][] = [
  ["Free plan that includes AI", true, false, "Trial only"],
  ["Use your own AI key", true, true, false],
  ["AI included in the plan", "1M tokens / $19", false, true],
  ["Story bible the AI reads from", true, true, true],
  ["Builds your outline and story bible from an imported draft", true, false, "Some"],
  ["Word and ebook (EPUB) export", "Pro", true, "Some"],
  ["One subscription covers app + AI", "Studio", false, true],
];

function Cell({ v }: { v: boolean | string }) {
  if (v === true) return <Check size={18} className="mx-auto text-accent" aria-label="Yes" />;
  if (v === false) return <Minus size={18} className="mx-auto text-muted/50" aria-label="No" />;
  return <span className="text-xs text-muted">{v}</span>;
}

export default function Comparison() {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-panel">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-line text-left">
            <th className="p-4 font-medium text-muted"> </th>
            <th className="w-36 bg-accent-soft p-4 text-center font-semibold text-accent">MANTIS</th>
            <th className="w-36 p-4 text-center font-medium text-muted">Key-only planners</th>
            <th className="w-36 p-4 text-center font-medium text-muted">Credit-based AI writers</th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map(([label, a, b, c]) => (
            <tr key={label} className="border-b border-line last:border-0">
              <td className="p-4">{label}</td>
              <td className="bg-accent-soft/60 p-4 text-center">
                <Cell v={a} />
              </td>
              <td className="p-4 text-center">
                <Cell v={b} />
              </td>
              <td className="p-4 text-center">
                <Cell v={c} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
