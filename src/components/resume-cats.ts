import type { Rig } from '../lib/cat-rig/types'

/**
 * How the desk's cats move, by the name of their cut-out (studio/resume/cats.py). Every point is a pixel of the
 * cut-out's picture as cats.py writes it, shadow margin and all, so cutting a cat again means placing its joints again.
 * Cats without a rig lie still.
 */
export const RIGS: Record<string, Rig> = {
  // On its back, paws folded on its chest, tail out across the desk, looking up at the lamp.
  gaze: {
    mood: 'awake',
    parts: {
      head: { kind: 'chain', joints: [[171, 100], [172, 56]], reach: [9, 34], soft: 10, yields: ['pawLeft', 'pawRight'] },
      pawLeft: { kind: 'chain', joints: [[142, 134], [130, 105]], reach: [10, 12], soft: 6 },
      pawRight: { kind: 'chain', joints: [[176, 138], [184, 112]], reach: [10, 12], soft: 6 },
      belly: { kind: 'swell', centre: [152, 176], radii: [58, 68], soft: 14 },
      tail: {
        kind: 'chain',
        joints: [[150, 234], [148, 263], [140, 292], [127, 321], [110, 348]],
        reach: [16, 18, 21, 24, 26],
        soft: 20,
      },
      leg: { kind: 'chain', joints: [[112, 236], [58, 243]], reach: [12, 11], soft: 12 },
      foot: { kind: 'chain', joints: [[184, 234], [198, 212]], reach: [10, 12], soft: 8 },
    },
    breath: 'belly',
    head: 'head',
    tail: 'tail',
    acts: [
      { kind: 'tilt', head: 'head', deg: 17, weight: 3, track: 'front' },
      { kind: 'groom', head: 'head', paws: ['pawLeft', 'pawRight'], bow: 4, reach: [-2, 7], lift: [0, -6], weight: 2, track: 'front' },
      { kind: 'knead', paws: ['pawLeft', 'pawRight'], push: [0, -5], weight: 2, track: 'front' },
      { kind: 'swish', tail: 'tail', deg: 30, weight: 3, track: 'back' },
      { kind: 'flick', tail: 'tail', deg: 16, weight: 2, track: 'back' },
      { kind: 'stretch', part: 'leg', deg: -7, reach: [-6, 0], weight: 1, track: 'back' },
      { kind: 'twitch', part: 'foot', deg: 14, weight: 1, track: 'back' },
    ],
  },
  // Asleep, curled round with its head tucked and its tail along its side.
  curl: {
    mood: 'asleep',
    parts: {
      head: { kind: 'chain', joints: [[102, 142], [122, 66]], reach: [24, 32], soft: 10, yields: ['earUp', 'earSide'] },
      earUp: { kind: 'chain', joints: [[121, 74], [127, 51]], reach: [8, 5], soft: 4 },
      earSide: { kind: 'chain', joints: [[127, 124], [144, 131]], reach: [7, 5], soft: 4 },
      back: { kind: 'swell', centre: [118, 212], radii: [74, 78], soft: 12 },
      foot: { kind: 'chain', joints: [[166, 216], [186, 203]], reach: [9, 10], soft: 6 },
      tail: {
        kind: 'chain',
        joints: [[150, 285], [180, 273], [200, 253], [209, 229], [205, 206]],
        reach: [14, 14, 13, 12, 10],
        soft: 14,
      },
    },
    breath: 'back',
    head: 'head',
    tail: 'tail',
    acts: [
      { kind: 'twitch', part: 'earUp', deg: 22, weight: 3, track: 'front' },
      { kind: 'twitch', part: 'earSide', deg: 24, weight: 2, track: 'front' },
      { kind: 'nestle', head: 'head', deg: 7, weight: 1, track: 'front' },
      { kind: 'flick', tail: 'tail', deg: 14, weight: 3, track: 'back' },
      { kind: 'twitch', part: 'foot', deg: 12, weight: 2, track: 'back' },
    ],
  },
  // Sitting with its tail wrapped round its feet, looking out. Its head is a tenth of an em from the folder lying over
  // the desk's edge to its left, so the head goes over that way only a little.
  cap: {
    mood: 'awake',
    parts: {
      head: { kind: 'chain', joints: [[93, 114], [88, 58]], reach: [24, 46], soft: 12, yields: ['paw'] },
      paw: { kind: 'chain', joints: [[100, 160], [72, 172]], reach: [10, 10], soft: 6 },
      chest: { kind: 'swell', centre: [165, 162], radii: [62, 56], soft: 12 },
      tail: {
        kind: 'chain',
        joints: [[222, 198], [233, 232], [210, 262], [165, 272], [125, 264], [90, 250]],
        reach: [12, 14, 16, 17, 16, 14],
        soft: 14,
      },
    },
    breath: 'chest',
    head: 'head',
    tail: 'tail',
    acts: [
      { kind: 'tilt', head: 'head', deg: 18, weight: 3, track: 'front', side: 1 },
      { kind: 'tilt', head: 'head', deg: 7, weight: 1, track: 'front', side: -1 },
      { kind: 'look', head: 'head', deg: 6, reach: [5, 0], weight: 2, track: 'front', side: 1 },
      { kind: 'groom', head: 'head', paws: ['paw'], bow: 5, reach: [2, 12], lift: [7, -8], weight: 2, track: 'front' },
      { kind: 'flick', tail: 'tail', deg: 18, weight: 3, track: 'back' },
    ],
  },
}
