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
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import { useMemo } from "react";
import {
  calculateYAxisDomain,
  generateChartConfig,
  SeriesConfig,
} from "@/lib/chart-utils";

interface LineChartCardProps {
  title?: string;
  description?: string;
  data: Record<string, any>[];
  xAxisKey: string;
  series: SeriesConfig[];
  height?: number;
  showGrid?: boolean;
  showYAxis?: boolean;
  yAxisPadding?: number;
  className?: string;
}

export default function LineChartCard({
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
}: LineChartCardProps) {
  const chartConfig = useMemo(() => generateChartConfig(series), [series]);

  const yAxisDomain = useMemo(
    () => calculateYAxisDomain(data, series, yAxisPadding),
    [data, series, yAxisPadding],
  );

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
          <LineChart
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
              <Line
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                stroke={`var(--color-${s.dataKey})`}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
