import { Link, useRouterState } from '@tanstack/react-router'
import { motion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'

import { profile } from '../content'

const STEP = 360 / profile.nav.length

export function Dial() {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const index = Math.max(
    0,
    profile.nav.findIndex((item) => item.to === pathname),
  )
  const [angle, setAngle] = useState(0)
  const current = useRef(0)

  useEffect(() => {
    const target = -index * STEP
    const delta = ((((target - current.current) % 360) + 540) % 360) - 180
    current.current += delta
    setAngle(current.current)
  }, [index])

  return (
    <nav
      aria-label="Pages"
      className="absolute top-[0.7rem] right-[4.6vw] z-30 size-[clamp(7rem,11.5vw,10.8rem)] max-md:right-[3vw]"
    >
      <span aria-hidden className="dial-pointer" />
      <motion.div
        animate={{ rotate: angle }}
        transition={{ type: 'spring', stiffness: 110, damping: 11, mass: 0.9 }}
        className="relative size-full drop-shadow-[0_10px_14px_rgba(0,0,0,0.6)]"
      >
        <img src="/dial.png" alt="" draggable={false} className="absolute inset-0 size-full select-none" />
        {profile.nav.map((item, i) => (
          <Link
            key={item.to}
            to={item.to}
            activeOptions={{ exact: true }}
            aria-label={item.label}
            className="dial-label"
            activeProps={{ className: 'dial-label is-active' }}
            style={{ transform: `rotate(${i * STEP}deg)` }}
          >
            <span>{item.label}</span>
          </Link>
        ))}
      </motion.div>
    </nav>
  )
}
