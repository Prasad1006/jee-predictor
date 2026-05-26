"use client";

import dynamic from "next/dynamic";

const CounsellingWorkspace = dynamic(
  () => import("@/components/CounsellingWorkspace").then((mod) => mod.CounsellingWorkspace),
  { ssr: false }
);

export default function HomePage() {
  return <CounsellingWorkspace />;
}

