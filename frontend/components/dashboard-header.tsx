"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";

function titleFromPath(pathname: string | null) {
  if (!pathname) return "Dashboard";
  if (pathname.includes("aggregates")) return "Aggregates";
  if (pathname.includes("news")) return "News";
  if (pathname.includes("stock-prices")) return "Stock Prices";
  return "Dashboard";
}

export default function DashboardHeader() {
  const pathname = usePathname();
  const title = titleFromPath(pathname);

  return (
    <header className="flex items-center justify-between mb-6">
      <div>
        <h2 className="text-2xl font-semibold">{title}</h2>
        <p className="text-sm text-muted-foreground">
          Overview and quick stats
        </p>
      </div>

      <div className="flex items-center gap-3">
        <ThemeToggle />
      </div>
    </header>
  );
}
