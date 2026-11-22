import type { Metadata } from "next";
import { Inter, Literata } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const literata = Literata({ variable: "--font-literata", subsets: ["latin"] });

const description =
  "Plan, draft and keep your story's canon straight. Outlines, a chapter editor, a World Bible and AI assistance in one place. Free to start.";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "MANTIS Studio — the AI writing studio for novelists", template: "%s — MANTIS Studio" },
  description,
  icons: { icon: "/mantis_favicon.png" },
  openGraph: {
    type: "website",
    siteName: "MANTIS Studio",
    title: "MANTIS Studio — write the novel, keep the canon straight",
    description,
    images: [{ url: "/mantis_banner_dark.png", width: 1600, height: 600, alt: "MANTIS Studio" }],
  },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${literata.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}
