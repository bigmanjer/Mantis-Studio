"use client";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { NAV as LINKS } from "./nav";

export default function MobileMenu({ signedIn }: { signedIn: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="md:hidden">
      <button onClick={() => setOpen(!open)} className="btn-quiet h-9 w-9 p-0" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open}>
        {open ? <X size={18} /> : <Menu size={18} />}
      </button>
      {open && (
        <div className="absolute inset-x-0 top-16 border-b border-line bg-bg px-4 pb-6 shadow-soft">
          <nav className="flex flex-col py-2" aria-label="Mobile">
            {LINKS.map((l) => (
              <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="border-b border-line py-3 text-sm">
                {l.label}
              </Link>
            ))}
            {!signedIn && (
              <Link href="/login" onClick={() => setOpen(false)} className="py-3 text-sm">
                Log in
              </Link>
            )}
          </nav>
        </div>
      )}
    </div>
  );
}
