export type Area = "Infrastructure" | "Networking" | "Platform" | "Data" | "Other";
export type Level = "Basic" | "Medium" | "High";

export interface Specialization {
  area: Area;
  specialization: string;
  score: number;
  level: Level;
}

export interface AreaScores {
  Infrastructure: number;
  Networking: number;
  Platform: number;
  Data: number;
  Other: number;
}

export interface AnalysisMetrics {
  api_calls: number;
  total_tokens: number;
  avg_api_call_seconds: number;
  model_used: string;
}

export interface AnalysisResult {
  area_scores: AreaScores;
  area_descriptions: Record<Area, string>;
  specializations: Specialization[];
  most_fitted_area: Area;
  best_specializations: Specialization[];
  most_fitted_reason: string;
  education_list: string[];
  soft_skills_list: string[];
  previous_jobs_list: string[];
  candidate_summary: string;
  recommended_role: string;
  recommendation_reason: string;
  metrics: AnalysisMetrics;
  // set by backend
  analysis_id?: string;
  analysis_time_seconds?: number;
  filename?: string;
}

export interface JobStatus {
  job_id: string;
  status: "processing" | "complete" | "failed";
  progress: number;
  current_step: string;
  result?: AnalysisResult;
  error?: string;
}

export interface AnalysisRecord {
  id: string;
  filename: string;
  timestamp: string;
  analysis_time_seconds: number;
  api_calls: number;
  total_tokens: number;
  model_used: string;
  most_fitted_area: Area;
  area_scores: AreaScores;
  candidate_summary: string;
  human_review_minutes: number;
}

export interface AnalysesList {
  total: number;
  items: AnalysisRecord[];
}

export interface Metrics {
  total_analyses: number;
  total_api_calls: number;
  total_tokens: number;
  avg_analysis_time_seconds: number;
  min_analysis_time_seconds: number;
  max_analysis_time_seconds: number;
  total_human_time_saved_minutes: number;
  avg_human_time_saved_minutes: number;
  human_review_minutes_per_cv: number;
  analyses_by_area: Record<Area, number>;
  analyses_by_model: Record<string, number>;
  recent_times: { timestamp: string; analysis_time_seconds: number; api_calls: number }[];
}

export interface BestCandidates {
  best_by_area: Record<
    Area,
    {
      id: string;
      filename: string;
      timestamp: string;
      most_fitted_area: Area;
      area_scores: AreaScores;
      candidate_summary: string;
      best_specializations: Specialization[];
      education_list: string[];
      score_in_area: number;
    } | null
  >;
}

export const AREAS: Area[] = ["Infrastructure", "Networking", "Platform", "Data", "Other"];

export const AREA_COLORS: Record<Area, string> = {
  Infrastructure: "#4285F4",
  Networking: "#34A853",
  Platform: "#FBBC04",
  Data: "#EA4335",
  Other: "#9AA0A6",
};

export const AREA_BG: Record<Area, string> = {
  Infrastructure: "#E8F0FE",
  Networking: "#E6F4EA",
  Platform: "#FEF9E7",
  Data: "#FCE8E6",
  Other: "#F1F3F4",
};

export const LEVEL_COLORS: Record<Level, string> = {
  High: "#34A853",
  Medium: "#FBBC04",
  Basic: "#4285F4",
};

export const LEVEL_BG: Record<Level, string> = {
  High: "#E6F4EA",
  Medium: "#FEF9E7",
  Basic: "#E8F0FE",
};
