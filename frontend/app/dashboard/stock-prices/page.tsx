"use client";

import React, { useEffect, useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useApplicationContext } from "@/context/application-context";
import LineChartCard from "@/components/charts/LineChartCard";
import { Icon } from "@/components/icons";
import { StockPrice } from "@/api/types";
import { cn } from "@/lib/utils";
import CandleChartCard from "@/components/charts/CandleChartCard";

export default function StockPricesPage() {
  const [data, setData] = useState<StockPrice[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // States for the Date Picker inputs
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const { currentTicker, fetchStockPriceWithDateRange } =
    useApplicationContext();

  const fetchData = async (start: string = "", end: string = "") => {
    if (!currentTicker) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetchStockPriceWithDateRange(
        currentTicker,
        start,
        end,
      );
      if (response && response.data && response.data.length > 0) {
        const sortedData = [...response.data].sort(
          (a, b) =>
            new Date(`${a.date}T${a.time}Z`).getTime() -
            new Date(`${b.date}T${b.time}Z`).getTime(),
        );
        setData(sortedData);

        // Requirement 3: Auto-update calendar inputs based on response
        const oldest = sortedData[0].date;
        const latest = sortedData[sortedData.length - 1].date;
        setStartDate(oldest!);
        setEndDate(latest!);
      } else {
        setData([]);
      }
    } catch (err) {
      setError("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentTicker]);

  const metrics = useMemo(() => {
    if (!data || data.length === 0) return null;

    const first = data[0];
    const latest = data[data.length - 1];
    const priceChange = latest.Close - first.Close;

    return {
      latestClose: latest.Close,
      latestDate: latest.date,
      latestTime: latest.time,
      priceChange,
      percentageChange: ((priceChange / first.Close) * 100).toFixed(2),
      highestHigh: Math.max(...data.map((item) => item.High)),
      lowestLow: Math.min(...data.map((item) => item.Low)),
    };
  }, [data]);

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {!loading && metrics && (
          <>
            {/* Latest Close */}
            <Card className="shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold uppercase tracking-wider">
                  Latest Close
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-slate-100">
                    <Icon
                      iconName="money-dollar-circle-line"
                      className="text-slate-600"
                    />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      ${metrics.latestClose.toFixed(2)}
                    </p>
                    <p className="text-[10px] font-bold uppercase tracking-tight">
                      Updated {metrics.latestTime}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Price Performance (unchanged, reference card) */}
            <Card className="shadow-sm border-slate-100">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold uppercase tracking-wider">
                  Price Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "p-2 rounded-lg",
                      metrics.priceChange >= 0 ? "bg-emerald-50" : "bg-rose-50",
                    )}
                  >
                    <Icon
                      iconName={
                        metrics.priceChange >= 0
                          ? "arrow-right-up-line"
                          : "arrow-right-down-line"
                      }
                      className={
                        metrics.priceChange >= 0
                          ? "text-emerald-600"
                          : "text-rose-600"
                      }
                    />
                  </div>
                  <div>
                    <p
                      className={cn(
                        "text-2xl font-bold",
                        metrics.priceChange >= 0
                          ? "text-emerald-600"
                          : "text-rose-600",
                      )}
                    >
                      {metrics.priceChange >= 0 ? "+" : ""}
                      {metrics.priceChange.toFixed(2)}
                    </p>
                    <p className="text-[10px] font-bold uppercase tracking-tight">
                      {metrics.percentageChange}% Change
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Range Extremes */}
            <Card className="shadow-sm border-slate-100">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-bold uppercase tracking-wider">
                  Range Extremes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-50">
                    <Icon iconName="bar-chart-line" className="text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      ${metrics.highestHigh.toFixed(2)}
                    </p>
                    <p className="text-[10px] font-bold uppercase tracking-tight">
                      Low ${metrics.lowestLow.toFixed(2)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Date Range Filters*/}
      <Card className="border-none shadow-sm  backdrop-blur">
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase ml-1">From</span>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-40 h-9 text-sm focus-visible:ring-blue-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase ml-1">To</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-40 h-9 text-sm focus-visible:ring-blue-500"
              />
            </div>
            <Button
              onClick={() => fetchData(startDate, endDate)}
              disabled={loading}
              size="sm"
              className="mt-5 "
            >
              {loading ? "Updating..." : "Update View"}
            </Button>
          </div>

          {metrics && (
            <div className="text-right">
              <p className="text-[10px] font-bold uppercase">
                Reference Period
              </p>
              <p className="text-xs font-medium">
                {new Date(startDate).toLocaleDateString()} —{" "}
                {new Date(endDate).toLocaleDateString()}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chart Section */}
      {data && data.length > 0 ? (
        // <LineChartCard
        //   title={`${currentTicker} Price Movement`}
        //   xAxisKey="name"
        //   series={[
        //     {
        //       dataKey: "close",
        //       label: "Close",
        //       color: "#8884d8",
        //     },
        //   ]}
        //   data={data.map((item) => {
        //     return {
        //       name: item.date || "",
        //       time: item.time || "",
        //       tooltipLabel: `${item.date || ""} ${item.time || ""}`,
        //       close: item.Close,
        //     };
        //   })}
        // />
        <CandleChartCard
          title={`Stock Price - Ticker : ${currentTicker}`}
          description="Candlestick representation of stock prices"
          data={data.map((item) => ({
            date: item.date,
            time: item.time,
            open: item.Open,
            high: item.High,
            low: item.Low,
            close: item.Close,
          }))}
          xAxisKey="date"
          bullColor="hsl(142, 76%, 36%)"
          bearColor="hsl(0, 84%, 60%)"
        />
      ) : (
        !loading && (
          <div className="h-64 flex items-center justify-center">
            No data available
          </div>
        )
      )}
    </div>
  );
}
