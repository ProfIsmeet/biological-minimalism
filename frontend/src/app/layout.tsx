import type { Metadata, Viewport } from "next";

import { AppHeader } from "@/components/layout/AppHeader";
import { LiveFeedProvider } from "@/components/layout/LiveFeedProvider";
import { MobileNav } from "@/components/layout/MobileNav";
import { Sidebar } from "@/components/layout/Sidebar";

import "./globals.css";

export const metadata: Metadata = {
  title: "Biological Minimalism — Final Sensing Architecture",
  description:
    "Jury-facing demonstration of the CORE_PLUS_CONTEXT physiological sensing architecture and its fault-aware evidence layer.",
};

export const viewport: Viewport = {
  themeColor: "#0B0F12",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark h-full">
      <body className="flex h-full flex-col bg-canvas text-ink-primary md:flex-row">
        <LiveFeedProvider>
          <Sidebar />
          <div className="flex min-h-0 flex-1 flex-col">
            <AppHeader />
            <MobileNav />
            <main className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6">{children}</main>
          </div>
        </LiveFeedProvider>
      </body>
    </html>
  );
}
