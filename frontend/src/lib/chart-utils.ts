import { ChartConfig } from "@/components/ui/chart";

export interface SeriesConfig {
  dataKey: string;
  color: string;
  label?: string;
}

export function generateChartConfig(series: SeriesConfig[]): ChartConfig {
  return series.reduce((config, s) => {
    config[s.dataKey] = {
      label: s.label || s.dataKey,
      color: s.color,
    };
    return config;
  }, {} as ChartConfig);
}

export function calculateYAxisDomain(
  data: Record<string, any>[],
  series: SeriesConfig[],
  yAxisPadding = 0.1,
): [number, number] {
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
}
