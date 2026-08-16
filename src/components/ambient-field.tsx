"use client";

import { useEffect, useRef } from "react";

const signalColours = [
  [164, 82, 73],
  [85, 117, 165],
  [93, 119, 103],
  [168, 135, 66],
  [178, 77, 67],
] as const;

type AmbientFieldProps = {
  signal?: number;
  engaged?: boolean;
};

export function AmbientField({ signal = 0, engaged = false }: AmbientFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext("2d", { alpha: true });
    if (!context) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const pointer = { x: window.innerWidth * 0.68, y: window.innerHeight * 0.42 };
    let pointerActive = false;
    let width = 0;
    let height = 0;
    let pixelRatio = 1;
    let animationFrame = 0;
    let previousFrame = 0;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.round(width * pixelRatio);
      canvas.height = Math.round(height * pixelRatio);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    };

    const draw = (time: number) => {
      if (time - previousFrame < 48 && !reducedMotion.matches) {
        animationFrame = window.requestAnimationFrame(draw);
        return;
      }

      previousFrame = time;
      context.clearRect(0, 0, width, height);

      const dark = document.documentElement.dataset.timeTheme === "dark";
      const ink = dark ? [220, 222, 214] : [29, 33, 30];
      const accent = signalColours[signal % signalColours.length];
      const spacing = width < 720 ? 34 : 29;
      const focusX = pointerActive ? pointer.x : width * 0.66;
      const focusY = pointerActive ? pointer.y : height * 0.42;
      const movement = reducedMotion.matches ? 0 : time * 0.00008;

      for (let y = 0; y < height + spacing; y += spacing) {
        for (let x = 0; x < width + spacing; x += spacing) {
          const distance = Math.hypot(x - focusX, y - focusY);
          const attention = Math.max(0, 1 - distance / 340);
          const noise = Math.sin(x * 0.021 + y * 0.017 + movement * 7 + signal);
          const radius = 0.35 + Math.max(0, noise) * 0.12 + attention * (engaged ? 0.55 : 0.2);

          context.beginPath();
          context.arc(x, y, radius, 0, Math.PI * 2);
          context.fillStyle = `rgba(${ink.join(",")}, ${0.018 + attention * 0.028})`;
          context.fill();
        }
      }

      const waveCount = width < 720 ? 3 : 6;
      for (let wave = 0; wave < waveCount; wave += 1) {
        context.beginPath();
        for (let x = -20; x <= width + 20; x += 14) {
          const distance = Math.abs(x - focusX);
          const pull = Math.max(0, 1 - distance / 460);
          const baseline = height * 0.5 + (wave - (waveCount - 1) / 2) * 25;
          const amplitude = (engaged ? 13 : 6) + pull * (engaged ? 19 : 7);
          const y = baseline + Math.sin(x * (0.007 + signal * 0.0007) + movement * 6 + wave * 0.7) * amplitude;

          if (x === -20) context.moveTo(x, y);
          else context.lineTo(x, y);
        }

        context.strokeStyle = `rgba(${accent.join(",")}, ${engaged ? 0.038 : 0.018})`;
        context.lineWidth = 0.7;
        context.stroke();
      }

      const glow = context.createRadialGradient(focusX, focusY, 0, focusX, focusY, engaged ? 250 : 130);
      glow.addColorStop(0, `rgba(${accent.join(",")}, ${engaged ? 0.055 : 0.018})`);
      glow.addColorStop(1, `rgba(${accent.join(",")}, 0)`);
      context.fillStyle = glow;
      context.fillRect(0, 0, width, height);

      if (!reducedMotion.matches) animationFrame = window.requestAnimationFrame(draw);
    };

    const handlePointer = (event: globalThis.PointerEvent) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointerActive = event.pointerType !== "touch";
    };

    const clearPointer = () => {
      pointerActive = false;
    };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", handlePointer, { passive: true });
    document.documentElement.addEventListener("pointerleave", clearPointer);
    draw(0);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", handlePointer);
      document.documentElement.removeEventListener("pointerleave", clearPointer);
    };
  }, [signal, engaged]);

  return <canvas ref={canvasRef} className="ambient-field" aria-hidden="true" />;
}
