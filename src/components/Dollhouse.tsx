import type { Role } from '../types'

type DollhouseProps = {
  roles: Role[]
}

/** The render's width and its height, in the model's metres. */
const WIDTH = 13.9
const HEIGHT = 14.75

/**
 * Where the middle of each floor's board falls down the render, top floor first, as a percentage of its
 * height, and how far in from either side a board starts. They come from the measures in
 * studio/dollhouse.py.
 */
const boards = [21.86, 47.29, 72.71]
const INSET = 4.2

/**
 * The building (studio/dollhouse.py): a model of a house cut open at the front, a floor for each job,
 * newest at the top. Over each floor a painted board runs across the front, as over a shop, and the job is
 * lettered on it in gilt: the company in the middle, and the month it began and the month it ended at
 * either end. The model has three floors, so it shows the three newest jobs.
 */
export function Dollhouse({ roles }: DollhouseProps) {
  return (
    <div className="@container relative">
      <img
        src="/objects/dollhouse.webp"
        alt="A doll's house with its front off, three floors under a slate roof: a parcel room shelved with pink cake boxes, a banking hall with marble columns and a vault, and a dispatch room stacked with trunks."
        width={1600}
        height={Math.round((1600 * HEIGHT) / WIDTH)}
        draggable={false}
        className="block h-auto w-full select-none"
      />
      <ol>
        {roles.slice(0, boards.length).map((role, i) => {
          const [from, to] = role.period.split(' to ')

          return (
            <li
              key={`${role.org}-${role.period}`}
              className="absolute mt-[0.45cqw] grid -translate-y-1/2 grid-cols-[1fr_auto_1fr] items-center gap-[2cqw] px-[3cqw] text-[#ecc66a] uppercase"
              style={{ top: `${boards[i]}%`, left: `${INSET}%`, right: `${INSET}%` }}
            >
              <span className="text-[1.75cqw] leading-none font-semibold tracking-[0.24em]">{from}</span>
              <h3 className="text-[3.7cqw] leading-none font-bold tracking-[0.12em] [text-shadow:0_0.04em_0_rgb(0_0_0/0.35)]">{role.org}</h3>
              <span className="text-right text-[1.75cqw] leading-none font-semibold tracking-[0.24em]">
                {to && <span className="sr-only">to </span>}
                {to}
              </span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
