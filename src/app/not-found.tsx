import { BackgroundCellCore } from "@/components/global/background-ripple-effect";
import { Button } from "@/components/ui/button";
import { Stack } from "@/components/stack";
import { Typography } from "@/components/typography";
import Link from "next/link";
import { FC, Fragment } from "react";

const page: FC = () => {
   return (
      <Fragment>
         <Stack className="relative h-[95vh] bg-[#111111] justify-center items-center overflow-hidden">
            <BackgroundCellCore />
            <Stack items="center" justify="center" className="z-50 w-full">
               <Stack dir="row" className="mt-8">
                  <Typography.H1 className="text-neutral-50 font-bold my-auto">4</Typography.H1>
                  <Stack className='my-auto'>
                     <img src="/assets/0.svg" alt="" className="phone:size-12 lg:size-16 my-auto" />
                  </Stack>
                  <Typography.H1 className="text-neutral-50 font-bold my-auto">4</Typography.H1>
               </Stack>
               <Typography.P className="phone:text-sm lg:text-lg mt-5 text-neutral-300 font-light tracking-tight">You just got lost in a beautiful space...</Typography.P>
               <Button className="bg-neutral-900 mt-5 px-7 py-5 rounded-md phone:text-sm tablet:text-base text-neutral-300">
                  <Link href="/">Home &nbsp;-&gt;</Link>
               </Button>
            </Stack>
         </Stack>
         <Stack dir="row" justify="space-between" className="bg-[#111111] phone:text-xs lg:text-sm tracking-tight text-stone-300 px-5">
            <Typography.P>{new Date().getFullYear()} &#169;Oeuvars</Typography.P>
            <Typography.P>Design + Build by Oeuvars</Typography.P>
         </Stack>
      </Fragment>
   );
};

export default page;
