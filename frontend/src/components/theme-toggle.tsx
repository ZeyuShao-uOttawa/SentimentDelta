"use client";
import { Icon } from "./icons";
import { useTheme } from "@/context/theme-provider";
import { Button } from "./ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const next = (theme === "light" ? "dark" : "light") as "light" | "dark";
  return (
    <Button
      onClick={() => setTheme(next)}
      aria-label="Toggle theme"
      title={`Switch to ${next} theme`}
      className={`fixed bottom-5 right-5 w-12 h-12 rounded-full p-0 inline-flex items-center justify-center shadow-lg transition-colors focus:outline-none ${
        theme === "light" ? "bg-white text-black" : "bg-slate-900 text-white"
      }`}
    >
      {theme === "light" ? (
        <Icon
          iconName="sun-line"
          iconSize="md"
          className="absolute inset-0 flex items-center justify-center"
          aria-hidden
        />
      ) : (
        <Icon
          iconName="moon-line"
          iconSize="md"
          className="absolute inset-0 flex items-center justify-center"
          aria-hidden
        />
      )}
    </Button>
  );
}
