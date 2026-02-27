"use client";

import type { AnalysisResult, Area } from "@/lib/types";
import { AREAS, AREA_COLORS, AREA_BG, LEVEL_COLORS, LEVEL_BG } from "@/lib/types";

interface Props {
  result: AnalysisResult;
}

const HUMAN_REVIEW_MINUTES = 45;

export default function AnalysisResults({ result }: Props) {
  const aTime = result.analysis_time_seconds ?? result.metrics?.avg_api_call_seconds;
  const aiMinutes = aTime ? aTime / 60 : null;
  const savedMinutes = aiMinutes ? Math.max(0, HUMAN_REVIEW_MINUTES - aiMinutes) : HUMAN_REVIEW_MINUTES - 2;

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Best fit hero */}
      <div
        className="card p-6 relative overflow-hidden"
        style={{ borderLeft: `5px solid ${AREA_COLORS[result.most_fitted_area as Area] ?? "#4285F4"}` }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[#5F6368] mb-1 flex items-center gap-1">
              🎯 Best-fit area
            </p>
            <h2
              className="text-3xl font-extrabold"
              style={{ color: AREA_COLORS[result.most_fitted_area as Area] ?? "#4285F4" }}
            >
              {result.most_fitted_area}
            </h2>
            {/* Specialization pills */}
            {result.best_specializations.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {result.best_specializations.slice(0, 4).map((s, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 rounded-full text-xs font-semibold border"
                    style={{
                      backgroundColor: LEVEL_BG[s.level],
                      color: LEVEL_COLORS[s.level],
                      borderColor: LEVEL_COLORS[s.level] + "40",
                    }}
                  >
                    {s.specialization} · {s.score}/5 · {s.level}
                  </span>
                ))}
              </div>
            )}
            {result.most_fitted_reason && (
              <p className="text-sm text-[#5F6368] mt-3 leading-relaxed border-t border-[#E8EAED] pt-3">
                {result.most_fitted_reason}
              </p>
            )}
          </div>
          {/* Recommended role badge */}
          <div
            className="rounded-xl p-4 text-center min-w-[140px]"
            style={{ backgroundColor: AREA_BG[result.most_fitted_area as Area] ?? "#E8F0FE" }}
          >
            <p className="text-xs font-medium text-[#5F6368] mb-1">Recommended Role</p>
            <p
              className="text-sm font-bold leading-tight"
              style={{ color: AREA_COLORS[result.most_fitted_area as Area] ?? "#4285F4" }}
            >
              {result.recommended_role}
            </p>
          </div>
        </div>
      </div>

      {/* Area scores */}
      <div className="card p-6">
        <h3 className="font-bold text-[#202124] mb-4">📊 Score per Area (1–5)</h3>
        <div className="space-y-3">
          {AREAS.map((area) => {
            const score = result.area_scores?.[area] ?? 1;
            const pct = ((score - 1) / 4) * 100;
            const isBest = area === result.most_fitted_area;
            return (
              <div key={area} className={`flex items-center gap-4 p-2.5 rounded-lg ${isBest ? "bg-[#F8F9FA]" : ""}`}>
                <div className="w-28 shrink-0 flex items-center gap-1.5">
                  {isBest && <span className="text-xs">🏆</span>}
                  <span className="text-sm font-medium text-[#202124] truncate">{area}</span>
                </div>
                <div className="flex-1 score-bar">
                  <div
                    className="score-bar-fill"
                    style={{ width: `${pct}%`, backgroundColor: AREA_COLORS[area] }}
                  />
                </div>
                <div className="w-16 text-right">
                  <span
                    className="text-sm font-bold"
                    style={{ color: AREA_COLORS[area] }}
                  >
                    {score.toFixed(1)}
                  </span>
                  <span className="text-xs text-[#9AA0A6]">/5</span>
                </div>
                <div className="w-16 text-right">
                  <span
                    className="badge text-xs"
                    style={{
                      backgroundColor: score >= 4 ? "#E6F4EA" : score >= 3 ? "#FEF9E7" : "#E8F0FE",
                      color: score >= 4 ? "#137333" : score >= 3 ? "#B06000" : "#1967D2",
                    }}
                  >
                    {score >= 4 ? "High" : score >= 3 ? "Medium" : "Basic"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Candidate summary + profile */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Summary */}
        <div className="card p-6">
          <h3 className="font-bold text-[#202124] mb-3">📝 Candidate Summary</h3>
          <p className="text-sm text-[#3C4043] leading-relaxed">{result.candidate_summary}</p>
        </div>

        {/* Profile */}
        <div className="space-y-4">
          {result.education_list?.length > 0 && (
            <div className="card p-5 border-l-4 border-[#34A853]">
              <h4 className="font-semibold text-[#202124] mb-2 text-sm">🎓 Education & Certifications</h4>
              <ul className="space-y-1">
                {result.education_list.slice(0, 5).map((e, i) => (
                  <li key={i} className="text-sm text-[#5F6368] flex items-start gap-1.5">
                    <span className="text-[#34A853] mt-0.5">·</span>
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.soft_skills_list?.length > 0 && (
            <div className="card p-5 border-l-4 border-[#4285F4]">
              <h4 className="font-semibold text-[#202124] mb-2 text-sm">💬 Soft Skills</h4>
              <div className="flex flex-wrap gap-1.5">
                {result.soft_skills_list.slice(0, 8).map((s, i) => (
                  <span key={i} className="px-2.5 py-0.5 bg-[#E8F0FE] text-[#1967D2] rounded-full text-xs font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Previous jobs */}
      {result.previous_jobs_list?.length > 0 && (
        <div className="card p-6">
          <h3 className="font-bold text-[#202124] mb-3">💼 Previous Experience</h3>
          <div className="space-y-2">
            {result.previous_jobs_list.slice(0, 8).map((job, i) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-[#F1F3F4] last:border-0">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5"
                  style={{ backgroundColor: ["#4285F4", "#EA4335", "#FBBC04", "#34A853"][i % 4] }}
                >
                  {i + 1}
                </div>
                <p className="text-sm text-[#3C4043]">{job}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Specializations grid */}
      <div className="card p-6">
        <h3 className="font-bold text-[#202124] mb-4">🔬 All Specializations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {AREAS.map((area) => {
            const specs = result.specializations?.filter((s) => s.area === area) ?? [];
            if (specs.length === 0) return null;
            return (
              <div key={area} className="rounded-xl border border-[#E8EAED] p-4">
                <div
                  className="text-xs font-bold uppercase tracking-wider mb-3 px-2 py-0.5 rounded inline-block"
                  style={{ color: AREA_COLORS[area], backgroundColor: AREA_BG[area] }}
                >
                  {area}
                </div>
                <div className="space-y-2">
                  {specs.map((s, i) => (
                    <div key={i} className="flex items-center justify-between gap-2">
                      <span className="text-sm text-[#3C4043] truncate">{s.specialization}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <div className="flex gap-0.5">
                          {[1, 2, 3, 4, 5].map((dot) => (
                            <span
                              key={dot}
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor: dot <= s.score ? AREA_COLORS[area] : "#E8EAED",
                              }}
                            />
                          ))}
                        </div>
                        <span
                          className="badge"
                          style={{
                            fontSize: "10px",
                            padding: "1px 6px",
                            backgroundColor: LEVEL_BG[s.level],
                            color: LEVEL_COLORS[s.level],
                          }}
                        >
                          {s.level}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Area descriptions */}
      {result.area_descriptions && (
        <div className="card p-6">
          <h3 className="font-bold text-[#202124] mb-4">📋 Area Insights</h3>
          <div className="space-y-3">
            {AREAS.map((area) => {
              const desc = result.area_descriptions?.[area];
              if (!desc) return null;
              const score = result.area_scores?.[area] ?? 1;
              return (
                <div
                  key={area}
                  className="rounded-xl p-4 border"
                  style={{
                    backgroundColor: AREA_BG[area],
                    borderColor: AREA_COLORS[area] + "30",
                  }}
                >
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="font-semibold text-sm" style={{ color: AREA_COLORS[area] }}>
                      {area}
                    </span>
                    <span className="text-xs font-bold" style={{ color: AREA_COLORS[area] }}>
                      {score.toFixed(1)}/5
                    </span>
                  </div>
                  <p className="text-sm text-[#3C4043] leading-relaxed">{desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Metrics panel */}
      <div className="card p-6 bg-[#F8F9FA] border-t-4 border-[#4285F4]">
        <h3 className="font-bold text-[#202124] mb-4">⚡ Analysis Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-extrabold text-[#34A853]">
              {aTime ? `${Math.round(aTime)}s` : "~2min"}
            </p>
            <p className="text-xs text-[#5F6368] mt-1">AI Analysis Time</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-extrabold text-[#EA4335]">{HUMAN_REVIEW_MINUTES}m</p>
            <p className="text-xs text-[#5F6368] mt-1">Human Review Est.</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-extrabold text-[#4285F4]">
              {result.metrics?.api_calls ?? "~16"}
            </p>
            <p className="text-xs text-[#5F6368] mt-1">API Calls Made</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-extrabold text-[#FBBC04]">
              {savedMinutes.toFixed(0)}m
            </p>
            <p className="text-xs text-[#5F6368] mt-1">Time Saved</p>
          </div>
        </div>
        {result.metrics?.model_used && (
          <p className="text-center mt-3 text-xs text-[#9AA0A6]">
            Model: <span className="font-medium text-[#5F6368]">{result.metrics.model_used}</span>
            {result.metrics.total_tokens > 0 && ` · ${result.metrics.total_tokens.toLocaleString()} tokens`}
          </p>
        )}
      </div>
    </div>
  );
}
