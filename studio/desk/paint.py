"""Array painting for flat stock. Distances are in em, arrays are rows from the top like CSS."""

import numpy as np


def linear(colour):
    """sRGB hex string to linear RGB."""
    value = colour.lstrip("#")
    rgb = np.array([int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def box(X, Y, x0, y0, x1, y1, r=0.0):
    """Signed distance to a rectangle with corner radius r. Negative inside."""
    qx = np.abs(X - (x0 + x1) / 2) - ((x1 - x0) / 2 - r)
    qy = np.abs(Y - (y0 + y1) / 2) - ((y1 - y0) / 2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def disc(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def segment(X, Y, ax, ay, bx, by, r=0.0):
    """Signed distance to a line segment of half-width r."""
    px, py, dx, dy = X - ax, Y - ay, bx - ax, by - ay
    t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(px - dx * t, py - dy * t) - r


def dots(X, Y, ax, ay, bx, by, pitch, r):
    """Signed distance to a row of discs spaced evenly from a to b."""
    length = np.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / length, (by - ay) / length
    along = (X - ax) * ux + (Y - ay) * uy
    across = (Y - ay) * ux - (X - ax) * uy
    count = max(1, round(length / pitch))
    nearest = np.clip(np.round(along * count / length), 0, count) * length / count
    return np.hypot(along - nearest, across) - r


def cover(d, soft):
    """Coverage of a shape from its signed distance, antialiased over `soft` em."""
    return np.clip(0.5 - d / soft, 0, 1)


def ramp(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, sigma):
    """Gaussian blur, sigma in pixels."""
    if sigma <= 0:
        return a
    pad = int(sigma * 3) + 1
    padded = np.pad(a, pad, mode="reflect")
    fy = np.fft.fftfreq(padded.shape[0])[:, None]
    fx = np.fft.rfftfreq(padded.shape[1])[None, :]
    kernel = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    out = np.fft.irfft2(np.fft.rfft2(padded) * kernel, s=padded.shape)
    return out[pad:-pad, pad:-pad]


def cloud(shape, seed, falloff=1.6, stretch=1.0):
    """Fractal noise with unit deviation. Higher falloff is smoother, stretch draws it out along x."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.rfftfreq(shape[1])[None, :] * stretch
    f = np.hypot(fx, fy)
    f[0, 0] = 1
    spectrum = np.fft.rfft2(rng.standard_normal(shape)) / f**falloff
    spectrum[0, 0] = 0
    out = np.fft.irfft2(spectrum, s=shape)
    return out / out.std()


def streaks(shape, seed, length, width=0.6):
    """White noise smeared along x: brushing, scratches. length and width are in pixels."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.rfftfreq(shape[1])[None, :]
    kernel = np.exp(-2 * np.pi**2 * ((length * fx) ** 2 + (width * fy) ** 2))
    out = np.fft.irfft2(np.fft.rfft2(rng.standard_normal(shape)) * kernel, s=shape)
    return out / out.std()
