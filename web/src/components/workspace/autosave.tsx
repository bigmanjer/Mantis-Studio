"use client";
import { useCallback, useEffect, useRef, useState } from "react";

export type SaveState = "saved" | "saving" | "unsaved" | "error" | "offline" | "conflict";

/** What a save function reports. `conflict` stops automatic retries until the writer chooses. */
export type SaveResult = { error: unknown; conflict?: boolean } | void;

/**
 * Debounced save. Call `schedule(patch)` on every change; it merges patches and saves after `delay` ms.
 * Failed saves keep the changes and retry on their own (sooner when the connection comes back),
 * and closing the tab with unsaved changes asks first.
 */
export function useAutosave<T extends object>(save: (patch: Partial<T>) => Promise<SaveResult>, delay = 800) {
  const [state, setState] = useState<SaveState>("saved");
  const pending = useRef<Partial<T>>({});
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retry = useRef<ReturnType<typeof setTimeout> | null>(null);
  const failures = useRef(0);
  const inFlight = useRef(false);
  const blocked = useRef(false);
  const saveRef = useRef(save);
  saveRef.current = save;

  const flush = useCallback(async (): Promise<void> => {
    if (timer.current) clearTimeout(timer.current);
    if (retry.current) clearTimeout(retry.current);
    timer.current = retry.current = null;
    if (inFlight.current || blocked.current) return;
    const patch = pending.current;
    if (!Object.keys(patch).length) return;
    pending.current = {};
    inFlight.current = true;
    setState("saving");
    let res: SaveResult;
    try {
      res = await saveRef.current(patch);
    } catch (e) {
      res = { error: e };
    }
    inFlight.current = false;
    if (res && res.error) {
      // Keep the changes (newer edits win over the failed patch) and try again shortly.
      pending.current = { ...patch, ...pending.current };
      if (res.conflict) {
        blocked.current = true;
        setState("conflict");
        return;
      }
      failures.current++;
      setState(typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "error");
      const wait = Math.min(30_000, 2000 * 2 ** Math.min(failures.current - 1, 4));
      retry.current = setTimeout(() => void flush(), wait);
    } else {
      failures.current = 0;
      if (Object.keys(pending.current).length) {
        setState("unsaved");
        timer.current = setTimeout(() => void flush(), delay);
      } else setState("saved");
    }
  }, [delay]);

  const schedule = useCallback(
    (patch: Partial<T>) => {
      pending.current = { ...pending.current, ...patch };
      if (blocked.current) return; // waiting for the writer to resolve a conflict
      setState("unsaved");
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void flush(), delay);
    },
    [delay, flush],
  );

  /** After a conflict: save again (overwriting), or drop the pending changes. */
  const resolve = useCallback(
    (how: "save" | "discard") => {
      blocked.current = false;
      if (how === "discard") {
        pending.current = {};
        setState("saved");
      } else void flush();
    },
    [flush],
  );

  useEffect(() => {
    const onUnload = (e: BeforeUnloadEvent) => {
      if (Object.keys(pending.current).length || inFlight.current) {
        void flush();
        e.preventDefault();
      }
    };
    const onOnline = () => {
      if (Object.keys(pending.current).length) void flush();
    };
    window.addEventListener("beforeunload", onUnload);
    window.addEventListener("online", onOnline);
    return () => {
      window.removeEventListener("beforeunload", onUnload);
      window.removeEventListener("online", onOnline);
      if (retry.current) clearTimeout(retry.current);
      void flush();
    };
  }, [flush]);

  return { state, schedule, flush, resolve, hasPending: () => Object.keys(pending.current).length > 0 };
}

export function SaveBadge({ state }: { state: SaveState }) {
  const text = {
    saved: "Saved",
    saving: "Saving…",
    unsaved: "Unsaved changes",
    error: "Couldn't save, retrying…",
    offline: "Offline, will save when you're back",
    conflict: "Changed elsewhere",
  }[state];
  const color = state === "error" || state === "conflict" ? "text-danger" : state === "saved" ? "text-muted" : "text-accent";
  return (
    <span className={`text-xs ${color}`} role="status" aria-live="polite">
      {text}
    </span>
  );
}
