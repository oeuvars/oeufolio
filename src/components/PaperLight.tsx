import { useEffect, useRef } from 'react'
import { Mesh, Program, Renderer, Texture, Triangle } from 'ogl'

const vertex = /* glsl */ `
  attribute vec2 position;
  attribute vec2 uv;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position, 0.0, 1.0);
  }
`

const fragment = /* glsl */ `
  precision highp float;
  uniform sampler2D uHeight;
  uniform vec2 uTexel;
  uniform vec2 uCover;
  uniform vec2 uLight;
  uniform float uAspect;
  uniform float uPower;
  uniform float uLoaded;
  varying vec2 vUv;

  float height(vec2 uv) {
    return texture2D(uHeight, uv).r;
  }

  void main() {
    if (uLoaded < 0.5) {
      gl_FragColor = vec4(vec3(0.5), 1.0);
      return;
    }
    vec2 uv = (vUv - 0.5) * uCover + 0.5;
    float dx = height(uv + vec2(uTexel.x, 0.0)) - height(uv - vec2(uTexel.x, 0.0));
    float dy = height(uv + vec2(0.0, uTexel.y)) - height(uv - vec2(0.0, uTexel.y));
    vec3 normal = normalize(vec3(-dx * 3.0, -dy * 3.0, 1.0));

    vec2 toLight = uLight - vUv;
    toLight.x *= uAspect;
    float dist = length(toLight);
    vec3 lightDir = normalize(vec3(toLight, 0.32));

    float falloff = 1.0 / (1.0 + dist * dist * 5.0);
    float relief = (dot(normal, lightDir) - lightDir.z) * falloff * 1.5;
    float pool = falloff * 0.1;
    gl_FragColor = vec4(vec3(0.5 + (relief + pool) * uPower), 1.0);
  }
`

const HEIGHT_MAP = '/paper-height.jpg'
const MAP_ASPECT = 1920 / 1200

export function PaperLight() {
  const host = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const container = host.current
    if (!container) return

    const renderer = new Renderer({ alpha: false, dpr: 1 })
    const gl = renderer.gl
    const canvas = gl.canvas as HTMLCanvasElement
    canvas.style.width = '100%'
    canvas.style.height = '100%'
    container.appendChild(canvas)

    const texture = new Texture(gl, { generateMipmaps: false })
    const program = new Program(gl, {
      vertex,
      fragment,
      uniforms: {
        uHeight: { value: texture },
        uTexel: { value: [1 / 1920, 1 / 1200] },
        uCover: { value: [1, 1] },
        uLight: { value: [0.2, 0.82] },
        uAspect: { value: 1 },
        uPower: { value: 1 },
        uLoaded: { value: 0 },
      },
    })
    const mesh = new Mesh(gl, { geometry: new Triangle(gl), program })

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const light = { x: 0.2, y: 0.82 }
    const target = { x: 0.2, y: 0.82 }
    let pointerSeen = false
    let frame = 0
    let disposed = false

    const resize = () => {
      const w = window.innerWidth
      const h = window.innerHeight
      renderer.setSize(w, h)
      const viewAspect = w / h
      program.uniforms.uAspect.value = viewAspect
      program.uniforms.uCover.value =
        viewAspect > MAP_ASPECT ? [1, MAP_ASPECT / viewAspect] : [viewAspect / MAP_ASPECT, 1]
    }

    const onPointer = (event: PointerEvent) => {
      if (event.pointerType === 'touch') return
      pointerSeen = true
      target.x = event.clientX / window.innerWidth
      target.y = 1 - event.clientY / window.innerHeight
    }

    const draw = (time: number) => {
      if (disposed) return
      const t = time / 1000
      if (!pointerSeen && !reduced) {
        target.x = 0.2 + 0.04 * Math.sin(t * 0.3)
        target.y = 0.82 + 0.03 * Math.cos(t * 0.4)
      }
      light.x += (target.x - light.x) * 0.08
      light.y += (target.y - light.y) * 0.08
      program.uniforms.uLight.value = [light.x, light.y]
      program.uniforms.uPower.value = reduced
        ? 1
        : 1 + 0.04 * Math.sin(t * 7.3) + 0.03 * Math.sin(t * 13.1)
      renderer.render({ scene: mesh })
      if (!reduced) frame = requestAnimationFrame(draw)
    }

    const image = new Image()
    image.onload = () => {
      texture.image = image
      program.uniforms.uTexel.value = [1 / image.naturalWidth, 1 / image.naturalHeight]
      program.uniforms.uLoaded.value = 1
      if (reduced) draw(0)
    }
    image.src = HEIGHT_MAP

    resize()
    window.addEventListener('resize', resize)
    window.addEventListener('pointermove', onPointer)
    frame = requestAnimationFrame(draw)

    return () => {
      disposed = true
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', onPointer)
      container.removeChild(canvas)
      gl.getExtension('WEBGL_lose_context')?.loseContext()
    }
  }, [])

  return (
    <div
      ref={host}
      aria-hidden
      className="pointer-events-none fixed inset-0 mix-blend-soft-light"
    />
  )
}
