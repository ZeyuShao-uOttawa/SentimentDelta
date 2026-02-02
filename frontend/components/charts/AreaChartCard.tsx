import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { useMemo } from "react";

interface AreaSeriesConfig {
  dataKey: string;
  color: string;
  label?: string;
}

interface AreaChartCardProps {
  title?: string;
  description?: string;
  data: Record<string, any>[];
  xAxisKey: string;
  series: AreaSeriesConfig[];
  height?: number;
  showGrid?: boolean;
  showYAxis?: boolean;
  yAxisPadding?: number;
  className?: string;
  stacked?: boolean;
}

export default function AreaChartCard({
  title,
  description,
  data,
  xAxisKey,
  series,
  height = 300,
  showGrid = true,
  showYAxis = true,
  yAxisPadding = 0.1,
  className,
  stacked = false,
}: AreaChartCardProps) {
  const chartConfig: ChartConfig = series.reduce((config, s) => {
    config[s.dataKey] = {
      label: s.label || s.dataKey,
      color: s.color,
    };
    return config;
  }, {} as ChartConfig);

  const yAxisDomain = useMemo(() => {
    if (!data.length || !series.length) return [0, 100];

    let min = Infinity;
    let max = -Infinity;

    data.forEach((item) => {
      series.forEach((s) => {
        const value = item[s.dataKey];
        if (typeof value === "number") {
          min = Math.min(min, value);
          max = Math.max(max, value);
        }
      });
    });

    if (min === Infinity || max === -Infinity) return [0, 100];

    const range = max - min;
    const padding = range * yAxisPadding;

    return [Math.floor(min - padding), Math.ceil(max + padding)];
  }, [data, series, yAxisPadding]);

  return (
    <Card className={className}>
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent>
        <ChartContainer
          config={chartConfig}
          className="w-full"
          style={{ height }}
        >
          <AreaChart
            data={data}
            margin={{ left: 0, right: 12, top: 12, bottom: 12 }}
          >
            {showGrid && (
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
            )}
            <XAxis
              dataKey={xAxisKey}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            {showYAxis && (
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                domain={yAxisDomain}
              />
            )}
            <ChartTooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;

                return (
                  <div className="rounded-lg border bg-background p-2 shadow-sm">
                    <div className="grid gap-2">
                      <div className="font-medium text-sm">
                        {payload[0].payload[xAxisKey]}
                      </div>
                      {payload.map((entry: any) => {
                        const config = chartConfig[entry.dataKey];
                        return (
                          <div
                            key={entry.dataKey}
                            className="flex items-center gap-2 text-xs"
                          >
                            <div
                              className="h-2 w-2 rounded-full"
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-muted-foreground">
                              {config?.label || entry.dataKey}:
                            </span>
                            <span className="font-medium">
                              {entry.value.toFixed(2)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              }}
            />
            {series.map((s) => (
              <Area
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                stroke={`var(--color-${s.dataKey})`}
                fill={`var(--color-${s.dataKey})`}
                fillOpacity={0.2}
                strokeWidth={2}
                stackId={stacked ? "stack" : undefined}
              />
            ))}
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
