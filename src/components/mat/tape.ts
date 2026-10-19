// What the recorder plays back when its play key is pressed: the key going down, a few bars of a slow tune
// off tape, with the hiss and the slight wow of tape, and the key coming up.
const TUNE = [220, 261.63, 329.63, 392, 329.63, 261.63, 293.66, 220]
const BEAT = 0.38

let deck: AudioContext | undefined

/** Starts the playback and returns how long it runs, in seconds. */
export const playTape = () => {
  deck ??= new AudioContext()
  void deck.resume()
  const audio = deck
  const start = audio.currentTime + 0.03
  const length = TUNE.length * BEAT + 0.5

  const out = audio.createGain()
  out.gain.value = 0.32
  const warm = audio.createBiquadFilter()
  warm.type = 'lowpass'
  warm.frequency.value = 2100
  warm.connect(out).connect(audio.destination)

  // One buffer of noise serves the hiss and both key clicks.
  const noise = audio.createBuffer(1, audio.sampleRate * (length + 0.3), audio.sampleRate)
  const grains = noise.getChannelData(0)
  for (let i = 0; i < grains.length; i++) grains[i] = Math.random() * 2 - 1
  const hiss = audio.createBufferSource()
  hiss.buffer = noise
  const quiet = audio.createGain()
  quiet.gain.value = 0.035
  hiss.connect(quiet).connect(audio.destination)
  hiss.start(start, 0, length)

  const key = (at: number) => {
    const click = audio.createBufferSource()
    click.buffer = noise
    const snap = audio.createGain()
    snap.gain.setValueAtTime(0.5, at)
    snap.gain.exponentialRampToValueAtTime(0.001, at + 0.05)
    click.connect(snap).connect(audio.destination)
    click.start(at, 0.1, 0.06)
  }
  key(start - 0.02)
  key(start + length)

  const wow = audio.createOscillator()
  wow.frequency.value = 0.8
  const drift = audio.createGain()
  drift.gain.value = 9
  wow.connect(drift)
  wow.start(start)
  wow.stop(start + length)

  TUNE.forEach((pitch, beat) => {
    const at = start + 0.2 + beat * BEAT
    const note = audio.createOscillator()
    note.type = 'triangle'
    note.frequency.value = pitch
    drift.connect(note.detune)
    const held = audio.createGain()
    held.gain.setValueAtTime(0, at)
    held.gain.linearRampToValueAtTime(0.9, at + 0.03)
    held.gain.exponentialRampToValueAtTime(0.001, at + BEAT * 1.6)
    note.connect(held).connect(warm)
    note.start(at)
    note.stop(at + BEAT * 1.7)
  })
  return length + 0.1
}
