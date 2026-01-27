"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/icons";

const navItems = [
  {
    href: "/dashboard/aggregates",
    label: "Aggregates",
    icon: "bar-chart-line",
  },
  { href: "/dashboard/news", label: "News", icon: "newspaper-line" },
  {
    href: "/dashboard/stock-prices",
    label: "Stock Prices",
    icon: "stock-line",
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-screen border-r bg-white/60 dark:bg-slate-900/60 sticky top-0">
      <div className="p-4 flex items-center gap-2">
        <div className="text-xl font-bold">Sentiment</div>
      </div>

      <nav className="px-2 py-4 space-y-1">
        {navItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm ${
                active
                  ? "bg-slate-100 dark:bg-slate-800 font-semibold"
                  : "hover:bg-slate-50 dark:hover:bg-slate-900"
              }`}
            >
              <Icon iconName={item.icon} iconSize="sm" className="shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
