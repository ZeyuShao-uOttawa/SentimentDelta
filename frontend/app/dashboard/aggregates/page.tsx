"use client";
import React, { useEffect, useState } from "react";
import { useApplicationContext } from "@/context/application-context";
import { aggregateResponse } from "@/api/resposne";
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

  const dataa = [
    { month: "Jan", revenue: 450, expenses: 420, profit: 30 },
    { month: "Feb", revenue: 480, expenses: 430, profit: 50 },
    { month: "Mar", revenue: 510, expenses: 445, profit: 65 },
    { month: "Apr", revenue: 530, expenses: 460, profit: 70 },
    { month: "May", revenue: 600, expenses: 500, profit: 100 },
    { month: "Jun", revenue: 620, expenses: 520, profit: 100 },
    { month: "Jul", revenue: 700, expenses: 580, profit: 120 },
    { month: "Aug", revenue: 750, expenses: 600, profit: 150 },
    { month: "Sep", revenue: 800, expenses: 650, profit: 150 },
    { month: "Oct", revenue: 850, expenses: 700, profit: 150 },
    { month: "Nov", revenue: 900, expenses: 750, profit: 150 },
    { month: "Dec", revenue: 950, expenses: 800, profit: 150 },
  ];

  return (
    <div className="p-4">
      {aggregateData && (
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

      {aggregateData && (
        <div className="mb-8">
          <DataTable columns={columns} data={aggregateData.data} />
        </div>
      )}
    </div>
  );
}
