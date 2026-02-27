import AnalysisDetailClient from "./AnalysisDetailClient";

/** Required for "output: export" — no paths pre-rendered; client handles /analysis/[id] at runtime. */
export function generateStaticParams() {
  return [];
}

export default function AnalysisDetailPage() {
  return <AnalysisDetailClient />;
}
