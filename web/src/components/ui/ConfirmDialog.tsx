"use client";
import { AlertTriangle } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

interface ConfirmOptions {
  title: string;
  body?: string;
  confirmLabel?: string;
  danger?: boolean;
}

type ConfirmFn = (opts: ConfirmOptions) => Promise<boolean>;
const ConfirmContext = createContext<ConfirmFn | null>(null);

/** Promise-based confirm dialog: `if (await confirm({ title: "Delete?" })) …` */
export function useConfirm(): ConfirmFn {
  const ctx = useContext(ConfirmContext);
  return ctx ?? (async (o) => window.confirm(o.title));
}

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [opts, setOpts] = useState<ConfirmOptions | null>(null);
  const resolver = useRef<((v: boolean) => void) | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);

  const confirm = useCallback<ConfirmFn>((o) => {
    setOpts(o);
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  useEffect(() => {
    if (opts && !dialog.current?.open) dialog.current?.showModal();
  }, [opts]);

  const close = (v: boolean) => {
    resolver.current?.(v);
    resolver.current = null;
    dialog.current?.close();
    setOpts(null);
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      <dialog
        ref={dialog}
        onCancel={(e) => {
          e.preventDefault();
          close(false);
        }}
        className="m-auto w-[min(92vw,420px)] rounded-2xl border border-line bg-panel p-0 text-text shadow-soft backdrop:bg-black/60 backdrop:backdrop-blur-sm"
      >
        {opts && (
          <div className="p-6">
            <div className="flex gap-4">
              {opts.danger && (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-danger-soft text-danger">
                  <AlertTriangle size={18} />
                </div>
              )}
              <div>
                <h2 className="font-semibold">{opts.title}</h2>
                {opts.body && <p className="mt-1.5 text-sm text-muted">{opts.body}</p>}
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => close(false)} className="btn-ghost" autoFocus>
                Cancel
              </button>
              <button
                onClick={() => close(true)}
                className={opts.danger ? "btn bg-danger text-white hover:opacity-90" : "btn-primary"}
              >
                {opts.confirmLabel ?? "Confirm"}
              </button>
            </div>
          </div>
        )}
      </dialog>
    </ConfirmContext.Provider>
  );
}
