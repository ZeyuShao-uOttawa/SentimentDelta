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
    href: "/dashboard/stock-prices",
    label: "Stock Prices",
    icon: "stock-line",
  },
  {
    href: "/dashboard/news",
    label: "News",
    icon: "newspaper-line",
  },
  {
    href: "/dashboard/aggregates",
    label: "Aggregates",
    icon: "bar-chart-line",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { tickers, currentTicker, setCurrentTicker } = useApplicationContext();

  return (
    <aside className="w-64 min-h-screen border-r bg-white/60 dark:bg-slate-900/60 sticky top-0">
      <div className="p-4 flex items-center gap-2">
        <div className="text-xl font-bold">Sentiment</div>
      </div>

      {tickers.length > 0 && currentTicker && (
        <div className="p-4">
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
            <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              <p>
                Start:{" "}
                {
                  tickers.find((ticker) => ticker.Ticker === currentTicker)
                    ?.start
                }
              </p>
              <p>
                End:{" "}
                {tickers.find((ticker) => ticker.Ticker === currentTicker)?.end}
              </p>
            </div>
          )}
        </div>
      )}

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
