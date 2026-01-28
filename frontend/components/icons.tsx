"use client";

import React, { useMemo, useEffect, useState } from "react";
import * as RemixIcons from "@remixicon/react";
import { cn } from "@/lib/utils";
import { BRAND_COLORS, type BrandColorKey } from "@/lib/colors";
import { useTheme } from "@/context/theme-provider";

const ICON_SIZE_CLASSES = {
  xs: "text-xs",
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
  xl: "text-xl",
  "2xl": "text-2xl",
} as const;

const BACKGROUND_SIZE_CLASSES = {
  none: "",
  sm: "h-8 w-8",
  md: "h-12 w-12",
  lg: "h-16 w-16",
  xl: "h-20 w-20",
} as const;

const LEGACY_SIZE_CLASSES = {
  sm: "h-8 w-8 text-base",
  md: "h-12 w-12 text-2xl",
  lg: "h-16 w-16 text-3xl",
  xl: "h-20 w-20 text-4xl",
} as const;

const BORDER_RADIUS = {
  none: "rounded-none",
  sm: "rounded-sm",
  md: "rounded-md",
  lg: "rounded-lg",
  xl: "rounded-xl",
  full: "rounded-full",
} as const;

export interface IconProps {
  iconName: string; // remixicon kebab-name, e.g. "sun-line"
  backgroundColor?: BrandColorKey;
  iconColor?: BrandColorKey;
  iconColorDark?: BrandColorKey;
  borderRadius?: keyof typeof BORDER_RADIUS;
  iconSize?: keyof typeof ICON_SIZE_CLASSES;
  backgroundSize?: keyof typeof BACKGROUND_SIZE_CLASSES;
  /** @deprecated */
  size?: keyof typeof LEGACY_SIZE_CLASSES;
  align?: "start" | "center" | "end";
  className?: string; // wrapper
  iconClassName?: string; // inner icon
}

const PIXEL_SIZES: Record<string, number> = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 20,
  xl: 24,
};

function kebabToPascal(kebab: string) {
  return kebab
    .split("-")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join("");
}

export const Icon: React.FC<IconProps> = ({
  iconName,
  backgroundColor,
  iconColor,
  iconColorDark,
  borderRadius = "full",
  iconSize,
  align = "center",
  backgroundSize,
  size = "lg",
  className,
  iconClassName,
}) => {
  const { theme } = useTheme();
  const [textColor, setTextColor] = useState<string | undefined>();
  const bgColor = backgroundColor ? BRAND_COLORS[backgroundColor] : undefined;

  useEffect(() => {
    if (!theme) return;
    if (iconColor && !iconColorDark) setTextColor(BRAND_COLORS[iconColor]);
    else if (iconColor && iconColorDark)
      setTextColor(
        theme === "dark"
          ? BRAND_COLORS[iconColorDark]
          : BRAND_COLORS[iconColor],
      );
    else if (iconColorDark && !iconColor)
      setTextColor(BRAND_COLORS[iconColorDark]);
    else setTextColor(undefined);
  }, [theme, iconColor, iconColorDark]);

  const useNewSizeSystem = Boolean(iconSize || backgroundSize);
  const finalIconSize = iconSize || (useNewSizeSystem ? "lg" : undefined);
  const finalBackgroundSize =
    backgroundSize || (useNewSizeSystem ? "none" : undefined);

  const compName = useMemo(() => `Ri${kebabToPascal(iconName)}`, [iconName]);
  const Comp = (RemixIcons as any)[compName] as
    | React.ComponentType<any>
    | undefined;

  const wrapperClasses = cn(
    "flex items-center",
    align === "start"
      ? "justify-start"
      : align === "end"
        ? "justify-end"
        : "justify-center",
    useNewSizeSystem && finalBackgroundSize
      ? BACKGROUND_SIZE_CLASSES[
          finalBackgroundSize as keyof typeof BACKGROUND_SIZE_CLASSES
        ]
      : LEGACY_SIZE_CLASSES[size as keyof typeof LEGACY_SIZE_CLASSES],
    backgroundColor || borderRadius !== "full"
      ? BORDER_RADIUS[borderRadius]
      : "",
    className,
  );

  const iconClasses = cn(
    useNewSizeSystem && finalIconSize
      ? ICON_SIZE_CLASSES[finalIconSize as keyof typeof ICON_SIZE_CLASSES]
      : "",
    iconClassName,
  );

  const pixelSize = finalIconSize ? (PIXEL_SIZES[finalIconSize] ?? 20) : 20;

  return (
    <div className={wrapperClasses} style={{ backgroundColor: bgColor }}>
      {Comp ? (
        <Comp
          size={pixelSize}
          className={iconClasses}
          style={{ color: textColor }}
          aria-hidden
        />
      ) : (
        <i
          className={cn(`ri-${iconName} font-normal`, iconClasses)}
          style={{ color: textColor }}
        />
      )}
    </div>
  );
};
