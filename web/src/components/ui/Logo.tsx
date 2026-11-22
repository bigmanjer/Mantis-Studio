import Image from "next/image";
import Link from "next/link";

export default function Logo({ href = "/", compact = false }: { href?: string; compact?: boolean }) {
  return (
    <Link href={href} className="group flex items-center gap-2.5" aria-label="MANTIS Studio home">
      <Image src="/mantis_favicon.png" alt="" width={30} height={30} className="transition group-hover:scale-105" />
      {!compact && (
        <span className="flex items-baseline gap-1.5">
          <span className="text-[15px] font-semibold tracking-[0.22em]">MANTIS</span>
          <span className="text-xs text-muted">Studio</span>
        </span>
      )}
    </Link>
  );
}
