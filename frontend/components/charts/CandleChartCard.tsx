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
import { CartesianGrid, ComposedChart, XAxis, YAxis, Bar } from "recharts";
import { useMemo } from "react";

interface CandleDataPoint {
  [key: string]: any;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface CandleChartCardProps {
  title?: string;
  description?: string;
  data: CandleDataPoint[];
  xAxisKey: string;
  height?: number;
  showGrid?: boolean;
  showYAxis?: boolean;
  yAxisPadding?: number;
  className?: string;
  bullColor?: string;
  bearColor?: string;
  tooltipKey?: string;
}

export default function CandleChartCard({
  title,
  description,
  data,
  xAxisKey,
  tooltipKey = undefined,
  height = 400,
  showGrid = true,
  showYAxis = true,
  yAxisPadding = 0.05,
  className,
  bullColor = "hsl(142, 76%, 36%)",
  bearColor = "hsl(0, 84%, 60%)",
}: CandleChartCardProps) {
  const chartConfig: ChartConfig = {
    candle: {
      label: "Price",
    },
  };

  const yAxisDomain = useMemo(() => {
    if (!data.length) return [0, 100];

    let min = Infinity;
    let max = -Infinity;

    data.forEach((item) => {
      min = Math.min(min, item.low);
      max = Math.max(max, item.high);
    });

    if (min === Infinity || max === -Infinity) return [0, 100];

    if (min === max) {
      min -= 1;
      max += 1;
    }

    const range = max - min;
    const padding = range * yAxisPadding;

    return [Math.floor(min - padding), Math.ceil(max + padding)];
  }, [data, yAxisPadding]);

  const Candle = (props: any) => {
    const { x, y, width, height, payload } = props;
    const { open, close, high, low } = payload;

    const isGreen = close > open;
    const color = isGreen ? bullColor : bearColor;
    const candleWidth = Math.max(width * 0.6, 2);
    const centerX = x + width / 2;

    const topPrice = Math.max(open, close);
    const bottomPrice = Math.min(open, close);
    const candleHeight = Math.abs(
      ((topPrice - bottomPrice) / (yAxisDomain[1] - yAxisDomain[0])) * height,
    );
    const candleY =
      y +
      ((yAxisDomain[1] - topPrice) / (yAxisDomain[1] - yAxisDomain[0])) *
        height;

    const highY =
      y +
      ((yAxisDomain[1] - high) / (yAxisDomain[1] - yAxisDomain[0])) * height;
    const lowY =
      y + ((yAxisDomain[1] - low) / (yAxisDomain[1] - yAxisDomain[0])) * height;

    return (
      <g>
        <line
          x1={centerX}
          y1={highY}
          x2={centerX}
          y2={lowY}
          stroke={color}
          strokeWidth={1}
        />
        <rect
          x={centerX - candleWidth / 2}
          y={candleY}
          width={candleWidth}
          height={Math.max(candleHeight, 1)}
          fill={color}
          stroke={color}
          strokeWidth={1.5}
        />
      </g>
    );
  };

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
          <ComposedChart
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

                const data = payload[0].payload;
                const isGreen = data.close > data.open;

                return (
                  <div className="rounded-lg border bg-background p-3 shadow-sm">
                    <div className="grid gap-2">
                      <div className="font-medium text-sm">
                        {data[tooltipKey || xAxisKey]}
                      </div>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                        <span className="text-muted-foreground">Open:</span>
                        <span className="font-medium text-right">
                          {data.open.toFixed(2)}
                        </span>
                        <span className="text-muted-foreground">High:</span>
                        <span className="font-medium text-right">
                          {data.high.toFixed(2)}
                        </span>
                        <span className="text-muted-foreground">Low:</span>
                        <span className="font-medium text-right">
                          {data.low.toFixed(2)}
                        </span>
                        <span className="text-muted-foreground">Close:</span>
                        <span
                          className="font-medium text-right"
                          style={{ color: isGreen ? bullColor : bearColor }}
                        >
                          {data.close.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="close"
              fill="transparent"
              isAnimationActive={false}
              shape={<Candle />}
            />
          </ComposedChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
