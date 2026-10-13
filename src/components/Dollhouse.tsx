import type { Role } from '../types'

type DollhouseProps = {
  roles: Role[]
}

/** The render's size in pixels. */
const WIDTH = 2600
const HEIGHT = 1470

/**
 * The building (studio/dollhouse.py): a model of a house cut open at the front, standing at night in the
 * snow among pines, with mountains behind. There is a floor for each job, newest at the top, and over each
 * a painted board with the company on it in a lit sign. The picture is far wider than the sheet, which is
 * about the house's width, and the page shows as much of the country either side as it has room for: the
 * panel's own edges are where the picture stops. It has no sky of its own, so the page's night shows there,
 * and it comes up behind the masthead, as a poster's picture does. The lettering is in the picture, so the
 * jobs are listed again here for whoever cannot see it.
 */
export function Dollhouse({ roles }: DollhouseProps) {
  return (
    <>
      <img
        src="/objects/dollhouse.webp"
        alt="A doll's house with its front off, lit up at night in the snow, with pines either side and mountains behind. It has three floors under a slate roof: a parcel room shelved with pink cake boxes, a banking hall with marble columns and a vault, and a dispatch room stacked with trunks. A lit sign over each floor names a company."
        width={WIDTH}
        height={HEIGHT}
        draggable={false}
        className="relative left-1/2 -mt-[8cqw] block h-auto w-[187cqw] max-w-none -translate-x-1/2 select-none md:-mt-[min(8cqw,6.4vh)] md:w-[min(187cqw,150vh)]"
      />
      <ol className="sr-only">
        {roles.map((role) => (
          <li key={`${role.org}-${role.period}`}>
            {role.org}, {role.period}
          </li>
        ))}
      </ol>
    </>
  )
}
