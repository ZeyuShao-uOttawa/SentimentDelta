"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/icons";
import { useApplicationContext } from "@/context/application-context";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const navItems = [
  {
    href: "/stock-prices",
    label: "Stock Prices",
    icon: "stock-line",
  },
  {
    href: "/news",
    label: "News",
    icon: "newspaper-line",
  },
  {
    href: "/",
    label: "Aggregates",
    icon: "bar-chart-line",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { tickers, currentTicker, setCurrentTicker } = useApplicationContext();

  return (
    <aside className="w-64 min-h-screen border-r bg-white/60 dark:bg-slate-900/60 sticky top-0">
      <div className="p-4 flex items-center gap-2 border-b mb-4">
        <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-white font-bold">
          S
        </div>
        <div className="text-xl font-bold tracking-tight">Delta</div>
      </div>

      <div className="p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Market Selection
        </h3>
        {tickers.length > 0 ? (
          <>
            <Select
              onValueChange={(value) => setCurrentTicker(value)}
              value={currentTicker || ""}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a Ticker" />
              </SelectTrigger>
              <SelectContent>
                {tickers.map((ticker) => (
                  <SelectItem key={ticker.Ticker} value={ticker.Ticker}>
                    {ticker.Ticker}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {currentTicker && (
              <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Start:</span>
                  <span className="font-medium">
                    {tickers.find((t) => t.Ticker === currentTicker)?.start}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">End:</span>
                  <span className="font-medium">
                    {tickers.find((t) => t.Ticker === currentTicker)?.end}
                  </span>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="space-y-2">
            <div className="h-9 w-full bg-slate-100 dark:bg-slate-800 animate-pulse rounded" />
            <p className="text-[10px] text-muted-foreground text-center">
              Loading markets...
            </p>
          </div>
        )}
      </div>

      <nav className="px-2 py-4 space-y-1">
        <h3 className="px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Navigation
        </h3>
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
