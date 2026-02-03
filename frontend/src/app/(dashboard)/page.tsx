"use client";
import React, { useEffect, useState } from "react";
import { useApplicationContext } from "@/context/application-context";
import { aggregateResponse } from "@/api/responses";
import { DataTable } from "@/components/ui/data-table";
import LineChartCard from "@/components/charts/LineChartCard";
import AreaChartCard from "@/components/charts/AreaChartCard";

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
      {!currentTicker && (
        <div className="flex flex-col items-center justify-center min-h-[400px] text-muted-foreground">
          <p>Please select a ticker from the sidebar to view aggregate data.</p>
        </div>
      )}

      {currentTicker && !aggregateData && (
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-4 text-muted-foreground">
            Loading aggregate data for {currentTicker}...
          </p>
        </div>
      )}

      {currentTicker && aggregateData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <LineChartCard
            className="md:col-span-3"
            title="Financial Overview"
            description="Monthly metrics"
            data={aggregateData.data}
            xAxisKey="date"
            series={[
              {
                dataKey: "bull_bear_ratio",
                color: "#8884d8",
                label: "Bull/Bear Ratio",
              },
              {
                dataKey: "sent_mean",
                color: "#82ca9d",
                label: "Sentiment Mean",
              },
              {
                dataKey: "sent_std",
                color: "#ffc658",
                label: "Sentiment Std Dev",
              },
            ]}
          />

          <AreaChartCard
            title="Bull/Bear Ratio Over Time"
            xAxisKey="date"
            series={[
              {
                dataKey: "bull_bear_ratio",
                color: "#8884d8",
                label: "Bull/Bear Ratio",
              },
            ]}
            data={aggregateData.data}
            height={300}
            yAxisPadding={0}
          />

          <AreaChartCard
            title="Sentiment Mean Over Time"
            xAxisKey="date"
            series={[
              {
                dataKey: "sent_mean",
                color: "#82ca9d",
                label: "Sentiment Mean",
              },
            ]}
            data={aggregateData.data}
            height={300}
            yAxisPadding={0}
          />

          <AreaChartCard
            title="Sentiment Std Dev Over Time"
            xAxisKey="date"
            series={[
              {
                dataKey: "sent_std",
                color: "#ffc658",
                label: "Sentiment Std Dev",
              },
            ]}
            data={aggregateData.data}
            height={300}
            yAxisPadding={0}
          />
        </div>
      )}
      {/* 
      {aggregateData && (
        <div className="mb-8">
          <DataTable columns={columns} data={aggregateData.data} />
        </div>
      )} */}
    </div>
  );
}
