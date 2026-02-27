"use client";

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { Area } from "@/lib/types";
import { AREA_COLORS } from "@/lib/types";

interface Props {
  data: Record<string, number>;
}

export default function AreaDistributionChart({ data }: Props) {
  const chartData = Object.entries(data)
    .map(([name, value]) => ({ name, value }))
    .filter((d) => d.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-[#9AA0A6] text-sm">
        No data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((entry) => (
            <Cell
              key={entry.name}
              fill={AREA_COLORS[entry.name as Area] ?? "#9AA0A6"}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [`${value} CV${value !== 1 ? "s" : ""}`, ""]}
          contentStyle={{ borderRadius: "8px", border: "1px solid #E8EAED", fontSize: "12px" }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => <span style={{ fontSize: "12px", color: "#5F6368" }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
