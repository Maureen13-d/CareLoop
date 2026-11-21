import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Self-hosted (SIL Open Font License, see fonts/OFL.txt) so the build and the
// running app never depend on a Google Fonts request.
const outfit = localFont({
  src: "./fonts/Outfit-Variable.woff2",
  weight: "100 900",
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "CareLoop", template: "%s · CareLoop" },
  description: "Patient navigation from a concerning screening finding to a real visit. Synthetic demo.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${outfit.variable} h-full`}>
      <body className="min-h-full bg-canvas text-ink antialiased">{children}</body>
    </html>
  );
}
