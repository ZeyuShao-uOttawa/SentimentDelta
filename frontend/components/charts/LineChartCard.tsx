"use client";

import React from "react";
import {
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

export type LineChartCardProps = {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  data: Array<Record<string, any>>;
  dataKey?: string;
  nameKey?: string;
  seriesKey: string;
  colorVar?: string;
  colors?: string[];
  height?: number | string;
  width?: number | string;
  strokeWidth?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  className?: string;
};

export default function LineChartCard({
  title,
  subtitle,
  data,
  dataKey = "value",
  nameKey = "name",
  seriesKey,
  colorVar = "var(--chart-2)",
  colors,
  height = 200,
  width = "100%",
  strokeWidth = 2,
  showGrid = true,
  showTooltip = true,
  margin = { left: 12, right: 12, top: 6, bottom: 6 },
  className,
}: LineChartCardProps) {
  const color = colors?.[0] ?? colorVar;
  const config: ChartConfig = {
    [seriesKey]: { label: seriesKey, color },
  };

  return (
    <Card className={className}>
      <CardHeader>
        {title && <CardTitle>{title}</CardTitle>}
        {subtitle && <CardDescription>{subtitle}</CardDescription>}
      </CardHeader>
      <CardContent>
        <ChartContainer config={config}>
          <ResponsiveContainer width={width} height={height}>
            <LineChart data={data} margin={margin}>
              {showGrid && (
                <CartesianGrid
                  vertical={false}
                  strokeDasharray="3 3"
                  strokeOpacity={0.06}
                />
              )}
              <XAxis
                dataKey={nameKey}
                tickLine={false}
                axisLine={false}
                tickMargin={8}
              />
              <YAxis tickLine={false} axisLine={false} />
              {showTooltip && (
                <ChartTooltip
                  cursor={false}
                  content={<ChartTooltipContent indicator="dot" />}
                />
              )}
              <Line
                dataKey={dataKey}
                stroke={`var(--color-${seriesKey})`}
                strokeWidth={strokeWidth}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
      <CardFooter />
    </Card>
  );
}
