"use client";

import { useState, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { uploadCV, uploadCVBatch, evaluateFromUrl, getJobStatus, downloadCandidateReport, downloadCandidatesReport } from "@/lib/api";
import type { AnalysisResult, JobStatus } from "@/lib/types";
import AnalysisProgress from "@/components/AnalysisProgress";
import AnalysisResults from "@/components/AnalysisResults";

const POLL_INTERVAL_MS = 2000;
const MAX_BATCH_FILES = 20;

type InputMode = "file" | "url";

const URL_SOURCES = [
  { label: "LinkedIn", icon: "💼", hint: "linkedin.com/in/username", color: "#0A66C2" },
  { label: "GitHub", icon: "🐙", hint: "github.com/username", color: "#202124" },
  { label: "Portfolio", icon: "🌐", hint: "yoursite.com/resume", color: "#34A853" },
  { label: "PDF Link", icon: "📄", hint: "example.com/cv.pdf", color: "#EA4335" },
  { label: "Any Page", icon: "🔗", hint: "Any public profile or CV page", color: "#9AA0A6" },
];

export default function HomePage() {
  const [mode, setMode] = useState<InputMode>("file");
  const [status, setStatus] = useState<"idle" | "uploading" | "fetching" | "processing" | "complete" | "error">("idle");
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  /** Batch: multiple jobs and results (when multiple files uploaded) */
  const [jobStatuses, setJobStatuses] = useState<JobStatus[]>([]);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [fileNames, setFileNames] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [sourceLabel, setSourceLabel] = useState("");
  const [reportDownloading, setReportDownloading] = useState<"xlsx" | "pdf" | null>(null);
  const urlRef = useRef<HTMLInputElement>(null);

  const getApiErrorMessage = useCallback((err: unknown): string => {
    if (err && typeof err === "object" && "response" in err) {
      const res = (err as { response?: { status?: number; data?: { detail?: string } } }).response;
      const detail = res?.data?.detail;
      if (typeof detail === "string") return detail;
      if (res?.status === 404) return "Job not found. The server may have restarted.";
      if (res?.status && res.status >= 500) return detail || "Server error. Check backend logs.";
    }
    if (err && typeof err === "object" && "message" in err && typeof (err as { message: string }).message === "string")
      return (err as { message: string }).message;
    return "Cannot reach the API. Make sure the backend is running (e.g. http://localhost:8000).";
  }, []);

  // ── Single-job polling ─────────────────────────────────────────────────────
  const pollJob = useCallback((job_id: string) => {
    const poll = async () => {
      try {
        const js = await getJobStatus(job_id);
        setJobStatus(js);
        if (js.status === "complete" && js.result) {
          setResult(js.result);
          setStatus("complete");
        } else if (js.status === "failed") {
          setErrorMsg(js.error || "Analysis failed. Please try again.");
          setStatus("error");
        } else {
          setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (err) {
        setErrorMsg(getApiErrorMessage(err));
        setStatus("error");
      }
    };
    setTimeout(poll, POLL_INTERVAL_MS);
  }, [getApiErrorMessage]);

  // ── Batch polling (multiple jobs) ─────────────────────────────────────────────
  const pollBatch = useCallback((jobIds: string[], names: string[]) => {
    const poll = async () => {
      try {
        const statuses = await Promise.all(jobIds.map((id) => getJobStatus(id)));
        setJobStatuses(statuses);

        const failed = statuses.find((s) => s.status === "failed");
        if (failed) {
          setErrorMsg(failed.error || "One or more analyses failed.");
          setStatus("error");
          return;
        }

        const allComplete = statuses.every((s) => s.status === "complete" && s.result);
        if (allComplete) {
          setResults(statuses.map((s) => s.result!).filter(Boolean));
          setFileNames(names);
          setStatus("complete");
          return;
        }

        setTimeout(poll, POLL_INTERVAL_MS);
      } catch (err) {
        setErrorMsg(getApiErrorMessage(err));
        setStatus("error");
      }
    };
    setTimeout(poll, POLL_INTERVAL_MS);
  }, [getApiErrorMessage]);

  const handleApiError = (err: unknown, fallback: string) => {
    const detail =
      err && typeof err === "object" && "response" in err
        ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback)
        : fallback;
    setErrorMsg(detail);
    setStatus("error");
  };

  // ── File upload (single or batch) ─────────────────────────────────────────────
  const startFileAnalysis = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    setFile(files[0] ?? null);
    setSourceLabel(files.length === 1 ? files[0].name : "");
    setStatus("uploading");
    setErrorMsg("");
    setResult(null);
    setResults([]);
    setJobStatus(null);
    setJobStatuses([]);
    setFileNames([]);
    try {
      const { job_ids } = await uploadCVBatch(files);
      if (job_ids.length === 1) {
        setStatus("processing");
        pollJob(job_ids[0]);
      } else {
        setStatus("processing");
        pollBatch(job_ids, files.map((f) => f.name));
      }
    } catch (err) {
      handleApiError(err, "Upload failed.");
    }
  }, [pollJob, pollBatch]);

  const onDrop = useCallback(
    (accepted: File[]) => { if (accepted.length) startFileAnalysis(accepted); },
    [startFileAnalysis]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: MAX_BATCH_FILES,
    disabled: status === "uploading" || status === "fetching" || status === "processing",
  });

  // ── URL submit ──────────────────────────────────────────────────────────────
  const startUrlAnalysis = useCallback(async () => {
    const url = urlInput.trim();
    if (!url) return;
    setStatus("fetching");
    setErrorMsg("");
    setResult(null);
    setJobStatus(null);
    setFile(null);
    try {
      const { job_id, source_label } = await evaluateFromUrl(url);
      setSourceLabel(source_label);
      setStatus("processing");
      pollJob(job_id);
    } catch (err) {
      handleApiError(err, "Failed to fetch URL.");
    }
  }, [urlInput, pollJob]);

  const reset = () => {
    setStatus("idle");
    setJobStatus(null);
    setResult(null);
    setJobStatuses([]);
    setResults([]);
    setFileNames([]);
    setErrorMsg("");
    setFile(null);
    setUrlInput("");
    setSourceLabel("");
  };

  const batchProgress = jobStatuses.length
    ? Math.round(jobStatuses.reduce((a, s) => a + s.progress, 0) / jobStatuses.length)
    : 0;
  const batchStep =
    jobStatuses.length && jobStatuses[0]
      ? jobStatuses[0].current_step
      : "Starting…";
  const batchCount = Math.max(jobStatuses.length, fileNames.length, results.length);
  const displayResult = result ?? (results.length === 1 ? results[0] : null);
  const displaySourceLabel = sourceLabel || (fileNames.length === 1 ? fileNames[0] : "");

  const isActive = status === "uploading" || status === "fetching" || status === "processing";

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      {/* Hero */}
      <div className="text-center mb-10 animate-fade-in">
        <div className="flex justify-center gap-2 mb-4">
          {["#4285F4", "#EA4335", "#FBBC04", "#34A853"].map((c, i) => (
            <span key={i} className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: c }} />
          ))}
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight mb-3">
          <span className="gradient-text">CV Review</span>
          <span className="text-[#202124]"> — Google Team</span>
        </h1>
        <p className="text-[#5F6368] text-lg max-w-2xl mx-auto">
          AI-powered evaluation against Infrastructure, Networking, Platform, Data, and specialized
          roles. Upload one or multiple files, or paste any public profile URL.
        </p>
        <div className="flex justify-center gap-6 mt-5 text-sm text-[#5F6368] flex-wrap">
          <span className="flex items-center gap-1"><span className="text-[#34A853]">✓</span> 13 specializations</span>
          <span className="flex items-center gap-1"><span className="text-[#4285F4]">✓</span> Multi-file batch analysis</span>
          <span className="flex items-center gap-1"><span className="text-[#FBBC04]">✓</span> Time savings metrics</span>
          <span className="flex items-center gap-1"><span className="text-[#EA4335]">✓</span> Dashboard history</span>
        </div>
      </div>

      {/* Input panel */}
      {(status === "idle" || status === "error") && (
        <div className="animate-slide-up">
          {/* Tab switcher */}
          <div className="flex gap-1 mb-4 bg-[#F1F3F4] rounded-xl p-1 max-w-xs mx-auto">
            <button
              onClick={() => setMode("file")}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-semibold transition-all ${
                mode === "file"
                  ? "bg-white text-[#4285F4] shadow-sm"
                  : "text-[#5F6368] hover:text-[#202124]"
              }`}
            >
              📄 Upload File
            </button>
            <button
              onClick={() => { setMode("url"); setTimeout(() => urlRef.current?.focus(), 50); }}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-semibold transition-all ${
                mode === "url"
                  ? "bg-white text-[#4285F4] shadow-sm"
                  : "text-[#5F6368] hover:text-[#202124]"
              }`}
            >
              🔗 Paste URL
            </button>
          </div>

          {/* FILE mode */}
          {mode === "file" && (
            <div
              {...getRootProps()}
              className={`relative card p-12 text-center cursor-pointer border-2 border-dashed transition-all duration-200 ${
                isDragActive
                  ? "border-[#4285F4] bg-[#E8F0FE]"
                  : "border-[#DADCE0] hover:border-[#4285F4] hover:bg-[#F8F9FF]"
              }`}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-[#E8F0FE] flex items-center justify-center text-3xl">
                  📄
                </div>
                {isDragActive ? (
                  <p className="text-xl font-semibold text-[#4285F4]">Drop it here!</p>
                ) : (
                  <>
                    <div>
                      <p className="text-xl font-semibold text-[#202124]">Drag & drop one or more CVs here</p>
                      <p className="text-[#5F6368] mt-1">
                        or <span className="text-[#4285F4] font-medium">browse files</span> · analyze up to {MAX_BATCH_FILES} at once
                      </p>
                    </div>
                    <p className="text-sm text-[#9AA0A6]">PDF, TXT, or DOCX · Max 20 files · 10 MB each</p>
                  </>
                )}
              </div>
            </div>
          )}

          {/* URL mode */}
          {mode === "url" && (
            <div className="card p-8">
              {/* Supported sources */}
              <div className="flex flex-wrap justify-center gap-3 mb-6">
                {URL_SOURCES.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => {
                      if (s.hint && !s.hint.includes(" ")) {
                        setUrlInput("https://" + s.hint.split("/")[0] + "/");
                        urlRef.current?.focus();
                      }
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#E8EAED] text-sm font-medium hover:border-[#4285F4] hover:bg-[#F8F9FF] transition-colors"
                    style={{ color: s.color }}
                  >
                    <span>{s.icon}</span>
                    <span>{s.label}</span>
                  </button>
                ))}
              </div>

              {/* URL input */}
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9AA0A6] text-sm">🔗</span>
                  <input
                    ref={urlRef}
                    type="url"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && startUrlAnalysis()}
                    placeholder="https://linkedin.com/in/username  or  https://mysite.com/cv"
                    className="w-full pl-9 pr-4 py-3 rounded-xl border border-[#DADCE0] text-sm focus:outline-none focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20 transition-all"
                    disabled={isActive}
                  />
                </div>
                <button
                  onClick={startUrlAnalysis}
                  disabled={!urlInput.trim() || isActive}
                  className="px-6 py-3 bg-[#4285F4] text-white rounded-xl font-semibold text-sm hover:bg-[#3367D6] disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm whitespace-nowrap"
                >
                  Analyze
                </button>
              </div>

              {/* Hints */}
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
                {URL_SOURCES.slice(0, 4).map((s) => (
                  <div
                    key={s.label}
                    className="flex items-start gap-2 p-3 rounded-lg bg-[#F8F9FA] border border-[#E8EAED]"
                  >
                    <span className="text-lg">{s.icon}</span>
                    <div>
                      <p className="text-xs font-semibold text-[#202124]">{s.label}</p>
                      <p className="text-xs text-[#9AA0A6] font-mono">{s.hint}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* LinkedIn note */}
              <div className="mt-4 p-3 bg-[#FEF9E7] border border-[#FBBC04]/30 rounded-xl flex gap-2 text-xs text-[#B06000]">
                <span>⚠️</span>
                <span>
                  <strong>LinkedIn note:</strong> Public profiles work for basic info.
                  For the full profile, use <strong>LinkedIn → More → Save to PDF</strong> and upload the file.
                </span>
              </div>
            </div>
          )}

          {/* Error */}
          {status === "error" && (
            <div className="mt-4 p-4 bg-[#FCE8E6] rounded-xl border border-[#EA4335]/20 text-[#C5221F] flex items-start gap-3">
              <span className="text-xl shrink-0">⚠️</span>
              <div className="flex-1">
                <p className="font-semibold">Analysis failed</p>
                <p className="text-sm mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Uploading / fetching spinner */}
      {(status === "uploading" || status === "fetching") && (
        <div className="card p-10 text-center animate-fade-in">
          <div className="w-12 h-12 border-4 border-[#4285F4] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-semibold text-[#202124]">
            {status === "fetching" ? "Fetching profile from URL…" : `Uploading ${file?.name}…`}
          </p>
          <p className="text-sm text-[#9AA0A6] mt-1">
            {status === "fetching" ? "Extracting text from the page" : "Preparing file for analysis"}
          </p>
        </div>
      )}

      {/* Analysis progress (single or batch) */}
      {status === "processing" && (jobStatus || jobStatuses.length > 0) && (
        <AnalysisProgress
          progress={jobStatus ? jobStatus.progress : batchProgress}
          currentStep={jobStatus ? jobStatus.current_step : batchStep}
          filename={
            jobStatus
              ? sourceLabel || file?.name || ""
              : `Analyzing ${batchCount} CV${batchCount > 1 ? "s" : ""}…`
          }
        />
      )}

      {/* Results (single or multiple) */}
      {status === "complete" && (displayResult || results.length > 0) && (
        <div className="animate-slide-up">
          <div className="flex justify-between items-center mb-6 flex-wrap gap-3">
            <div>
              <h2 className="text-xl font-bold text-[#202124]">
                Analysis complete <span className="text-[#34A853]">✓</span>
                {results.length > 1 && (
                  <span className="text-base font-normal text-[#5F6368] ml-2">
                    {results.length} CVs
                  </span>
                )}
              </h2>
              {displaySourceLabel && results.length <= 1 && (
                <p className="text-sm text-[#9AA0A6] mt-0.5">Source: {displaySourceLabel}</p>
              )}
            </div>
            <div className="flex gap-2 flex-wrap items-center">
              {results.length > 1 ? (
                <>
                  <button
                    onClick={() => {
                      const ids = results.map((r) => r.analysis_id).filter(Boolean) as string[];
                      if (!ids.length) return;
                      setReportDownloading("xlsx");
                      downloadCandidatesReport({ format: "xlsx", ids }).catch((err) => setErrorMsg(err instanceof Error ? err.message : "Download failed.")).finally(() => setReportDownloading(null));
                    }}
                    disabled={!!reportDownloading || !results.some((r) => r.analysis_id)}
                    className="px-3 py-1.5 rounded-lg border border-[#DADCE0] text-sm font-medium hover:bg-[#F8F9FA] disabled:opacity-60"
                  >
                    {reportDownloading === "xlsx" ? "…" : "📊"} Download Excel
                  </button>
                  <button
                    onClick={() => {
                      const ids = results.map((r) => r.analysis_id).filter(Boolean) as string[];
                      if (!ids.length) return;
                      setReportDownloading("pdf");
                      downloadCandidatesReport({ format: "pdf", ids }).catch((err) => setErrorMsg(err instanceof Error ? err.message : "Download failed.")).finally(() => setReportDownloading(null));
                    }}
                    disabled={!!reportDownloading || !results.some((r) => r.analysis_id)}
                    className="px-3 py-1.5 rounded-lg border border-[#DADCE0] text-sm font-medium hover:bg-[#F8F9FA] disabled:opacity-60"
                  >
                    {reportDownloading === "pdf" ? "…" : "📄"} Download PDF
                  </button>
                </>
              ) : (
                displayResult?.analysis_id && (
                  <>
                    <button
                      onClick={() => {
                        setReportDownloading("xlsx");
                        downloadCandidateReport(displayResult.analysis_id!, "xlsx").catch((err) => setErrorMsg(err instanceof Error ? err.message : "Download failed.")).finally(() => setReportDownloading(null));
                      }}
                      disabled={!!reportDownloading}
                      className="px-3 py-1.5 rounded-lg border border-[#DADCE0] text-sm font-medium hover:bg-[#F8F9FA] disabled:opacity-60"
                    >
                      {reportDownloading === "xlsx" ? "…" : "📊"} Excel
                    </button>
                    <button
                      onClick={() => {
                        setReportDownloading("pdf");
                        downloadCandidateReport(displayResult.analysis_id!, "pdf").catch((err) => setErrorMsg(err instanceof Error ? err.message : "Download failed.")).finally(() => setReportDownloading(null));
                      }}
                      disabled={!!reportDownloading}
                      className="px-3 py-1.5 rounded-lg border border-[#DADCE0] text-sm font-medium hover:bg-[#F8F9FA] disabled:opacity-60"
                    >
                      {reportDownloading === "pdf" ? "…" : "📄"} PDF
                    </button>
                  </>
                )
              )}
              <button
                onClick={reset}
                className="px-4 py-2 rounded-lg border border-[#DADCE0] text-[#5F6368] text-sm font-medium hover:bg-white hover:border-[#4285F4] hover:text-[#4285F4] transition-colors"
              >
                ↩ Analyze another
              </button>
            </div>
          </div>
          {results.length > 1 ? (
            <div className="space-y-8">
              {results.map((res, idx) => (
                <div key={idx} className="border border-[#E8EAED] rounded-xl overflow-hidden">
                  <div className="bg-[#F8F9FA] px-4 py-2 border-b border-[#E8EAED]">
                    <p className="text-sm font-semibold text-[#202124]">
                      {(res.filename ?? fileNames[idx]) || `CV ${idx + 1}`}
                    </p>
                  </div>
                  <div className="p-4">
                    <AnalysisResults result={res} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            displayResult && <AnalysisResults result={displayResult} />
          )}
        </div>
      )}
    </div>
  );
}
