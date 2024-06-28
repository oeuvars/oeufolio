import { BackgroundCellCore } from "@/components/global/background-ripple-effect";
import { Button } from "@nextui-org/button";
import { Image } from "@nextui-org/image";
import Link from "next/link";
import { FC } from "react";

const page: FC = () => {
   return (
      <section>
         <div className="relative h-[95vh] bg-[#111111] grid justify-center items-center overflow-hidden">
            <BackgroundCellCore />
            <div className="flex flex-col justify-center items-center z-50 w-full">
               <div className="flex gap-2 mt-8">
                  <h1 className="font-bold phone:text-6xl lg:text-9xl text-neutral-50">4</h1>
                  <div className='my-auto'>
                     <Image src="/assets/0.svg" alt="" className="phone:w-12 phone:h-12 lg:w-24 lg:h-24 my-auto" />
                  </div>
                  <h1 className="font-bold phone:text-6xl lg:text-9xl text-neutral-50">4</h1>
               </div>
               <p className="phone:text-sm lg:text-lg mt-5 text-neutral-300 font-light tracking-tight">You just got lost in a beautiful space...</p>
               <Button radius='sm' className="bg-neutral-900 mt-5 px-7 py-5 rounded-md phone:text-sm tablet:text-base text-neutral-300">
                  <Link href="/">Home &nbsp;-&gt;</Link>
               </Button>
            </div>
         </div>
         <div className="bg-[#111111] phone:text-xs lg:text-sm tracking-tight py-5 text-stone-300 flex justify-between px-5">
            <p>2024 &#169;Oeuvars</p>
            <p>Design + Build by Oeuvars</p>
         </div>
      </section>
   );
};

export default page;
