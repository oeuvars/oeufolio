import Link from "next/link";
import { BackgroundCellCore } from "@/components/global/background-ripple-effect";
import {
  IconBrandGithub,
  IconBrandInstagram,
  IconBrandX,
} from "@tabler/icons-react";
import { GlitchText } from "../../components/text/glitch-text";
import { Fragment } from "react";
import { Stack } from "@/components/stack";
import { Typography } from "@/components/typography";

export default function Home() {
  return (
    <Fragment>
      <Stack
        dir="column"
        justify="center"
        items="center"
        className="h-[93vh] overflow-hidden relative"
      >
        <BackgroundCellCore />
        <Stack gap={3} className="z-50">
          <img
            src="/icons/Logo.svg"
            alt=""
            className="phone:size-12 lg:size-20 m-auto saturate-[1.25]"
          />
          <Typography.H1 className="text-center gradient-text font-instrument-serif italic">
            Anurag Das
          </Typography.H1>
          <Typography.Small className="gradient-text text-center opacity-80">
            Soft Engineer building servers and interfaces
          </Typography.Small>
          <Link href="https://cybership.io" target="_blank">
            <GlitchText
              text="@Cybership"
              starCount={0}
              className="z-50 phone:text-base lg:text-2xl font-medium"
            />
          </Link>
          <Stack dir="row" gap={4} className="mx-auto my-2">
            <Link href="https://github.com/oeuvars" target="_blank">
              <IconBrandGithub className="text-[#505050] animate-when-hovered hover:text-[#606060] size-7" />
            </Link>
            <Link href="https://www.instagram.com/oeuvars/" target="_blank">
              <IconBrandInstagram className="text-[#505050] animate-when-hovered hover:text-[#606060] size-7" />
            </Link>
            <Link href="https://twitter.com/oeuvars" target="_blank">
              <IconBrandX className="text-[#505050] animate-when-hovered hover:text-[#606060] size-7" />
            </Link>
          </Stack>
        </Stack>
      </Stack>
      <Stack
        dir="row"
        justify="space-between"
        className="bg-[#111111] font-medium phone:text-xs lg:text-sm tracking-tight py-5 text-stone-300 px-5"
      >
        <Typography.P>{new Date().getFullYear()} &#169;Oeuvars</Typography.P>
        <Typography.P>Design + Build by Oeuvars</Typography.P>
      </Stack>
    </Fragment>
  );
}
