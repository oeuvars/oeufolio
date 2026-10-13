import type { Role } from '../types'

type DollhouseProps = {
  roles: Role[]
}

/** The render's size in pixels. */
const WIDTH = 1600
const HEIGHT = 1469

/**
 * The building (studio/dollhouse.py): a model of a house cut open at the front, standing at night in the
 * snow among pines, with mountains behind. There is a floor for each job, newest at the top, and over each
 * a painted board with the company on it in a lit sign. The picture has no sky of its own: the page's night
 * shows there. It is wider than the sheet, which is the house's width, and it comes up behind the masthead,
 * as a poster's picture does. It fades out at its own edges, and again at the edges of the room the page
 * gives it, so that wherever it stops it stops in the dark and never at a line. The lettering is in the
 * picture, so the jobs are listed again here for whoever cannot see it.
 */
export function Dollhouse({ roles }: DollhouseProps) {
  const fade = '[mask-composite:intersect] [mask-image:linear-gradient(to_right,transparent,#000_5%,#000_95%,transparent),linear-gradient(to_top,transparent,#000_6%)]'

  return (
    <>
      <div className={`-mt-[8cqw] overflow-hidden @md/box:-mt-[min(8cqw,5.8vh)] ${fade}`}>
        <img
          src="/objects/dollhouse.webp"
          alt="A doll's house with its front off, lit up at night in the snow, with pines either side and mountains behind. It has three floors under a slate roof: a parcel room shelved with pink cake boxes, a banking hall with marble columns and a vault, and a dispatch room stacked with trunks. A lit sign over each floor names a company."
          width={WIDTH}
          height={HEIGHT}
          draggable={false}
          className={`relative left-1/2 block h-auto w-[115cqw] max-w-none -translate-x-1/2 select-none @md/box:w-[min(115cqw,84vh)] ${fade}`}
        />
      </div>
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
