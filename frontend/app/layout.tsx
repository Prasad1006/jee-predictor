import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JoSAA Copilot — AI Counselling",
  description: "Predict colleges and get AI counselling for JoSAA admissions",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#2563eb",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
      </head>
      <body className="antialiased bg-[#060609] text-slate-100 h-full w-full overflow-hidden select-none">
        <main className="h-full w-full">{children}</main>
      </body>
    </html>
  );
}
