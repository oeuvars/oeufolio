"use client";

import React, { useEffect, useRef, useState } from "react";
import { AnimationControls, motion, useAnimation } from "framer-motion";
import { cn } from "@/lib/utils";

export const BackgroundCellAnimation = () => {
  const variants = {
    hidden: { opacity: 0, x: 0, y: 200 },
    enter: { opacity: 1, x: 0, y: 0},
  }
return (
  <div className="relative h-screen bg-[#111111] grid justify-center items-center overflow-hidden">
    <BackgroundCellCore />
    <div className="grid gap-3 z-50">
      <motion.div transition={{ ease: "easeOut", duration: 1.1 }} variants={variants} initial="hidden" animate="enter" className="relative pointer-events-none select-none flex gap-2 justify-center">
         <img src="/icons/Logo.svg" alt="" className="phone:w-12 phone:h-12 lg:w-20 lg:h-20 my-auto"/>
         <h1 className="phone:text-5xl lg:text-7xl font-playfair p-1 my-auto bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-400 to-neutral-500 tracking-tighter">Oeuvars</h1>
      </motion.div>
      <motion.div transition={{ ease: "easeOut", duration: 1.2 }} variants={variants} initial="hidden" animate="enter" className="phone:text-2xl lg:text-3xl bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-300 to-neutral-400 tracking-tight text-center font-parisienne py-1">Anurag Das. Lemme land g.</motion.div>
      <motion.div className="flex w-full phone:gap-2 lg:gap-0 mt-2 " transition={{ ease: "easeOut", duration: 1.3 }} variants={variants} initial="hidden" animate="enter">
        <input
          className="bg-[#222222] text-[#FAFAFA] px-6 py-3 w-full rounded-md outline-none focus:outline-2 focus:outline focus:outline-[#333333]"
          placeholder="something@gmail.com"
          type="email"
          id="email"
          name="email"
          required
        />
        <button className="-ml-10">
          <img src="/icons/arrow.svg" alt="" className="w-7 h-7 my-auto"/>
        </button>
      </motion.div>
    </div>
  </div>
);
};

const BackgroundCellCore = () => {
const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
const ref = useRef<any>(null);
const handleMouseMove = (event: any) => {
  const rect = ref.current && ref.current.getBoundingClientRect();
  setMousePosition({
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  });
};

const size = 300;
return (
  <div
    ref={ref}
    onMouseMove={handleMouseMove}
    className="h-full absolute inset-0"
  >
    <div className="absolute h-[20rem] inset-y-0 overflow-hidden">
      <div className="absolute h-full w-full pointer-events-none -bottom-2 z-40 bg-[#111111] [mask-image:linear-gradient(to_bottom,transparent,black)]"></div>
      <div
        className="absolute inset-0 z-20 bg-transparent"
        style={{
          maskImage: `radial-gradient(
            ${size / 4}px circle at center,
           white, transparent
          )`,
          WebkitMaskImage: `radial-gradient(
          ${size / 4}px circle at center,
          white, transparent
        )`,
          WebkitMaskPosition: `${mousePosition.x - size / 2}px ${
            mousePosition.y - size / 2
          }px`,
          WebkitMaskSize: `${size}px`,
          maskSize: `${size}px`,
          pointerEvents: "none",
          maskRepeat: "no-repeat",
          WebkitMaskRepeat: "no-repeat",
        }}
      >
        <Pattern cellClassName="border-purple-600 relative z-[100]" />
      </div>
      <Pattern className="opacity-[0.5]" cellClassName="border-neutral-700" />
    </div>
  </div>
);
};

function Pattern({className, cellClassName}: {className?: string; cellClassName?: string}) {
  const x = new Array(47).fill(0);
  const y = new Array(30).fill(0);
  const matrix = x.map((_, i) => y.map((_, j) => [i, j]));
  const [clickedCell, setClickedCell] = useState<any>(null);

  return (
    <div className={cn("flex flex-row  relative z-30", className)}>
      {matrix.map((row, rowIdx) => (
        <div
          key={`matrix-row-${rowIdx}`}
          className="flex flex-col  relative z-20 border-b"
        >
          {row.map((column, colIdx) => {
            const controls = useAnimation();

            useEffect(() => {
              if (clickedCell) {
                const distance = Math.sqrt(
                  Math.pow(clickedCell[0] - rowIdx, 2) +
                    Math.pow(clickedCell[1] - colIdx, 2)
                );
                controls.start({
                  opacity: [0, 1 - distance * 0.1, 0],
                  transition: { duration: distance * 0.2 },
                });
              }
            }, [clickedCell]);
            return (
              <div
                key={`matrix-col-${colIdx}`}
                className={cn(
                  "bg-transparent border-l border-b border-neutral-600",
                  cellClassName
                )}
                onClick={() => {setClickedCell([rowIdx, colIdx])}}
              >
                <motion.div
                  initial={{opacity: 0}}
                  whileHover={{opacity: [0, 1, 0.5]}}
                  transition={{duration: 0.5,ease: "backOut"}}
                  animate={controls}
                  className="bg-purple-600/30 h-12 w-12"
                ></motion.div>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
};
