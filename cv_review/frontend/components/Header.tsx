"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const path = usePathname();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-[#E8EAED] shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex gap-1">
            {["#4285F4", "#EA4335", "#FBBC04", "#34A853"].map((c, i) => (
              <span
                key={i}
                className="w-2.5 h-2.5 rounded-full transition-transform group-hover:scale-125"
                style={{ backgroundColor: c, transitionDelay: `${i * 30}ms` }}
              />
            ))}
          </div>
          <div>
            <span className="font-extrabold text-[#202124] text-base tracking-tight">CV Review</span>
            <span className="ml-1 text-xs text-[#9AA0A6] font-normal">Google Team</span>
          </div>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          <NavLink href="/" active={path === "/"}>
            Evaluate CV
          </NavLink>
          <NavLink href="/dashboard" active={path === "/dashboard"}>
            Dashboard
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

function NavLink({ href, children, active }: { href: string; children: React.ReactNode; active: boolean }) {
  return (
    <Link
      href={href}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        active
          ? "bg-[#E8F0FE] text-[#4285F4]"
          : "text-[#5F6368] hover:bg-[#F1F3F4] hover:text-[#202124]"
      }`}
    >
      {children}
    </Link>
  );
}
