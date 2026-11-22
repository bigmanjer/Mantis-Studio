import type { Metadata, Viewport } from "next";
import { Inter, Literata } from "next/font/google";
import "./globals.css";
import { siteUrl } from "@/lib/env";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const literata = Literata({ variable: "--font-literata", subsets: ["latin"] });

const description =
  "Plan, draft and keep your story's canon straight. Outlines, a chapter editor, a World Bible and AI assistance in one place. Free to start.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
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

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#070b09" },
    { media: "(prefers-color-scheme: light)", color: "#f6f4ee" },
  ],
};

// Applies the saved theme before first paint so pages never flash the wrong colors.
const themeScript = `try{var t=localStorage.getItem("mantis-theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={`${inter.variable} ${literata.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}
