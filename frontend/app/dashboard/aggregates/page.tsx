import React from "react";
import AreaChartCard from "@/components/charts/AreaChartCard";

const sampleData = [
  { month: "Jan", desktop: 30, mobile: 18 },
  { month: "Feb", desktop: 45, mobile: 28 },
  { month: "Mar", desktop: 28, mobile: 20 },
  { month: "Apr", desktop: 60, mobile: 30 },
  { month: "May", desktop: 72, mobile: 40 },
  { month: "Jun", desktop: 55, mobile: 35 },
];

export default function AggregatesPage() {
  return (
    <div>
      <div className="grid grid-cols-1 gap-4">
        <AreaChartCard
          title="Traffic by Device"
          subtitle="Last 6 months"
          data={sampleData}
          nameKey="month"
          seriesKey=""
          height={300}
        />
      </div>
    </div>
  );
}
