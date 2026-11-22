import { BookOpen, Check, Sparkles, Users } from "lucide-react";

/** A static, lightweight rendering of the real editor for the landing page hero. */
export default function EditorMock() {
  return (
    <div className="relative mx-auto max-w-5xl">
      <div className="pointer-events-none absolute -inset-x-10 -top-10 -bottom-10 rounded-[40px] bg-[radial-gradient(ellipse_at_center,var(--accent-soft),transparent_65%)]" />
      <div className="relative overflow-hidden rounded-2xl border border-line-strong bg-panel shadow-soft" aria-hidden>
        {/* window chrome */}
        <div className="flex items-center gap-2 border-b border-line bg-panel-2 px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-line-strong" />
          <span className="h-2.5 w-2.5 rounded-full bg-line-strong" />
          <span className="h-2.5 w-2.5 rounded-full bg-line-strong" />
          <span className="ml-3 text-xs text-muted">The Glass Orchard — Chapter 3</span>
          <span className="ml-auto hidden items-center gap-1 text-[11px] text-muted sm:flex">
            <Check size={12} className="text-accent" /> Saved
          </span>
        </div>
        <div className="grid text-left md:grid-cols-[180px_1fr_260px]">
          {/* chapters */}
          <div className="hidden border-r border-line p-3 md:block">
            <p className="px-2 text-[10px] font-semibold tracking-widest text-muted uppercase">Chapters</p>
            {[
              ["The Letter", "2,914"],
              ["First Harvest", "3,402"],
              ["The Collector", "1,288"],
              ["Night Picking", "—"],
            ].map(([t, w], i) => (
              <div key={t} className={`mt-1 rounded-lg px-2 py-1.5 ${i === 2 ? "bg-panel-3" : ""}`}>
                <p className={`truncate text-xs ${i === 2 ? "text-text" : "text-muted"}`}>{t}</p>
                <p className="text-[10px] text-muted">{w} words</p>
              </div>
            ))}
          </div>
          {/* page */}
          <div className="bg-paper px-6 py-6 sm:px-10">
            <p className="font-serif text-xl font-semibold">The Collector</p>
            <div className="mt-4 space-y-3 font-serif text-[14px] leading-7 text-text/90">
              <p>The stranger arrived with the first frost, his coat buttoned to the throat and his hands bare despite the cold.</p>
              <p>
                &ldquo;I hear your trees bear something unusual,&rdquo; he said, and Mara felt the orchard go still behind her, as if
                every branch were listening.
              </p>
              <p className="rounded-md border-l-2 border-accent bg-accent-soft px-3 py-1 text-text">
                She thought of the memory she had picked that morning — her mother laughing in a kitchen that no longer existed — and
                closed her hand around it in her pocket.
              </p>
            </div>
          </div>
          {/* ai panel */}
          <div className="hidden space-y-3 border-l border-line p-4 md:block">
            <div className="rounded-xl border border-line bg-panel-2 p-3">
              <p className="flex items-center gap-1.5 text-xs font-semibold">
                <Sparkles size={13} className="text-accent" /> AI assistant
              </p>
              <div className="mt-2 rounded-lg bg-accent px-2 py-1.5 text-center text-[11px] font-medium text-accent-fg">Continue writing</div>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {["Deepen POV", "Tighten", "Sensory"].map((p) => (
                  <span key={p} className="rounded-md border border-line px-1.5 py-0.5 text-[10px] text-muted">
                    {p}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-line bg-panel-2 p-3">
              <p className="flex items-center gap-1.5 text-xs font-semibold">
                <Users size={13} className="text-accent" /> Canon found
              </p>
              {[
                ["The Collector", "Character"],
                ["Frost Market", "Location"],
              ].map(([n, c]) => (
                <div key={n} className="mt-2 flex items-center justify-between text-[11px]">
                  <span>
                    {n} <span className="text-muted">· {c}</span>
                  </span>
                  <span className="text-accent">+ Add</span>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-line bg-panel-2 p-3 text-[11px] text-muted">
              <BookOpen size={13} className="text-accent" /> 7,604 / 90,000 words
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
