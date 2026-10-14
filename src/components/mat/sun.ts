import type { Light } from '../../types'

const LATITUDE = 22.5726
const LONGITUDE = 88.3639
const OFFSET_MINUTES = 330
const RAD = Math.PI / 180
const DAY_MS = 86_400_000

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))
const smooth = (from: number, to: number, value: number) => {
  const t = clamp((value - from) / (to - from), 0, 1)
  return t * t * (3 - 2 * t)
}

/** Solar altitude and azimuth over Kolkata, in radians. Azimuth runs from south towards west. */
function sunPosition(date: Date) {
  const days = date.getTime() / DAY_MS - 0.5 + 2440588 - 2451545
  const anomaly = RAD * (357.5291 + 0.98560028 * days)
  const centre = RAD * (1.9148 * Math.sin(anomaly) + 0.02 * Math.sin(2 * anomaly) + 0.0003 * Math.sin(3 * anomaly))
  const longitude = anomaly + centre + RAD * 102.9372 + Math.PI
  const obliquity = RAD * 23.4397
  const declination = Math.asin(Math.sin(obliquity) * Math.sin(longitude))
  const ascension = Math.atan2(Math.sin(longitude) * Math.cos(obliquity), Math.cos(longitude))
  const phi = RAD * LATITUDE
  const hour = RAD * (280.16 + 360.9856235 * days) + RAD * LONGITUDE - ascension
  return {
    altitude: Math.asin(Math.sin(phi) * Math.sin(declination) + Math.cos(phi) * Math.cos(declination) * Math.cos(hour)),
    azimuth: Math.atan2(Math.sin(hour), Math.cos(hour) * Math.sin(phi) - Math.tan(declination) * Math.cos(phi)),
  }
}

/** The same day in Kolkata as now, at that minute of it. */
export function atKolkataMinute(now: Date, minute: number) {
  const current = (now.getUTCHours() * 60 + now.getUTCMinutes() + OFFSET_MINUTES) % 1440
  return new Date(now.getTime() + (minute - current) * 60_000)
}

export function lightAt(date: Date): Light {
  const elevation = sunPosition(date).altitude / RAD
  const day = smooth(-6, 6, elevation)
  return { day, warmth: day * (1 - smooth(6, 38, elevation)) }
}
