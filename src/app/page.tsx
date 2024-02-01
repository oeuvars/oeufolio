import { BackgroundCellAnimation } from "@/components/BackgroundRippleEffect";

export default function Home() {
  return (
    <main className="">
      <BackgroundCellAnimation />
      <div className="bg-[#111111] phone:text-xs lg:text-sm tracking-tight py-5 text-stone-300 flex justify-between px-5">
        <p>2024 &#169;Oeuvars</p>
        <p>Design + Build by Oeuvars</p>
      </div>
    </main>
  );
}
