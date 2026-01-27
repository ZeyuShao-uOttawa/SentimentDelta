export const BRAND_COLORS = {
    slate: "#64748b",
    gray: "#6b7280",
    zinc: "#71717a",
    neutral: "#737373",
    stone: "#78716c",
    red: "#ef4444",
    orange: "#f97316",
    amber: "#f59e0b",
    yellow: "#eab308",
    lime: "#84cc16",
    green: "#10b981",
    emerald: "#10b981",
    teal: "#14b8a6",
    cyan: "#06b6d4",
    sky: "#0ea5e9",
    blue: "#3b82f6",
    indigo: "#6366f1",
    violet: "#8b5cf6",
    purple: "#7c3aed",
    fuchsia: "#d946ef",
    pink: "#ec4899",
    rose: "#fb7185",
} as const;

export type BrandColorKey = keyof typeof BRAND_COLORS;
export type BrandColors = typeof BRAND_COLORS;

export const BRAND_COLOR_KEYS = Object.keys(BRAND_COLORS) as BrandColorKey[];

export const isBrandColor = (v: string): v is BrandColorKey =>
    v in BRAND_COLORS;

export const getBrandColor = (key: BrandColorKey) => BRAND_COLORS[key];

export const getBrandColorOr = (key: string, fallback = "#000000") =>
    isBrandColor(key) ? BRAND_COLORS[key] : fallback;
