import type { Role } from '../types'

type DollhouseProps = {
  roles: Role[]
}

/** The render's size in pixels. */
const WIDTH = 1600
const HEIGHT = 1697

/**
 * The building (studio/dollhouse.py): a model of a house cut open at the front, a floor for each job,
 * newest at the top. Over each floor a painted board runs across the front, as over a shop, with the job
 * fixed to it in raised gilt letters under a row of lamps. The lettering is in the picture, so the jobs
 * are listed again here for whoever cannot see it.
 */
export function Dollhouse({ roles }: DollhouseProps) {
  return (
    <>
      <img
        src="/objects/dollhouse.webp"
        alt="A doll's house with its front off, three floors under a slate roof: a parcel room shelved with pink cake boxes, a banking hall with marble columns and a vault, and a dispatch room stacked with trunks. A signboard over each floor names a company."
        width={WIDTH}
        height={HEIGHT}
        draggable={false}
        className="block h-auto w-full select-none"
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
