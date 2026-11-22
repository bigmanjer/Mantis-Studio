"use client";
import { useCallback, useEffect, useRef, useState } from "react";

export type SaveState = "saved" | "saving" | "unsaved" | "error";

/** Debounced save. Call `schedule(patch)` on every change; it merges patches and saves after `delay` ms. */
export function useAutosave<T extends object>(save: (patch: Partial<T>) => Promise<{ error: unknown } | void>, delay = 800) {
  const [state, setState] = useState<SaveState>("saved");
  const pending = useRef<Partial<T>>({});
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saveRef = useRef(save);
  saveRef.current = save;

  const flush = useCallback(async () => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    const patch = pending.current;
    if (!Object.keys(patch).length) return;
    pending.current = {};
    setState("saving");
    const res = await saveRef.current(patch);
    if (res && res.error) {
      pending.current = { ...patch, ...pending.current };
      setState("error");
    } else {
      setState(Object.keys(pending.current).length ? "unsaved" : "saved");
    }
  }, []);

  const schedule = useCallback(
    (patch: Partial<T>) => {
      pending.current = { ...pending.current, ...patch };
      setState("unsaved");
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(flush, delay);
    },
    [delay, flush],
  );

  useEffect(() => {
    const onUnload = (e: BeforeUnloadEvent) => {
      if (Object.keys(pending.current).length) {
        void flush();
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", onUnload);
    return () => {
      window.removeEventListener("beforeunload", onUnload);
      void flush();
    };
  }, [flush]);

  return { state, schedule, flush };
}

export function SaveBadge({ state }: { state: SaveState }) {
  const text = { saved: "Saved", saving: "Saving…", unsaved: "Unsaved changes", error: "Save failed — retrying on next edit" }[state];
  const color = state === "error" ? "text-danger" : state === "saved" ? "text-muted" : "text-accent";
  return <span className={`text-xs ${color}`}>{text}</span>;
}
