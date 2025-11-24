import { cn } from "@/lib/utils"
import React, { useMemo, type ElementType, type ComponentPropsWithoutRef } from "react"

export type StackProps<T extends ElementType = "div"> = {
	as?: T
	gap?:
		| {
				xs?: number
				sm?: number
				md?: number
				lg?: number
				xl?: number
		  }
		| number
	dir?: "row" | "column"
	items?: React.CSSProperties["alignItems"]
	justify?: React.CSSProperties["justifyContent"]
	wrap?: "nowrap" | "wrap" | "wrap-reverse"
	padding?: string
	margin?: string
} & Omit<ComponentPropsWithoutRef<T>, "dir">

export const Stack = <T extends ElementType = "div">({
	as,
	gap,
	dir = "column",
	items,
	justify,
	wrap = "nowrap",
	padding,
	margin,
	className,
	children,
	style,
	...rest
}: StackProps<T>) => {
	const Component = as || "div"
	const gapStyles = useMemo(() => {
		if (typeof gap === "number") {
			return { "--stack-gap": `${gap * 4}px` }
		} else {
			return {
				...(gap?.xs && { "--stack-gap-xs": `${gap.xs * 4}px` }),
				...(gap?.sm && { "--stack-gap-sm": `${gap.sm * 4}px` }),
				...(gap?.md && { "--stack-gap-md": `${gap.md * 4}px` }),
				...(gap?.lg && { "--stack-gap-lg": `${gap.lg * 4}px` }),
				...(gap?.xl && { "--stack-gap-xl": `${gap.xl * 4}px` }),
			}
		}
	}, [gap])

	const gapClasses = useMemo(() => {
		if (typeof gap === "number") {
			return `gap-[var(--stack-gap)]`
		} else {
			return [
				gap?.xs && `gap-[var(--stack-gap-xs)]`,
				gap?.sm && `sm:gap-[var(--stack-gap-sm)]`,
				gap?.md && `md:gap-[var(--stack-gap-md)]`,
				gap?.lg && `lg:gap-[var(--stack-gap-lg)]`,
				gap?.xl && `xl:gap-[var(--stack-gap-xl)]`,
			]
				.filter(Boolean)
				.join(" ")
		}
	}, [gap])

	return (
		<Component
			className={cn("flex", dir === "column" ? "flex-col" : "flex-row", gapClasses, className)}
			style={
				{
					...style,
					...gapStyles,
					alignItems: items,
					justifyContent: justify,
					flexWrap: wrap,
					padding,
					margin,
				} satisfies React.CSSProperties
			}
			{...rest}
		>
			{children}
		</Component>
	)
}
