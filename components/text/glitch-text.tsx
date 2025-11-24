import React from "react";
import { Tomorrow } from "next/font/google";

import { cn } from "@/lib/utils";
import { Stack } from "@/components/stack";

const tomorrow = Tomorrow({
  subsets: ["latin"],
  weight: ["800"],
  variable: "--font-tomorrow",
});

export const GlitchText = ({
  text = "1000 Stars",
  className,
  starCount = 50,
}: {
  text: string;
  className?: string;
  starCount?: number;
}) => {
  return (
    <Stack className="relative overflow-hidden" items="center" justify="center">
      <Stack className="relative" items="center" justify="center">
        {[...Array(starCount)].map((_, i) => (
          <div
            key={i}
            className="star absolute aspect-square animate-twinkle rounded-full bg-[#fafafa] opacity-75"
            style={{
              width: `${Math.random() * 4}px`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
            }}
          />
        ))}
        <h1
          className={cn(
            "glitch-text z-10 animate-[glitch_0.5s_infinite]",
            className,
            tomorrow.className,
          )}
          aria-label={text}
        >
          {text}
        </h1>
      </Stack>
    </Stack>
  );
}
