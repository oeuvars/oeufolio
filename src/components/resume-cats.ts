import type { Rig, Spring } from '../lib/cat-rig/types'

/**
 * How the desk's cats move, by the name of their cut-out (studio/resume/cats.py). Every point is a pixel of the
 * cut-out's picture as cats.py writes it, shadow margin and all, so cutting a cat again means placing its joints again.
 * Cats without a rig lie still.
 *
 * The springs and acts follow footage of real cats, tracked frame by frame: a head turns fastest half a second in and
 * has settled by about a second and a half; a lying cat's tail sweeps over a second or two, its tip trailing; a
 * sleeping head barely shifts.
 */

// An awake head, a sleeping one, a paw, a leg stretched slowly, a quick foot or ear.
const HEAD: Spring = { rate: 3.2, damping: 1 }
const DOZING: Spring = { rate: 1.8, damping: 1 }
const PAW: Spring = { rate: 10, damping: 0.8 }
const LEG: Spring = { rate: 4, damping: 1 }
const QUICK: Spring = { rate: 18, damping: 0.7 }
// A tail laid along the desk: slow at the root, the tip slower and looser, so it trails and swings through.
const TAIL: Spring = { rate: 3.2, damping: 0.95, tip: { rate: 2.2, damping: 0.6 } }

export const RIGS: Record<string, Rig> = {
  // On its back, paws folded on its chest, tail out across the desk, looking up at the lamp.
  gaze: {
    mood: 'awake',
    parts: {
      head: { kind: 'chain', joints: [[171, 100], [172, 56]], reach: [9, 34], soft: 10, spring: HEAD, yields: ['pawLeft', 'pawRight'] },
      pawLeft: { kind: 'chain', joints: [[142, 134], [130, 105]], reach: [10, 12], soft: 6, spring: PAW },
      pawRight: { kind: 'chain', joints: [[176, 138], [184, 112]], reach: [10, 12], soft: 6, spring: PAW },
      belly: { kind: 'swell', centre: [152, 176], radii: [58, 68], soft: 14, across: 0 },
      tail: {
        kind: 'chain',
        joints: [[150, 234], [148, 263], [140, 292], [127, 321], [110, 348]],
        reach: [16, 18, 21, 24, 26],
        soft: 20,
        spring: TAIL,
      },
      leg: { kind: 'chain', joints: [[112, 236], [58, 243]], reach: [12, 11], soft: 12, spring: LEG },
      foot: { kind: 'chain', joints: [[184, 234], [198, 212]], reach: [10, 12], soft: 8, spring: QUICK },
    },
    breath: 'belly',
    acts: [
      { kind: 'look', head: 'head', roll: [-14, 14], reach: [3, 1], weight: 4, track: 'front' },
      {
        kind: 'groom',
        head: 'head',
        paws: ['pawLeft', 'pawRight'],
        bow: 3,
        reach: [-1, 6],
        lift: [0, -6],
        roll: 7,
        strokes: [5, 10],
        weight: 1,
        track: 'front',
      },
      { kind: 'knead', paws: ['pawLeft', 'pawRight'], push: [0, -4], weight: 1, track: 'front' },
      { kind: 'sweep', tail: 'tail', deg: 14, curl: 22, weight: 3, track: 'back' },
      { kind: 'flick', tail: 'tail', deg: 18, weight: 3, track: 'back' },
      { kind: 'stretch', part: 'leg', deg: -6, reach: [-5, 0], weight: 0.5, track: 'back' },
      { kind: 'twitch', part: 'foot', deg: 12, weight: 1, track: 'back' },
    ],
  },
  // Asleep, curled round with its head tucked and its tail along its side.
  curl: {
    mood: 'asleep',
    parts: {
      head: { kind: 'chain', joints: [[102, 142], [122, 66]], reach: [24, 32], soft: 10, spring: DOZING },
      earUp: { kind: 'chain', joints: [[121, 74], [127, 51]], reach: [8, 5], soft: 4, spring: QUICK },
      earSide: { kind: 'chain', joints: [[127, 124], [144, 131]], reach: [7, 5], soft: 4, spring: QUICK },
      back: { kind: 'swell', centre: [118, 212], radii: [74, 78], soft: 12, across: 0 },
      foot: { kind: 'chain', joints: [[166, 216], [186, 203]], reach: [9, 10], soft: 6, spring: QUICK },
      tail: {
        kind: 'chain',
        joints: [[150, 285], [180, 273], [200, 253], [209, 229], [205, 206]],
        reach: [14, 14, 13, 12, 10],
        soft: 14,
        spring: TAIL,
      },
    },
    breath: 'back',
    acts: [
      { kind: 'twitch', part: 'earUp', deg: 25, weight: 3, track: 'front' },
      { kind: 'twitch', part: 'earSide', deg: 25, weight: 2, track: 'front' },
      { kind: 'settle', head: 'head', deg: 4, weight: 1, track: 'front' },
      { kind: 'flick', tail: 'tail', deg: 12, weight: 3, track: 'back' },
      { kind: 'sweep', tail: 'tail', deg: 2, curl: 8, weight: 1, track: 'back' },
      { kind: 'twitch', part: 'foot', deg: 10, weight: 1, track: 'back' },
    ],
  },
  // Sitting with its tail wrapped round its feet, looking out. Its head is a tenth of an em from the folder lying over
  // the desk's edge to its left, so the head goes over that way only a little. Its paw is on the ground, too far from
  // its mouth for the photograph to be bent into washing it.
  cap: {
    mood: 'awake',
    parts: {
      head: { kind: 'chain', joints: [[93, 114], [88, 58]], reach: [24, 46], soft: 12, spring: HEAD },
      earLeft: { kind: 'chain', joints: [[63, 80], [51, 51]], reach: [9, 5], soft: 4, spring: QUICK },
      earRight: { kind: 'chain', joints: [[108, 77], [119, 52]], reach: [9, 5], soft: 4, spring: QUICK },
      chest: { kind: 'swell', centre: [165, 162], radii: [62, 56], soft: 12, across: 0 },
      tail: {
        kind: 'chain',
        joints: [[222, 198], [233, 232], [210, 262], [165, 272], [125, 264], [90, 250]],
        reach: [12, 14, 16, 17, 16, 14],
        soft: 14,
        spring: TAIL,
      },
    },
    breath: 'chest',
    acts: [
      { kind: 'look', head: 'head', roll: [-6, 16], reach: [4, 1], weight: 4, track: 'front' },
      { kind: 'twitch', part: 'earLeft', deg: -22, weight: 1, track: 'front' },
      { kind: 'twitch', part: 'earRight', deg: 22, weight: 1, track: 'front' },
      { kind: 'flick', tail: 'tail', deg: 20, weight: 3, track: 'back' },
      { kind: 'sweep', tail: 'tail', deg: 1.5, curl: 14, weight: 1, track: 'back' },
    ],
  },
}
