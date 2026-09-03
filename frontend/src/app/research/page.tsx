import type { Metadata } from "next";

import { ResearchMode } from "@/components/research/ResearchMode";

export const metadata: Metadata = {
  title: "Research Mode — Biological Minimalism",
};

export default function ResearchPage() {
  return <ResearchMode />;
}
