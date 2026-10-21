const VERTEX = `#version 300 es
in vec2 place;
in vec2 spot;
uniform vec2 size;
out vec2 at;
void main() {
  at = spot;
  gl_Position = vec4(place.x / size.x * 2.0 - 1.0, 1.0 - place.y / size.y * 2.0, 0.0, 1.0);
}`

const FRAGMENT = `#version 300 es
precision mediump float;
uniform sampler2D picture;
in vec2 at;
out vec4 colour;
void main() {
  // Half a mipmap level finer than the picture's size on the screen calls for, as sharp as the page draws the still.
  colour = texture(picture, at, -0.5);
}`

const compile = (gl: WebGL2RenderingContext, type: number, source: string) => {
  const shader = gl.createShader(type)
  if (!shader) throw new Error('No shader')
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) ?? 'Shader failed')
  return shader
}

/**
 * Draws the cut-out's picture over its mesh in WebGL, as the page would draw the picture itself: its colours as they
 * are, its edge's alpha premultiplied, and scaled down through the picture's mipmaps, so the fur stays as fine as the
 * still picture's at any zoom.
 */
export class Painter {
  private readonly gl: WebGL2RenderingContext
  private readonly places: WebGLBuffer
  private readonly size: WebGLUniformLocation | null
  private readonly spot: number
  private count = 0
  private width = 1
  private height = 1

  /** A painter for the canvas, or none where the browser has no WebGL 2. */
  static open(canvas: HTMLCanvasElement) {
    const gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: false })
    return gl ? new Painter(gl) : null
  }

  private constructor(gl: WebGL2RenderingContext) {
    this.gl = gl
    const program = gl.createProgram()
    gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERTEX))
    gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAGMENT))
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) ?? 'Program failed')
    gl.useProgram(program)
    this.size = gl.getUniformLocation(program, 'size')
    this.places = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, this.places)
    const place = gl.getAttribLocation(program, 'place')
    gl.enableVertexAttribArray(place)
    gl.vertexAttribPointer(place, 2, gl.FLOAT, false, 0, 0)
    this.spot = gl.getAttribLocation(program, 'spot')
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.clearColor(0, 0, 0, 0)
  }

  /** The picture and the mesh it is pinned to: its size in pixels, each point's place on the picture, the triangles. */
  load(picture: HTMLImageElement, width: number, height: number, uv: Float32Array, indices: Uint32Array) {
    const gl = this.gl
    this.width = width
    this.height = height
    const texture = gl.createTexture()
    gl.bindTexture(gl.TEXTURE_2D, texture)
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true)
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, picture)
    gl.generateMipmap(gl.TEXTURE_2D)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    const spots = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, spots)
    gl.bufferData(gl.ARRAY_BUFFER, uv, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(this.spot)
    gl.vertexAttribPointer(this.spot, 2, gl.FLOAT, false, 0, 0)
    const triangles = gl.createBuffer()
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, triangles)
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW)
    this.count = indices.length
    gl.bindBuffer(gl.ARRAY_BUFFER, this.places)
    gl.bufferData(gl.ARRAY_BUFFER, uv.length * 4, gl.DYNAMIC_DRAW)
  }

  /** The canvas's pixels to its box on the page, at the screen's pixel density. */
  fit(width: number, height: number) {
    const canvas = this.gl.canvas
    if (canvas.width === width && canvas.height === height) return
    canvas.width = width
    canvas.height = height
    this.gl.viewport(0, 0, width, height)
  }

  draw(positions: Float32Array) {
    const gl = this.gl
    gl.clear(gl.COLOR_BUFFER_BIT)
    gl.uniform2f(this.size, this.width, this.height)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.places)
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, positions)
    gl.drawElements(gl.TRIANGLES, this.count, gl.UNSIGNED_INT, 0)
  }

  dispose() {
    this.gl.getExtension('WEBGL_lose_context')?.loseContext()
  }
}
