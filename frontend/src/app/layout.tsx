import type { Metadata, Viewport } from "next";

import { LiveFeedProvider } from "@/components/layout/LiveFeedProvider";
import { MobileNav } from "@/components/layout/MobileNav";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

import "./globals.css";

export const metadata: Metadata = {
  title: "Biological Minimalism — Mission Control",
  description:
    "AI-driven minimal sensor architecture for autonomous astronaut health monitoring — IAC 2026 research demonstrator.",
};

export const viewport: Viewport = {
  themeColor: "#04070d",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark h-full">
      <body className="flex h-full flex-col bg-space-950 text-slate-200 md:flex-row">
        <LiveFeedProvider>
          <Sidebar />
          <div className="flex min-h-0 flex-1 flex-col">
            <TopBar />
            <MobileNav />
            <main className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6">{children}</main>
          </div>
        </LiveFeedProvider>
      </body>
    </html>
  );
}
