import axios from "axios";
import type { AnalysesList, AnalysisRecord, BestCandidates, JobStatus, Metrics } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE });

export async function uploadCV(file: File): Promise<{ job_id: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<{ job_id: string }>("/api/evaluate", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function uploadCVBatch(files: File[]): Promise<{ job_ids: string[] }> {
  if (files.length === 0) return { job_ids: [] };
  if (files.length === 1) {
    const { job_id } = await uploadCV(files[0]);
    return { job_ids: [job_id] };
  }
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await api.post<{ job_ids: string[] }>("/api/evaluate-batch", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function evaluateFromUrl(
  url: string
): Promise<{ job_id: string; source_label: string; chars_extracted: number }> {
  const res = await api.post("/api/evaluate-url", { url });
  return res.data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await api.get<JobStatus>(`/api/jobs/${jobId}`);
  return res.data;
}

export async function listAnalyses(limit = 50, offset = 0): Promise<AnalysesList> {
  const res = await api.get<AnalysesList>("/api/analyses", { params: { limit, offset } });
  return res.data;
}

export async function getAnalysis(id: string): Promise<AnalysisRecord & { result: import("./types").AnalysisResult }> {
  const res = await api.get(`/api/analyses/${id}`);
  return res.data;
}

export async function deleteAnalysis(id: string): Promise<void> {
  await api.delete(`/api/analyses/${id}`);
}

export async function getMetrics(): Promise<Metrics> {
  const res = await api.get<Metrics>("/api/metrics");
  return res.data;
}

export async function getBestCandidates(): Promise<BestCandidates> {
  const res = await api.get<BestCandidates>("/api/best-candidates");
  return res.data;
}

async function getReportErrorDetail(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text);
    return (j.detail ?? text) || "Download failed.";
  } catch {
    return text || "Download failed.";
  }
}

/** Trigger download of high-level report for one candidate (Excel or PDF). */
export async function downloadCandidateReport(
  analysisId: string,
  format: "xlsx" | "pdf"
): Promise<void> {
  const url = `${API_BASE}/api/reports/candidate/${analysisId}?format=${format}`;
  const res = await fetch(url);
  if (!res.ok) {
    const msg = await getReportErrorDetail(res);
    throw new Error(msg);
  }
  const blob = await res.blob();
  const disp = res.headers.get("Content-Disposition");
  const match = disp && disp.match(/filename="?([^";]+)"?/);
  const filename = match ? match[1] : `candidate-report.${format === "xlsx" ? "xlsx" : "pdf"}`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

/** Trigger download of high-level report for multiple candidates (optional filter by area, ids, or date range). */
export async function downloadCandidatesReport(params: {
  format: "xlsx" | "pdf";
  ids?: string[];
  area?: string;
  dateFrom?: string;
  dateTo?: string;
}): Promise<void> {
  const search = new URLSearchParams();
  search.set("format", params.format);
  if (params.ids?.length) search.set("ids", params.ids.join(","));
  if (params.area) search.set("area", params.area);
  if (params.dateFrom) search.set("date_from", params.dateFrom);
  if (params.dateTo) search.set("date_to", params.dateTo);
  const url = `${API_BASE}/api/reports/candidates?${search.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    const msg = await getReportErrorDetail(res);
    throw new Error(msg);
  }
  const blob = await res.blob();
  const disp = res.headers.get("Content-Disposition");
  const match = disp && disp.match(/filename="?([^";]+)"?/);
  const filename = match ? match[1] : `candidate-reports.${params.format === "xlsx" ? "xlsx" : "pdf"}`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
