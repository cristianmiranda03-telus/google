import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "CV Review — Google Team",
  description: "AI-powered candidate evaluation for Google Cloud support roles",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#F8F9FA]">
        <Header />
        <main className="pt-16">{children}</main>
      </body>
    </html>
  );
}
