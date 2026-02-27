interface Props {
  icon: string;
  label: string;
  value: string;
  subtitle?: string;
  color: string;
  bg: string;
}

export default function MetricCard({ icon, label, value, subtitle, color, bg }: Props) {
  return (
    <div className="card p-5 card-hover transition-all duration-200">
      <div className="flex items-start justify-between mb-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
          style={{ backgroundColor: bg }}
        >
          {icon}
        </div>
      </div>
      <p className="text-2xl font-extrabold" style={{ color }}>
        {value}
      </p>
      <p className="text-sm font-medium text-[#202124] mt-0.5">{label}</p>
      {subtitle && <p className="text-xs text-[#9AA0A6] mt-0.5">{subtitle}</p>}
    </div>
  );
}
