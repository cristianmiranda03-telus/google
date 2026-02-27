"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface Props {
  data: { timestamp: string; analysis_time_seconds: number; api_calls: number }[];
}

export default function AITimeChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-[#9AA0A6] text-sm">
        No data yet
      </div>
    );
  }

  const formatted = data.map((d, i) => ({
    idx: i + 1,
    time: d.analysis_time_seconds,
    calls: d.api_calls,
    date: new Date(d.timestamp).toLocaleDateString("en", { month: "short", day: "numeric" }),
  }));

  const avg =
    formatted.reduce((s, d) => s + d.time, 0) / formatted.length;

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={formatted} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F1F3F4" />
        <XAxis
          dataKey="idx"
          tick={{ fontSize: 10, fill: "#9AA0A6" }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#9AA0A6" }}
          tickLine={false}
          axisLine={false}
          unit="s"
        />
        <Tooltip
          formatter={(v: number) => [`${v.toFixed(1)}s`, "AI Time"]}
          labelFormatter={(l) => `Analysis #${l}`}
          contentStyle={{ borderRadius: "8px", border: "1px solid #E8EAED", fontSize: "12px" }}
        />
        <ReferenceLine
          y={avg}
          stroke="#FBBC04"
          strokeDasharray="4 4"
          label={{ value: `avg ${avg.toFixed(0)}s`, fontSize: 10, fill: "#B06000", position: "right" }}
        />
        <Line
          type="monotone"
          dataKey="time"
          stroke="#4285F4"
          strokeWidth={2}
          dot={{ fill: "#4285F4", r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
