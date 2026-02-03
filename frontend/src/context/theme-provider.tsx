"use client";

import React, { useEffect, useState, createContext, useContext } from "react";

type Theme = "light" | "dark" | "system";

type ThemeContextType = {
  theme: Theme;
  setTheme: (t: Theme) => void;
};

const ThemeContext = createContext<ThemeContextType>({
  theme: "light",
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("theme") as Theme | null;
      if (stored) setTheme(stored);
      else setTheme("system");
    } catch (e) {
      setTheme("system");
    }
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const apply = (t: Theme) => {
      root.classList.remove("light", "dark");
      let resolved = t;
      if (t === "system") {
        resolved =
          window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
      }
      root.classList.add(resolved);
    };

    apply(theme);
    try {
      localStorage.setItem("theme", theme);
    } catch (e) {}

    const mq =
      window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if (theme === "system") apply("system");
    };
    if (mq && mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq && mq.addListener) mq.addListener(onChange);

    return () => {
      if (mq && mq.removeEventListener)
        mq.removeEventListener("change", onChange);
      else if (mq && mq.removeListener) mq.removeListener(onChange);
    };
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
