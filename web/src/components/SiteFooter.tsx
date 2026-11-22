import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-muted sm:flex-row sm:justify-between">
        <p>© {new Date().getFullYear()} MANTIS Studio</p>
        <div className="flex gap-4">
          <Link href="/pricing" className="hover:text-text">
            Pricing
          </Link>
          <Link href="/legal/terms" className="hover:text-text">
            Terms
          </Link>
          <Link href="/legal/privacy" className="hover:text-text">
            Privacy
          </Link>
          <a href={`mailto:${process.env.NEXT_PUBLIC_SUPPORT_EMAIL || "support@mantis-studio.com"}`} className="hover:text-text">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
