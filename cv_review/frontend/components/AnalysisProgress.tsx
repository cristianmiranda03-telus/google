"use client";

interface Props {
  progress: number;
  currentStep: string;
  filename: string;
}

const STEPS = [
  { label: "Extracting text", threshold: 5 },
  { label: "Evaluating Infrastructure", threshold: 20 },
  { label: "Evaluating Networking", threshold: 32 },
  { label: "Evaluating Platform", threshold: 44 },
  { label: "Evaluating Data", threshold: 55 },
  { label: "Evaluating Other", threshold: 63 },
  { label: "Area descriptions", threshold: 72 },
  { label: "Extracting profile", threshold: 82 },
  { label: "Generating summary", threshold: 92 },
  { label: "Complete", threshold: 100 },
];

const HUMAN_REVIEW_MINUTES = 45;

export default function AnalysisProgress({ progress, currentStep, filename }: Props) {
  const elapsedPct = Math.max(1, progress);
  const estimatedTotalSec = 120; // rough estimate
  const remainingSec = Math.max(0, Math.round(estimatedTotalSec * (1 - elapsedPct / 100)));

  return (
    <div className="card p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="font-bold text-[#202124] text-lg flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#4285F4] animate-pulse-soft inline-block" />
            Analyzing CV
          </h2>
          <p className="text-sm text-[#5F6368] mt-0.5 truncate max-w-xs">{filename}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-extrabold text-[#4285F4]">{elapsedPct}%</p>
          {remainingSec > 0 && (
            <p className="text-xs text-[#9AA0A6]">~{remainingSec}s left</p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="score-bar mb-2">
        <div
          className="score-bar-fill"
          style={{
            width: `${elapsedPct}%`,
            background: `linear-gradient(90deg, #4285F4 0%, #34A853 ${elapsedPct}%)`,
          }}
        />
      </div>
      <p className="text-sm text-[#5F6368] mb-6">{currentStep}</p>

      {/* Step dots */}
      <div className="flex gap-1 flex-wrap mb-8">
        {STEPS.map((s, i) => (
          <div
            key={i}
            className={`flex-1 min-w-[6px] h-1.5 rounded-full transition-all duration-500 ${
              progress >= s.threshold
                ? "bg-[#34A853]"
                : progress >= STEPS[Math.max(0, i - 1)].threshold
                ? "bg-[#4285F4] animate-pulse-soft"
                : "bg-[#E8EAED]"
            }`}
          />
        ))}
      </div>

      {/* Time savings teaser */}
      <div className="bg-[#E6F4EA] rounded-xl p-4 flex items-center gap-4">
        <div className="text-2xl">⏱️</div>
        <div>
          <p className="text-sm font-semibold text-[#137333]">
            This analysis saves ~{HUMAN_REVIEW_MINUTES} minutes of manual review
          </p>
          <p className="text-xs text-[#34A853] mt-0.5">
            AI evaluates all 13 specializations simultaneously in under 2 minutes
          </p>
        </div>
      </div>
    </div>
  );
}
