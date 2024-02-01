"use client";

import React, { useEffect, useRef, useState } from "react";
import { AnimationControls, motion, useAnimation } from "framer-motion";
import { cn } from "@/lib/utils";
import { Github, Linkedin, Twitter } from "lucide-react";
import Link from "next/link";
import toast, { Toaster } from "react-hot-toast";

export const BackgroundCellAnimation = () => {
  const [email, setEmail] = useState('');
  const [isValidEmail, setIsValidEmail] = useState(false);
  const variants = {
    hidden: { opacity: 0.5, x: 0, y: 200 },
    enter: { opacity: 1, x: 0, y: 0},
  }
  const handleClick = () => {
    if (isValidEmail) {
      toast.success("Subscribed to the Oeuletter", {
        style: {
          border: "2px solid rgba(255, 255, 255, 0.1)",
          padding: "10px",
          color: "#fff",
          backgroundColor: "rgba(0, 0, 0, 0.1)",
          backdropFilter: "blur(10px)",
          fontSize: '1.1em',
          minWidth: "10em",
        },
        iconTheme: {
          primary: "#000",
          secondary: "#fff",
        },
      });
      setEmail('')
    } else {
      toast.error("Not a valid email", {
        style: {
          border: "2px solid rgba(255, 255, 255, 0.1)",
          padding: "10px",
          color: "#fff",
          backgroundColor: "rgba(0, 0, 0, 0.1)",
          backdropFilter: "blur(10px)",
          fontSize: '1.1em',
          minWidth: "10em",
        },
        iconTheme: {
          primary: "#000",
          secondary: "#fff",
        },
      });
    }

  }
  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const inputEmail = event.target.value;
    setEmail(inputEmail);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    setIsValidEmail(emailRegex.test(inputEmail));
  };
return (
  <div className="relative h-screen bg-[#111111] grid justify-center items-center overflow-hidden">
    <BackgroundCellCore />
    <div className="grid gap-3 z-50">
      <div className="flex gap-2 justify-center">
         <img src="/icons/Logo.svg" alt="" className="phone:w-12 phone:h-12 lg:w-20 lg:h-20 my-auto"/>
         <h1 className="phone:text-5xl lg:text-7xl font-playfair p-1 my-auto bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-400 to-neutral-500 tracking-tighter">Oeuvars</h1>
      </div>
      <h1 className="phone:text-2xl lg:text-3xl bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-300 to-neutral-400 tracking-tight text-center font-parisienne py-1">Anurag Das. Lemme land g.</h1>
      <div className="flex w-full phone:gap-2 lg:gap-0 mt-2">
        <input
          className={`bg-[#222222] text-[#FAFAFA] px-6 py-3 w-full rounded-md outline-none focus:outline-2 focus:outline focus:outline-[#333333] ${
            isValidEmail ? '' : 'border-red-500'
          }`}
          placeholder="something@gmail.com"
          type="email"
          id="email"
          name="email"
          onChange={handleEmailChange}
          value={email}
          required
        />
        <Toaster position="top-center"/>
        <button className="-ml-10" onClick={handleClick}>
          <img src="/icons/arrow.svg" alt="" className="w-7 h-7 my-auto"/>
        </button>
      </div>
      <motion.div className="mx-auto flex gap-4 my-2">
        <Link href="https://github.com/oeuvars" target="_blank">
          <Github className="text-[#505050] w-7 h-7"/>
        </Link>
        <Link href="https://www.linkedin.com/in/anurag-das-00075925b/" target="_blank">
          <Linkedin className="text-[#505050] w-7 h-7"/>
        </Link>
        <Link href="https://twitter.com/oeuvars" target="_blank">
          <Twitter className="text-[#505050] w-7 h-7"/>
        </Link>
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

function CellAnimation(clickedCell: [number, number], rowIdx: number, colIdx: number) {
  const controls = useAnimation();

  useEffect(() => {
    if (clickedCell) {
      const distance = Math.sqrt(
        Math.pow(clickedCell[0] - rowIdx, 2) + Math.pow(clickedCell[1] - colIdx, 2)
      );
      controls.start({
        opacity: [0, 1 - distance * 0.1, 0],
        transition: { duration: distance * 0.2 },
      });
    }
  }, [clickedCell, rowIdx, colIdx, controls]);

  return controls;
}

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
            const handleCellClick = () => {
              setClickedCell([rowIdx, colIdx]);
            };

            const controls = CellAnimation(clickedCell, rowIdx, colIdx);
            return (
              <div
                key={`matrix-col-${colIdx}`}
                className={cn(
                  "bg-transparent border-l border-b border-neutral-600",
                  cellClassName
                )}
                onClick={handleCellClick}
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
