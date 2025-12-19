import Link from "next/link";
import { BackgroundCellCore } from "@/components/global/background-ripple-effect";
import {
  IconBrandGithub,
  IconBrandInstagram,
  IconBrandX,
} from "@tabler/icons-react";
import { Fragment } from "react";
import { Stack } from "@/components/stack";
import { Typography } from "@/components/typography";
import CenterUnderline from "@/components/fancy/text/underline-center";

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
          <Stack dir="row" items="center" gap={1}>
            <Typography.Small className="gradient-text text-center opacity-80">Soft Engineer building servers and interfaces</Typography.Small>
            <CenterUnderline>
              <Link className="flex items-center" href="https://cybership.io" target="_blank">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="inline align-middle my-auto"
                >
                  <defs>
                    <linearGradient id="atGradient" x1="0%" y1="100%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#e5e5e5" />
                      <stop offset="50%" stopColor="#a8a29e" />
                      <stop offset="100%" stopColor="#737373" />
                    </linearGradient>
                  </defs>
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M16.5485 20.9074C16.7993 21.3985 16.6058 22.0046 16.0939 22.2098C13.9858 23.0552 11.6589 23.2302 9.43437 22.6966C6.885 22.0852 4.63785 20.5833 3.09784 18.4616C1.55783 16.3399 0.82623 13.7379 1.03488 11.1246C1.24352 8.51121 2.37869 6.0583 4.23584 4.20784C6.09298 2.35738 8.54997 1.23105 11.1641 1.03182C13.7782 0.832594 16.3775 1.57356 18.4936 3.12121C20.6097 4.66885 22.1035 6.9214 22.7058 9.47296C22.9026 10.3069 23 11.1549 23 12L23 12.0022C22.9999 12.5715 22.9555 13.1396 22.8676 13.7012C22.5877 15.7731 21.7158 19 19 19C16.6669 19 15.889 17.6669 15.6297 16.778C14.6219 17.5448 13.3641 18 12 18C8.68629 18 6 15.3137 6 12C6 8.68629 8.68629 6 12 6C15.3137 6 18 8.68629 18 12C18 12 18 14 17.9985 16C18 17 18.5 17 18.5 17C19.427 17 20.0112 16.2367 20.3791 15.3067C20.3882 15.2749 20.3987 15.2434 20.4106 15.2122C20.4524 15.1026 20.4921 14.9924 20.5296 14.8815C20.9613 13.5182 21 12 21 12H21.0031C21.0031 11.3083 20.9234 10.6143 20.7623 9.93171C20.2694 7.84334 19.0467 5.99971 17.3148 4.73301C15.5828 3.46632 13.4554 2.85986 11.3158 3.02292C9.17626 3.18599 7.1653 4.10785 5.64529 5.62239C4.12529 7.13693 3.19619 9.14455 3.02542 11.2835C2.85465 13.4224 3.45343 15.5521 4.71388 17.2886C5.97433 19.0251 7.81354 20.2544 9.90012 20.7548C11.6616 21.1773 13.5015 21.057 15.1819 20.4221C15.6977 20.2273 16.2977 20.4164 16.5485 20.9074ZM7.99803 12C7.99803 14.2102 9.78977 16.002 12 16.002C14.2102 16.002 16.002 14.2102 16.002 12C16.002 9.78978 14.2102 7.99803 12 7.99803C9.78977 7.99803 7.99803 9.78978 7.99803 12Z"
                    fill="url(#atGradient)"
                  />
                </svg>
                <Typography.Small className="gradient-text text-center opacity-80">Cybership</Typography.Small>
              </Link>
            </CenterUnderline>
          </Stack>
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
