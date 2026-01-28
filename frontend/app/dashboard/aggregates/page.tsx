"use client";
import React, { useEffect, useState } from "react";
import { useApplicationContext } from "@/context/application-context";
import { aggregateResponse } from "@/api/resposne";
import { DataTable } from "@/components/ui/data-table";
import LineChartCard from "@/components/charts/LineChartCard";

const columns = [
  {
    accessorKey: "date",
    header: "Date",
  },
  {
    accessorKey: "attention",
    header: "Attention",
  },
  {
    accessorKey: "bull_bear_ratio",
    header: "Bull/Bear Ratio",
  },
  {
    accessorKey: "sent_mean",
    header: "Sentiment Mean",
  },
  {
    accessorKey: "sent_std",
    header: "Sentiment Std Dev",
  },
];

export default function AggregatesPage() {
  const { currentTicker, fetchAggregatesByTicker, aggregates } =
    useApplicationContext();
  const [aggregateData, setAggregateData] = useState<aggregateResponse | null>(
    null,
  );

  useEffect(() => {
    if (currentTicker) {
      fetchAggregatesByTicker().then((data) => {
        if (data) {
          setAggregateData(data);
        }
      });
    }
  }, [currentTicker]);

  return (
    <div className="p-4">
      {aggregateData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <LineChartCard
            title="Bull/Bear Ratio Over Time"
            data={aggregateData.data}
            dataKey="bull_bear_ratio"
            nameKey="date"
            seriesKey="bull_bear_ratio"
            colors={["#8884d8"]}
            height={300}
          />

          <LineChartCard
            title="Sentiment Mean Over Time"
            data={aggregateData.data}
            dataKey="sent_mean"
            nameKey="date"
            seriesKey="sent_mean"
            colors={["#82ca9d"]}
            height={300}
          />

          <LineChartCard
            title="Sentiment Std Dev Over Time"
            data={aggregateData.data}
            dataKey="sent_std"
            nameKey="date"
            seriesKey="sent_std"
            colors={["#ffc658"]}
            height={300}
          />

          <LineChartCard
            title="Combined Metrics Over Time"
            data={aggregateData.data}
            nameKey="date"
            seriesKey="combined_metrics"
            height={400}
            colors={["#8884d8", "#82ca9d", "#ffc658"]}
            showTooltip={true}
            margin={{ left: 20, right: 20, top: 10, bottom: 10 }}
            config={{
              bull_bear_ratio: { label: "Bull/Bear Ratio", color: "#8884d8" },
              sent_mean: { label: "Sentiment Mean", color: "#82ca9d" },
              sent_std: { label: "Sentiment Std Dev", color: "#ffc658" },
            }}
          />
        </div>
      )}

      {aggregateData && (
        <div className="mb-8">
          <DataTable
            columns={columns}
            data={aggregateData.data}
            filterKey="date"
          />
        </div>
      )}
    </div>
  );
}
