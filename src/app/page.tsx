import { Github, Linkedin, Twitter } from "lucide-react";
import Link from "next/link";
import { BackgroundCellCore } from "@/components/global/background-ripple-effect";
import Input from "@/components/global/hero-input";

export default function Home() {

  return (
    <main>
      <div className="relative h-screen bg-[#111111] grid justify-center items-center overflow-hidden">
        <BackgroundCellCore />
        <div className="grid gap-3 z-50">
          <div className="flex gap-2 justify-center">
            <img
              src="/icons/Logo.svg"
              alt=""
              className="phone:w-12 phone:h-12 lg:w-20 lg:h-20 my-auto"
            />
            <h1 className="phone:text-5xl lg:text-7xl font-playfair p-1 my-auto bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-400 to-neutral-500 tracking-tighter">
              Oeuvars
            </h1>
          </div>
          <h1 className="phone:text-2xl lg:text-3xl bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 via-stone-300 to-neutral-400 tracking-tight text-center font-parisienne py-1">
            Anurag lemme land g.
          </h1>
          <div className="flex w-full phone:gap-2 lg:gap-0 mt-2">
            <Input />
          </div>
          <div className="mx-auto flex gap-4 my-2">
            <Link href="https://github.com/oeuvars" target="_blank">
              <Github className="text-[#505050] animate-when-hovered hover:text-[#606060] w-7 h-7" />
            </Link>
            <Link
              href="https://www.linkedin.com/in/anurag-das-00075925b/"
              target="_blank"
            >
              <Linkedin className="text-[#505050] animate-when-hovered hover:text-[#606060] w-7 h-7" />
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
