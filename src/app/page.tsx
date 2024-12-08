import { Github, Instagram, Twitter } from "lucide-react";
import Link from "next/link";
import { BackgroundCellCore } from "@/components/global/background-ripple-effect";

export default function Home() {

  return (
    <main>
      <div className="relative h-[96vh] bg-[#111111] grid justify-center items-center overflow-hidden">
        <BackgroundCellCore />
        <div className="grid gap-3 z-50">
          <img
            src="/icons/Logo.svg"
            alt=""
            className="phone:w-12 phone:h-12 lg:w-20 lg:h-20 m-auto saturate-[1.25]"
          />
          <div className="flex gap-2 justify-center">
            <h1 className="phone:text-5xl instrument-serif-italic lg:text-7xl font-playfair p-2 my-auto bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-400 to-neutral-500 font-medium tracking-tight">
              Anurag Das
            </h1>
          </div>
          <h1 className="phone:text-sm mb-2 lg:text-xl bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-400 to-neutral-500 text-center tracking-tighter font-medium py-1 opacity-80">
            Soft Engineer building servers and interfaces
          </h1>
          <div className="mx-auto flex gap-4 my-2">
            <Link href="https://github.com/oeuvars" target="_blank">
              <Github className="text-[#505050] animate-when-hovered hover:text-[#606060] w-7 h-7" />
            </Link>
            <Link
              href="https://www.instagram.com/oeuvars/"
              target="_blank"
            >
              <Instagram className="text-[#505050] animate-when-hovered hover:text-[#606060] w-7 h-7" />
            </Link>
            <Link href="https://twitter.com/oeuvars" target="_blank">
              <Twitter className="text-[#505050] animate-when-hovered hover:text-[#606060] w-7 h-7" />
            </Link>
          </div>
        </div>
      </div>
      <div className="bg-[#111111] phone:text-xs lg:text-sm tracking-tight py-5 text-stone-300 flex justify-between px-5">
        <p>2024 &#169;Oeuvars</p>
        <p>Design + Build by Oeuvars</p>
      </div>
    </main>
  );
}
