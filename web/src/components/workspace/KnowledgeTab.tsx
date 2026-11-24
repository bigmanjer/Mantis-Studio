"use client";
import { BookOpen, ChevronDown, ChevronRight, FileUp, Library, Loader2, Plus, Search, Sparkles, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { addKnowledgeDoc, deleteKnowledgeDoc, getLenses, searchKnowledge, type KnowledgeDoc } from "@/app/app/knowledge-actions";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import type { AuthorLens } from "@/data/knowledge-builtin";
import type { KnowledgeHit } from "@/lib/knowledge";
import { createClient } from "@/lib/supabase/client";
import type { Project } from "@/lib/types";

const BROWSE = ["opening chapter", "pacing", "dialogue subtext", "character arc", "mystery clues", "worldbuilding", "romance tension", "horror dread", "sagging middle", "point of view", "endings", "revision"];

/**
 * Knowledge Base (ported from the original MANTIS app): the writer's research and reference
 * documents, a built-in craft library, and author style lenses. The AI reads the relevant bits.
 */
export default function KnowledgeTab({ project, setProject }: { project: Project; setProject: React.Dispatch<React.SetStateAction<Project>> }) {
  const supabase = createClient();
  const confirm = useConfirm();
  const [docs, setDocs] = useState<KnowledgeDoc[] | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [passages, setPassages] = useState<Record<string, string[]>>({});
  const [query, setQuery] = useState("");
  const [where, setWhere] = useState<"all" | "mine" | "builtin">("all");
  const [hits, setHits] = useState<KnowledgeHit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addMode, setAddMode] = useState<"file" | "text">("file");
  const [scope, setScope] = useState<string>(project.id);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busyAdd, setBusyAdd] = useState(false);
  const [lenses, setLenses] = useState<{ all: AuthorLens[]; suggested: (AuthorLens & { why: string[] })[] } | null>(null);
  const [lensQuery, setLensQuery] = useState("");
  const chosen = useMemo(() => project.style_lenses ?? [], [project.style_lenses]);

  useEffect(() => {
    void supabase
      .from("knowledge_docs")
      .select("id, project_id, title, category, word_count, created_at")
      .or(`project_id.is.null,project_id.eq.${project.id}`)
      .order("created_at", { ascending: false })
      .then(({ data }) => setDocs((data ?? []) as KnowledgeDoc[]));
    void getLenses(project.id).then(setLenses);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.id]);

  async function saveProject(patch: Partial<Project>) {
    setProject((prev) => ({ ...prev, ...patch }));
    await supabase.from("projects").update(patch).eq("id", project.id);
  }

  async function run(q = query, w = where) {
    if (!q.trim()) return;
    setQuery(q);
    setSearching(true);
    setHits(await searchKnowledge(project.id, q, w));
    setSearching(false);
  }

  async function add(form: FormData) {
    setBusyAdd(true);
    setMsg(null);
    form.set("scope", scope);
    const res = await addKnowledgeDoc(form);
    setBusyAdd(false);
    if (res.error || !res.doc) return setMsg({ ok: false, text: res.error ?? "Couldn't add that." });
    setDocs((d) => [res.doc!, ...(d ?? [])]);
    setMsg({ ok: true, text: `Added “${res.doc.title}”. The AI will use it when it's relevant.` });
    setAdding(false);
  }

  async function remove(d: KnowledgeDoc) {
    const ok = await confirm({ title: `Delete “${d.title}”?`, body: "It will be removed from your Knowledge Base for every book that uses it.", confirmLabel: "Delete", danger: true });
    if (!ok) return;
    const res = await deleteKnowledgeDoc(d.id);
    if (!res.error) setDocs((list) => (list ?? []).filter((x) => x.id !== d.id));
  }

  async function toggleDoc(d: KnowledgeDoc) {
    if (open === d.id) return setOpen(null);
    setOpen(d.id);
    if (!passages[d.id]) {
      const { data } = await supabase.from("knowledge_chunks").select("content").eq("doc_id", d.id).order("position").limit(40);
      setPassages((p) => ({ ...p, [d.id]: (data ?? []).map((r) => r.content as string) }));
    }
  }

  async function sendTo(field: "style_guide" | "canon_rules", text: string) {
    const current = (project[field] ?? "").trim();
    await saveProject({ [field]: current ? `${current}\n${text}` : text } as Partial<Project>);
    setMsg({ ok: true, text: field === "style_guide" ? "Added to the style guide (Plan tab)." : "Added to the canon rules (Plan tab)." });
  }

  const toggleLens = (name: string) => {
    const next = chosen.includes(name) ? chosen.filter((n) => n !== name) : [...chosen, name].slice(-3);
    void saveProject({ style_lenses: next });
  };

  const lensMatches = lensQuery.trim()
    ? (lenses?.all ?? []).filter((l) => `${l.name} ${l.traits} ${l.works}`.toLowerCase().includes(lensQuery.toLowerCase())).slice(0, 8)
    : [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Knowledge Base</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Your research and reference notes, a built-in craft library, and style lenses. When the AI writes, it reads whatever here is relevant. Story facts still come from the World Bible.
          </p>
        </div>
        <label className="flex cursor-pointer items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm">
          <input type="checkbox" checked={project.use_knowledge !== false} onChange={(e) => void saveProject({ use_knowledge: e.target.checked })} />
          Let the AI use this for this book
        </label>
      </div>

      {msg && (
        <p className={`mt-4 rounded-lg border px-3 py-2 text-sm ${msg.ok ? "border-accent/30 bg-accent-soft text-accent" : "border-danger/30 bg-danger-soft text-danger"}`} role="status">
          {msg.text}
        </p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          {/* Search */}
          <section className="card p-5">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void run();
              }}
              className="flex flex-wrap gap-2"
            >
              <label className="relative min-w-0 flex-1">
                <Search size={15} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted" />
                <input className="input pl-9" placeholder="Search: e.g. “unreliable narrator”, “Victorian mourning”, “heist pacing”" value={query} onChange={(e) => setQuery(e.target.value)} />
              </label>
              <select className="input w-auto" value={where} onChange={(e) => setWhere(e.target.value as typeof where)} aria-label="Search in">
                <option value="all">Everything</option>
                <option value="mine">My documents</option>
                <option value="builtin">Craft library</option>
              </select>
              <button className="btn-primary" disabled={searching}>
                {searching ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />} Search
              </button>
            </form>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {BROWSE.map((b) => (
                <button key={b} onClick={() => void run(b, "builtin")} className="cursor-pointer rounded-full border border-line px-2.5 py-1 text-xs text-muted hover:text-text">
                  {b}
                </button>
              ))}
            </div>
            {hits && (
              <div className="mt-4 space-y-2">
                {hits.length === 0 && <p className="text-sm text-muted">Nothing found. Try other words, or add your own notes.</p>}
                {hits.map((h, i) => (
                  <div key={i} className="rounded-xl border border-line bg-panel p-3">
                    <p className="text-[11px] tracking-wide text-accent uppercase">
                      {h.source === "mine" ? `Your notes · ${h.title}` : `Craft library · ${h.category}`}
                    </p>
                    <p className="mt-1 text-sm whitespace-pre-line text-text/90">{h.text.slice(0, 1100)}</p>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs">
                      <button onClick={() => void sendTo("style_guide", h.text.slice(0, 600))} className="cursor-pointer text-accent hover:underline">
                        Add to style guide
                      </button>
                      <button onClick={() => void sendTo("canon_rules", h.text.slice(0, 600))} className="cursor-pointer text-muted hover:text-text">
                        Add to canon rules
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* My documents */}
          <section className="card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="flex items-center gap-2 font-semibold">
                  <Library size={16} className="text-accent" /> Your documents
                </h2>
                <p className="text-xs text-muted">Research, a series bible, character interviews, a craft book you own. Word, PDF, EPUB, text and more.</p>
              </div>
              <button onClick={() => setAdding((v) => !v)} className={adding ? "btn-ghost" : "btn-primary"}>
                {adding ? <X size={15} /> : <Plus size={15} />} {adding ? "Cancel" : "Add document"}
              </button>
            </div>

            {adding && (
              <form action={add} className="mt-4 space-y-3 rounded-xl border border-line bg-panel p-4">
                <div className="flex gap-1 rounded-lg border border-line bg-panel-2 p-0.5 text-xs">
                  {(["file", "text"] as const).map((m) => (
                    <button key={m} type="button" onClick={() => setAddMode(m)} className={`flex-1 cursor-pointer rounded-md py-1.5 ${addMode === m ? "bg-panel text-text" : "text-muted"}`}>
                      {m === "file" ? "Upload a file" : "Paste text"}
                    </button>
                  ))}
                </div>
                {addMode === "file" ? (
                  <label className="flex cursor-pointer flex-col items-center gap-1 rounded-xl border border-dashed border-line-strong p-5 text-center text-sm">
                    <FileUp size={20} className="text-accent" />
                    <span>Choose a file (up to 4 MB)</span>
                    <input name="file" type="file" required accept=".docx,.doc,.pdf,.rtf,.odt,.epub,.html,.htm,.md,.markdown,.txt" className="text-xs" />
                  </label>
                ) : (
                  <textarea name="text" rows={8} required className="input" placeholder="Paste research, notes or a reference passage…" />
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <input name="title" className="input" placeholder="Title (optional)" />
                  <select className="input" value={scope} onChange={(e) => setScope(e.target.value)} aria-label="Use for">
                    <option value={project.id}>Use for this book</option>
                    <option value="all">Use for all my books</option>
                  </select>
                </div>
                <button className="btn-primary w-full" disabled={busyAdd}>
                  {busyAdd ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />} {busyAdd ? "Reading…" : "Add to Knowledge Base"}
                </button>
              </form>
            )}

            <div className="mt-4 space-y-2">
              {docs === null ? (
                <p className="text-sm text-muted">Loading…</p>
              ) : docs.length === 0 ? (
                <p className="text-sm text-muted">No documents yet. Add research or notes and the AI will draw on them.</p>
              ) : (
                docs.map((d) => (
                  <div key={d.id} className="rounded-xl border border-line bg-panel">
                    <div className="flex items-center gap-2 p-3">
                      <button onClick={() => void toggleDoc(d)} className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 text-left" aria-expanded={open === d.id}>
                        {open === d.id ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium">{d.title}</span>
                          <span className="text-xs text-muted">
                            {d.category} · {d.word_count.toLocaleString()} words · {d.project_id ? "this book" : "all books"}
                          </span>
                        </span>
                      </button>
                      <button onClick={() => void remove(d)} className="btn-quiet h-8 w-8 p-0" aria-label={`Delete ${d.title}`}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                    {open === d.id && (
                      <div className="max-h-80 space-y-2 overflow-y-auto border-t border-line p-3 text-sm text-muted">
                        {(passages[d.id] ?? []).map((p, i) => (
                          <p key={i} className="whitespace-pre-line">
                            {p}
                          </p>
                        ))}
                        {!passages[d.id] && <Loader2 size={14} className="animate-spin" />}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </section>
        </div>

        {/* Style lenses */}
        <aside className="card h-fit p-5">
          <h2 className="flex items-center gap-2 font-semibold">
            <Sparkles size={16} className="text-accent" /> Style lenses
          </h2>
          <p className="mt-1 text-xs text-muted">
            Pick up to 3 authors whose craft you want to learn from. The AI borrows their techniques (structure, pacing, tone), never their sentences.
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {chosen.length === 0 && <span className="text-xs text-muted">None chosen.</span>}
            {chosen.map((n) => (
              <button key={n} onClick={() => toggleLens(n)} className="flex cursor-pointer items-center gap-1 rounded-full border border-accent bg-accent-soft px-2.5 py-1 text-xs text-accent">
                {n} <X size={11} />
              </button>
            ))}
          </div>
          <input className="input mt-3" placeholder="Find an author or a trait (e.g. “dread”)" value={lensQuery} onChange={(e) => setLensQuery(e.target.value)} />
          <ul className="mt-2 space-y-1.5">
            {(lensQuery.trim() ? lensMatches : lenses?.suggested ?? []).map((l) => (
              <li key={l.name}>
                <button onClick={() => toggleLens(l.name)} className={`w-full cursor-pointer rounded-lg border p-2 text-left text-xs transition ${chosen.includes(l.name) ? "border-accent bg-accent-soft" : "border-line hover:border-line-strong"}`}>
                  <span className="flex items-center justify-between font-medium text-text">
                    {l.name}
                    {chosen.includes(l.name) ? <X size={12} /> : <Plus size={12} />}
                  </span>
                  <span className="mt-0.5 block text-muted">{l.traits}</span>
                  {"why" in l && Array.isArray(l.why) && l.why.length > 0 && <span className="mt-0.5 block text-accent/80">Fits your book: {l.why.slice(0, 4).join(", ")}</span>}
                </button>
              </li>
            ))}
            {!lensQuery.trim() && lenses && lenses.suggested.length === 0 && (
              <li className="text-xs text-muted">Add a genre or premise in Plan and suggestions will appear here. Or search above.</li>
            )}
            {lensQuery.trim() && lensMatches.length === 0 && <li className="text-xs text-muted">No match among {lenses?.all.length ?? 0} authors.</li>}
            {!lenses && (
              <li className="text-xs text-muted">
                <Loader2 size={12} className="inline animate-spin" /> Loading…
              </li>
            )}
          </ul>
          <p className="mt-4 flex items-start gap-1.5 text-[11px] text-muted">
            <BookOpen size={12} className="mt-0.5 shrink-0" /> From MANTIS&apos;s built-in library of 250 authors, from Homer to today.
          </p>
        </aside>
      </div>
    </div>
  );
}
