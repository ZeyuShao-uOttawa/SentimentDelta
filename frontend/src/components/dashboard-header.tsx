"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./theme-toggle";
import { useApplicationContext } from "@/context/application-context";

const PAGE_TITLES: Record<string, string> = {
  "/": "Aggregates",
  news: "News",
  "stock-prices": "Stock Prices",
};

function titleFromPath(pathname: string | null) {
  if (!pathname || pathname === "/") return "Aggregates";
  const segment = pathname.split("/").filter(Boolean).pop();
  return (segment && PAGE_TITLES[segment]) || "Dashboard";
}

export default function DashboardHeader() {
  const pathname = usePathname();
  const title = titleFromPath(pathname);
  const { currentTicker } = useApplicationContext();

  return (
    <header className="flex items-center justify-between mb-6">
      <div>
        <h2 className="text-2xl font-semibold">
          {currentTicker ? `${title} - ${currentTicker}` : title}
        </h2>
        <p className="text-sm text-muted-foreground">
          Real-time financial sentiment analysis for{" "}
          {currentTicker || "selected ticker"}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <ThemeToggle />
      </div>
    </header>
  );
}
