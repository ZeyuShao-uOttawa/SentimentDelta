"use client";

import React from "react";
import {
  Area,
  AreaChart,
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

export type AreaChartCardProps = {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  data: Array<Record<string, any>>;
  dataKey?: string; // value field name
  nameKey?: string; // x axis field name
  seriesKey: string; // key used in ChartConfig for color/label
  colorVar?: string; // css var or color string (e.g. 'var(--chart-1)')
  colors?: string[];
  height?: number | string;
  width?: number | string;
  strokeWidth?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  className?: string;
  config?: ChartConfig; // config object for multiple series
};

export default function AreaChartCard({
  title,
  subtitle,
  data,
  dataKey = "value",
  nameKey = "name",
  seriesKey,
  colorVar = "var(--chart-1)",
  colors,
  height = 200,
  width = "100%",
  strokeWidth = 2,
  showGrid = true,
  showTooltip = true,
  margin = { left: 0, right: 0, top: 6, bottom: 0 },
  className,
  config,
}: AreaChartCardProps) {
  const color = colors?.[0] ?? colorVar;
  const resolvedConfig =
    config && Object.keys(config).length > 0
      ? config
      : { [seriesKey]: { label: seriesKey, color } };

  return (
    <Card className={className}>
      <CardHeader>
        {title && <CardTitle>{title}</CardTitle>}
        {subtitle && <CardDescription>{subtitle}</CardDescription>}
      </CardHeader>
      <CardContent className="pl-0 pr-6">
        <ChartContainer config={resolvedConfig}>
          <ResponsiveContainer width={width} height={height}>
            <AreaChart data={data} margin={margin}>
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
                  content={<ChartTooltipContent indicator="line" />}
                />
              )}
              {Object.keys(resolvedConfig).map((key, index) => (
                <Area
                  key={index}
                  dataKey={key}
                  type="natural"
                  stroke={resolvedConfig[key].color}
                  fill={resolvedConfig[key].color}
                  fillOpacity={0.12}
                  strokeWidth={strokeWidth}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
      <CardFooter />
    </Card>
  );
}
