"use client";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

type Theme = "dark" | "light";

export function useTheme(): [Theme, (t: Theme) => void] {
  const [theme, setThemeState] = useState<Theme>("dark");
  useEffect(() => {
    setThemeState(document.documentElement.dataset.theme === "light" ? "light" : "dark");
  }, []);
  const setTheme = (t: Theme) => {
    document.documentElement.dataset.theme = t;
    try {
      localStorage.setItem("mantis-theme", t);
    } catch {
      /* storage unavailable: the theme still applies for this visit */
    }
    setThemeState(t);
  };
  return [theme, setTheme];
}

export default function ThemeToggle({ withLabel = false }: { withLabel?: boolean }) {
  const [theme, setTheme] = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  const Icon = theme === "dark" ? Sun : Moon;
  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      className={withLabel ? "btn-quiet w-full justify-start px-3" : "btn-quiet h-9 w-9 p-0"}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
    >
      <Icon size={16} />
      {withLabel && <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>}
    </button>
  );
}
