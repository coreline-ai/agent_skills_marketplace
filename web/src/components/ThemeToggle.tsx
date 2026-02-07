"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
    const { theme, setTheme, resolvedTheme } = useTheme();
    const [mounted, setMounted] = React.useState(false);

    // Avoid hydration mismatch
    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return (
            <div className="w-10 h-10 border-2 border-black bg-white shadow-[2px_2px_0px_0px_#000]"></div>
        );
    }

    const toggleTheme = () => {
        setTheme(resolvedTheme === "dark" ? "light" : "dark");
    };

    return (
        <button
            onClick={toggleTheme}
            className="inline-flex items-center justify-center w-10 h-10 border-2 border-black dark:border-white bg-white dark:bg-black text-black dark:text-white shadow-[4px_4px_0px_0px_#000] dark:shadow-none hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_#000] dark:hover:translate-x-0 dark:hover:translate-y-0 dark:hover:shadow-none transition-all p-0"
            aria-label="Toggle theme"
        >
            {resolvedTheme === "dark" ? (
                <Sun className="h-5 w-5" />
            ) : (
                <Moon className="h-5 w-5" />
            )}
        </button>
    );
}
