#!/usr/bin/env python3
"""Procedural "coffee patronus": a cup of coffee rendered as a glowing smoke spirit.

The picture is built from scratch with numpy + Pillow (no image model, no external
assets): a glassy cup of revolution, smoke ribbons made of wandering filaments,
sparks, bloom and a tone ramp.

Usage:
    python coffee_patronus.py --palette all --out-dir out
"""
from __future__ import annotations

import argparse
import math
import os
import time

import numpy as np
from PIL import Image

# Base design size; everything scales from it.
W0, H0 = 1080, 1920
ELEV = math.radians(17.5)       # camera elevation above the table
LIQUID = 0.90                   # coffee surface radius relative to the rim
EXPOSURE = 1.4
CUP_TRANSMISSION = 0.35         # share of back-layer light that passes through the cup body

# Warmth: 0 = "patronus" blue ramp, 1 = coffee ramp (only the "mixed" palette blends them).
WARM_STEAM, WARM_SWIRL, WARM_BODY, WARM_LIQUID, WARM_FLOOR, WARM_SPARK = 0.10, 0.12, 0.45, 1.0, 0.35, 0.2

BLUE = [(0.0, (1, 3, 9)), (0.12, (4, 14, 42)), (0.3, (12, 48, 122)), (0.5, (34, 104, 200)),
        (0.68, (92, 172, 242)), (0.84, (168, 220, 252)), (1.0, (240, 250, 255))]
COFFEE = [(0.0, (4, 2, 1)), (0.12, (18, 9, 4)), (0.3, (52, 26, 10)), (0.5, (112, 64, 26)),
          (0.68, (172, 118, 58)), (0.84, (222, 180, 122)), (1.0, (255, 246, 228))]

# Steam layout in rim radii, X right / Y up from the rim centre:
# ("w", x, y) is a waypoint, ("l", radius, turn, turns) a curl (+1 = counter-clockwise).
STEAM_RIBBONS = [
    [("w", -0.70, 0.87), ("w", -0.95, 1.56), ("l", 0.72, 1, 1.0), ("w", -1.90, 2.39), ("w", -1.50, 3.59)],
    [("w", 0.70, 1.01), ("w", 1.00, 2.12), ("l", 0.80, -1, 1.0), ("w", 1.90, 3.22), ("w", 1.70, 4.42)],
    [("w", -0.45, 1.47), ("w", -0.75, 2.48), ("w", -0.20, 3.59), ("w", -0.55, 4.69), ("w", -0.10, 5.43)],
    [("w", 0.40, 1.66), ("w", 0.60, 3.04), ("l", 0.60, -1, 1.0), ("w", 1.50, 4.23), ("w", 1.80, 5.06)],
    [("w", -0.40, 1.84), ("w", -0.60, 3.50), ("l", 0.55, 1, 1.0), ("w", -1.40, 4.69), ("w", -1.60, 5.34)],
    [("w", 0.20, 2.39), ("w", 0.30, 4.23), ("w", -0.40, 5.06), ("w", -1.30, 5.34), ("w", -2.00, 4.97)],
    [("w", -0.20, 2.30), ("w", 0.50, 3.96), ("w", 1.10, 4.97), ("w", 1.90, 5.24), ("w", 2.40, 4.78)],
    [("w", 0.60, 0.37), ("w", 1.00, 0.83), ("l", 0.50, -1, 1.0), ("w", 1.60, 1.56), ("w", 1.50, 2.58)],
    [("w", -0.60, 0.37), ("w", -1.00, 0.74), ("l", 0.48, 1, 1.0), ("w", -1.60, 1.38), ("w", -1.70, 2.39)],
]

PALETTES = ("blue", "coffee", "mixed")


# ----------------------------------------------------------------------------- noise

def make_lattice(seed):
    """Periodic 256x256 lattice of unit gradient vectors."""
    ang = np.random.default_rng(seed).uniform(0.0, 2.0 * np.pi, size=(256, 256))
    return np.cos(ang), np.sin(ang)


def fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def fade_d(t):
    return 30.0 * t * t * (t - 1.0) * (t - 1.0)


def perlin_d(x, y, lat):
    """Gradient noise with analytic derivatives: (n, dn/dx, dn/dy), n roughly in [-1, 1]."""
    gx, gy = lat
    xi = np.floor(x)
    yi = np.floor(y)
    xf = x - xi
    yf = y - yi
    x0 = xi.astype(np.int64) & 255
    y0 = yi.astype(np.int64) & 255
    x1 = (x0 + 1) & 255
    y1 = (y0 + 1) & 255
    ax, ay = gx[y0, x0], gy[y0, x0]
    bx, by = gx[y0, x1], gy[y0, x1]
    cx, cy = gx[y1, x0], gy[y1, x0]
    dx, dy = gx[y1, x1], gy[y1, x1]
    u, v = fade(xf), fade(yf)
    du, dv = fade_d(xf), fade_d(yf)
    d00 = ax * xf + ay * yf
    d10 = bx * (xf - 1.0) + by * yf
    d01 = cx * xf + cy * (yf - 1.0)
    d11 = dx * (xf - 1.0) + dy * (yf - 1.0)
    a = d00 + u * (d10 - d00)
    b = d01 + u * (d11 - d01)
    dax = ax + du * (d10 - d00) + u * (bx - ax)
    dbx = cx + du * (d11 - d01) + u * (dx - cx)
    day = ay + u * (by - ay)
    dby = cy + u * (dy - cy)
    n = a + v * (b - a)
    nx = (1.0 - v) * dax + v * dbx
    ny = dv * (b - a) + (1.0 - v) * day + v * dby
    k = 1.414
    return n * k, nx * k, ny * k


def fbm(x, y, lat, octaves=3, lac=2.0, gain=0.5):
    n = np.zeros(np.shape(x))
    amp, f, norm = 1.0, 1.0, 0.0
    for i in range(octaves):
        n += amp * perlin_d(x * f + 7.3 * i + 0.31, y * f + 3.1 * i + 0.77, lat)[0]
        norm += amp
        amp *= gain
        f *= lac
    return n / norm


def noise1(t, lat):
    """Smooth 1D noise along a coordinate."""
    return perlin_d(t, 0.37, lat)[0]


# ----------------------------------------------------------------------------- raster helpers

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def deposit(buf, x, y, w):
    """Bilinear splat of weights w at float positions (x, y); out-of-range points are dropped."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    shape = np.broadcast(x, y).shape
    x = np.broadcast_to(x, shape).ravel()
    y = np.broadcast_to(y, shape).ravel()
    w = np.broadcast_to(np.asarray(w, dtype=np.float64), shape).ravel()
    ok = (x >= 0) & (y >= 0) & (x <= buf.shape[1] - 1) & (y <= buf.shape[0] - 1)
    if not ok.all():
        x, y, w = x[ok], y[ok], w[ok]
    if x.size == 0:
        return
    x0 = x.astype(np.int64)
    y0 = y.astype(np.int64)
    x1 = np.minimum(x0 + 1, buf.shape[1] - 1)
    y1 = np.minimum(y0 + 1, buf.shape[0] - 1)
    fx = x - x0
    fy = y - y0
    width = buf.shape[1]
    flat = buf.ravel()
    n = buf.size
    flat += np.bincount(y0 * width + x0, weights=w * (1.0 - fx) * (1.0 - fy), minlength=n)
    flat += np.bincount(y0 * width + x1, weights=w * fx * (1.0 - fy), minlength=n)
    flat += np.bincount(y1 * width + x0, weights=w * (1.0 - fx) * fy, minlength=n)
    flat += np.bincount(y1 * width + x1, weights=w * fx * fy, minlength=n)


class Layer:
    """Additive HDR layer: intensity plus (optionally) warmth-weighted intensity."""

    def __init__(self, w, h, use_warm=False):
        self.w, self.h, self.use_warm = w, h, use_warm
        self.i = np.zeros((h, w))
        self.k = np.zeros((h, w))

    def add(self, x, y, weight, warm=0.0):
        deposit(self.i, x, y, weight)
        if self.use_warm and np.any(warm):
            deposit(self.k, x, y, weight * np.asarray(warm, dtype=np.float64))


def spline_curve(ctrl, spacing):
    """Catmull-Rom spline through control points, resampled at a fixed arc-length spacing."""
    P = np.vstack([ctrl[0], ctrl, ctrl[-1]])
    t = np.linspace(0.0, 1.0, 24, endpoint=False)[:, None]
    out = [ctrl[0][None]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        out.append(0.5 * (2.0 * p1 + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t ** 2
                          + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t ** 3))
    out.append(ctrl[-1][None])
    curve = np.vstack(out)
    seg = np.hypot(*np.diff(curve, axis=0).T)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(2, int(cum[-1] / spacing))
    s = np.linspace(0.0, cum[-1], n)
    return np.stack([np.interp(s, cum, curve[:, 0]), np.interp(s, cum, curve[:, 1])], axis=1)


def gaussian_blur(img, sigma):
    """FFT gaussian blur; large sigmas are computed on a block-averaged copy."""
    if sigma < 1e-3:
        return img
    f = max(1, int(sigma / 16.0))
    small = img if f == 1 else block_mean(img, f)
    pad = int(3.0 * sigma / f) + 2
    p = np.pad(small, pad, mode="edge")
    spec = np.fft.rfft2(p)
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    spec *= np.exp(-2.0 * (math.pi * sigma / f) ** 2 * (fx * fx + fy * fy))
    out = np.fft.irfft2(spec, s=p.shape)[pad:-pad, pad:-pad]
    return out if f == 1 else resize(out, img.shape)


def block_mean(img, f):
    h, w = img.shape
    hh, ww = h // f, w // f
    return img[:hh * f, :ww * f].reshape(hh, f, ww, f).mean(axis=(1, 3))


def resize(a, shape):
    h, w = shape
    pil = Image.fromarray(a.astype(np.float32), mode="F")
    return np.asarray(pil.resize((w, h), Image.BILINEAR), dtype=np.float64)


# ----------------------------------------------------------------------------- scene

class Geometry:
    """Cup dimensions in output pixels."""

    def __init__(self, w, h):
        s = w / W0
        self.w, self.h, self.s = w, h, s
        self.cx = 505.0 * s
        self.R = 222.0 * s                    # rim radius
        self.Rb = 0.65 * self.R               # foot radius
        self.Hc = self.R * 250.0 / 215.0      # cup height
        self.ytop = 1290.0 * s                # rim centre
        self.se, self.ce = math.sin(ELEV), math.cos(ELEV)
        self.ybot = self.ytop + self.Hc * self.ce          # foot ellipse centre
        self.floor = self.ybot + self.Rb * self.se         # lowest point of the cup
        # handle ring: centre, semi-axes, tube radius
        self.handle = (self.cx + 0.79 * self.R, self.ytop + 0.52 * self.Hc * self.ce,
                       0.56 * self.R, 0.415 * self.R, 0.075 * self.R)

    def surface(self, th, hh, f=1.0):
        """Project a point of the (optionally inflated) cup wall: (sx, sy, depth Z>0 = front)."""
        r = np.maximum(self.Rb * 0.9, self.Rb + (self.R - self.Rb) * hh) * f
        x = r * np.cos(th)
        z = r * np.sin(th)
        return self.cx + x, self.ytop + (1.0 - hh) * self.Hc * self.ce + z * self.se, z


def pixel_grid(g):
    return np.meshgrid(np.arange(g.w, dtype=np.float64), np.arange(g.h, dtype=np.float64))


def cup_body_coverage(g, X, Y):
    """Anti-aliased coverage of the cup body (walls and foot, the opening excluded)."""
    xr = X - g.cx
    yr = Y - g.ytop
    wall = math.hypot(g.R - g.Rb, g.Hc * g.ce)
    nx, ny = g.Hc * g.ce / wall, -(g.R - g.Rb) / wall
    # the walls only exist below the rim; higher up the rim ellipse is the sole boundary
    d_left = np.where(yr < 0.0, 1e3, (xr + g.R) * nx + yr * ny)
    d_right = np.where(yr < 0.0, 1e3, (g.R - xr) * nx + yr * ny)

    def half_ellipse(half, cy, want_above):
        inside_x = np.abs(xr) < half * (1.0 - 1e-6)
        q = np.sqrt(np.clip(1.0 - (xr / half) ** 2, 0.0, None))
        y_arc = cy + half * g.se * q
        slope = -g.se * xr / (half * np.maximum(q, 1e-6))
        d = (y_arc - yr) if want_above else (yr - y_arc)
        return np.where(inside_x, d / np.sqrt(1.0 + slope * slope), 1e3)

    d_bottom = half_ellipse(g.Rb, g.Hc * g.ce, True)
    d_lip = half_ellipse(g.R, 0.0, False)
    d = np.minimum(np.minimum(d_left, d_right), np.minimum(d_bottom, d_lip))
    # above the rim level only the rim ellipse bounds the body (positive inside it, negative outside)
    ex, ey = xr / g.R, yr / (g.R * g.se)
    above = (1.0 - (ex * ex + ey * ey)) \
        / (2.0 * np.sqrt((xr / g.R ** 2) ** 2 + (yr / (g.R * g.se) ** 2) ** 2) + 1e-12)
    d = np.where(yr < 0.0, np.minimum(d, above), d)
    return np.clip(d + 0.5, 0.0, 1.0)


def ellipse_coverage(g, X, Y, scale=1.0):
    """Anti-aliased coverage of an ellipse concentric with the rim."""
    a, b = g.R * scale, g.R * g.se * scale
    xr, yr = X - g.cx, Y - g.ytop
    e = (xr / a) ** 2 + (yr / b) ** 2
    grad = 2.0 * np.sqrt((xr / a ** 2) ** 2 + (yr / b ** 2) ** 2) + 1e-12
    return np.clip((1.0 - e) / grad + 0.5, 0.0, 1.0)


# ----------------------------------------------------------------------------- smoke

def ribbon_points(rng, start, segments):
    """Control points of a smoke ribbon from a small route description (same units as the route)."""
    pts = [np.array(start, dtype=np.float64)]
    for seg in segments:
        if seg[0] == "w":
            target = np.array(seg[1:]) + rng.normal(0.0, 0.08, 2)
            p0, p1 = pts[-1], target
            d = p1 - p0
            bow = rng.normal(0.0, 0.12) * np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9)
            for t in (1.0 / 3.0, 2.0 / 3.0):
                pts.append(p0 + d * t + bow * math.sin(math.pi * t))
            pts.append(p1)
        else:
            _, rho, turn, turns = seg
            e = pts[-1]
            v = e - pts[-2]
            v = v / (np.linalg.norm(v) + 1e-9)
            c = e + turn * rho * np.array([-v[1], v[0]])          # circle tangent to the arrival direction
            a0 = math.atan2(e[1] - c[1], e[0] - c[0])
            m = max(3, int(round(6 * turns)))
            squash = rng.uniform(0.0, 0.28)                          # curls are flattened, not circular
            tilt = rng.uniform(0.0, math.pi)
            grow = rng.uniform(0.18, 0.40)
            for k in range(1, m + 1):
                a = a0 + turn * 2.0 * math.pi * turns * k / m
                r = rho * (1.0 + grow * k / m) * (1.0 + squash * math.cos(2.0 * (a - tilt)))
                pts.append(c + r * np.array([math.cos(a), math.sin(a)]))
    return np.array(pts)


def draw_ribbon(layer, curve, rng, lat, g, q, gain, width, warm, fade=0.45, haze=1.0, back=None, back_mask=None):
    """A smoke ribbon: a widening band of soft filaments along a centreline (screen px).

    With `back`/`back_mask` the band is split by depth: samples flagged in back_mask go to the back layer.
    Returns the core sample positions and weights (used to seed sparks).
    """
    n = max(4, int(rng.integers(14, 26) * q))
    m = curve.shape[0]
    s = np.linspace(0.0, 1.0, m)[:, None]
    tangent = np.gradient(curve, axis=0)
    norm = np.hypot(tangent[:, 0], tangent[:, 1]) + 1e-9
    nrm = np.stack([-tangent[:, 1] / norm, tangent[:, 0] / norm], axis=1)[:, None, :]
    half = width * g.s * (0.45 + 1.0 * s ** 0.9)                 # the band widens along the ribbon
    wander = (4.0 + 18.0 * s) * g.s * noise1(s * 5.0 + rng.uniform(0.0, 100.0, (1, n)), lat)
    off = 0.7 * rng.normal(0.0, 1.0, (1, n)) * half + wander \
        + 3.0 * g.s * noise1(s * 14.0 + rng.uniform(0.0, 100.0, (1, n)), lat)
    pos = curve[:, None, :] + off[..., None] * nrm
    core = np.exp(-((off / half) ** 2) / 0.6)                     # brighter in the middle of the band
    env = smoothstep(0.0, 0.2, s) * (1.0 - smoothstep(fade, 1.0, s)) ** 1.3
    streak = 0.3 + 0.7 * np.clip(0.5 + noise1(s * 9.0 + rng.uniform(0.0, 100.0, (1, n)), lat), 0.0, 1.0) ** 1.2
    w = gain * env * streak * core
    x, y = pos[..., 0], pos[..., 1]
    behind = None if back is None else np.broadcast_to(back_mask[:, None], x.shape)

    def puff(px, py, pw, jitter):
        px = px + rng.normal(0.0, jitter, px.shape)
        py = py + rng.normal(0.0, jitter, px.shape)
        if behind is None:
            layer.add(px, py, pw, warm)
        else:
            layer.add(px[~behind], py[~behind], pw[~behind], warm)
            back.add(px[behind], py[behind], pw[behind], warm)

    for _copy in range(3):
        puff(x, y, 0.3 * w, 1.5 * g.s)                            # soft filaments
    sig = 0.55 * half + 6.0 * g.s
    for _copy in range(4):
        puff(x, y, 0.45 * w, sig)                                 # body of the ribbon
    for _copy in range(3):
        puff(x, y, 0.25 * haze * w, 2.8 * sig)                    # haze
    return x.ravel(), y.ravel(), w.ravel()


def wandering_ribbons(rng, count):
    """Straight-ish rising ribbons without curls, to fill the column between the designed ones."""
    out = []
    for _ in range(count):
        x, y, route = 0.0, 0.0, []
        for _step in range(int(rng.integers(3, 5))):
            x = float(np.clip(x + rng.uniform(-0.7, 0.7), -1.0, 1.0))
            y += rng.uniform(0.8, 1.5)
            route.append(("w", x, y))
        out.append(route)
    return out


def draw_steam(g, front, rng, lat, q):
    """Steam: designed ribbons rising from the coffee surface."""
    samples = []
    routes = STEAM_RIBBONS + wandering_ribbons(rng, int(3 * q))
    for route in routes:
        a = rng.uniform(0.0, 2.0 * math.pi)
        rr = 0.9 * LIQUID * math.sqrt(rng.random())
        start = (rr * math.cos(a), -rr * math.sin(a) * g.se)      # a point on the coffee surface
        ctrl = ribbon_points(rng, start, route)
        curve = np.stack([g.cx + ctrl[:, 0] * g.R, g.ytop - ctrl[:, 1] * g.R], axis=1)
        curve = spline_curve(curve, 0.6 * g.s)
        designed = any(seg[0] == "l" for seg in route)
        samples.append(draw_ribbon(front, curve, rng, lat, g, q, rng.uniform(0.45, 0.65) if designed else 0.25,
                                   rng.uniform(20.0, 34.0), WARM_STEAM))
    return samples


def draw_swirls(g, front, back, rng, lat, q):
    """Skirts of smoke: helical ribbons that leave the rim, hug the wall and flare out to the floor."""
    steps = 500
    s = np.linspace(0.0, 1.0, steps)
    for _ in range(int(4 * q)):
        direction = 1.0 if rng.random() < 0.5 else -1.0
        turns = rng.uniform(0.8, 1.5)
        h0, h1 = rng.uniform(0.8, 1.0), rng.uniform(0.0, 0.2)
        f1 = rng.uniform(1.6, 2.4)
        th = rng.uniform(0.0, 2.0 * math.pi) + direction * turns * 2.0 * math.pi * s ** 0.85 \
            + 0.12 * noise1(s * 7.0 + rng.uniform(0.0, 100.0), lat)
        hh = h0 + (h1 - h0) * s + 0.04 * noise1(s * 6.0 + rng.uniform(0.0, 100.0), lat)
        ff = 1.03 + (f1 - 1.03) * s ** 1.7
        sx, sy, z = g.surface(th, hh, ff)
        curve = spline_curve(np.stack([sx, sy], axis=1), 0.7 * g.s)
        depth = np.interp(np.linspace(0.0, 1.0, curve.shape[0]), s, z)
        draw_ribbon(front, curve, rng, lat, g, q, rng.uniform(0.20, 0.30), rng.uniform(14.0, 22.0),
                    WARM_SWIRL, fade=0.5, back=back, back_mask=depth < 0.0)


def draw_floor(g, back, front, fx, rng, lat, q):
    """Light pool under the cup plus mist creeping outwards over the table."""
    X, Y = pixel_grid(g)
    dx, dy = (X - g.cx) / (1.45 * g.R), (Y - (g.floor + 0.02 * g.R)) / (0.24 * g.R)
    glow = 0.16 * np.exp(-(dx * dx + dy * dy))
    dx2, dy2 = (X - g.cx) / (0.78 * g.R), (Y - g.floor) / (0.13 * g.R)
    glow += 0.14 * np.exp(-(dx2 * dx2 + dy2 * dy2))
    fx.i += glow
    fx.k += glow * WARM_FLOOR

    # mist routes live on the table plane (second axis = away from the viewer), in rim radii
    for _ in range(int(7 * q)):
        a = rng.uniform(0.0, 2.0 * math.pi)
        cir = -1.0 if rng.random() < 0.5 else 1.0
        r = 0.72
        start = (r * math.cos(a), r * math.sin(a))
        route = []
        for _step in range(2):
            a += cir * rng.uniform(0.8, 1.4)
            r += rng.uniform(0.55, 0.95)
            route.append(("w", r * math.cos(a), r * math.sin(a)))
        route.append(("l", rng.uniform(0.35, 0.6), cir, rng.uniform(0.7, 1.1)))
        a += cir * 0.7
        r += 0.45
        route.append(("w", r * math.cos(a), r * math.sin(a)))
        ctrl = ribbon_points(rng, start, route)
        curve = np.stack([g.cx + ctrl[:, 0] * g.R, g.ybot - ctrl[:, 1] * g.R * g.se], axis=1)
        curve = spline_curve(curve, 0.7 * g.s)
        draw_ribbon(front, curve, rng, lat, g, q, rng.uniform(0.16, 0.24), rng.uniform(26.0, 40.0),
                    WARM_SWIRL, fade=0.4, back=back, back_mask=curve[:, 1] < g.ybot)


# ----------------------------------------------------------------------------- cup

def glass_shade(nx, ny, nz, g):
    """Translucent glossy material: dark base, bright grazing angles, two specular streaks."""
    ce, se = g.ce, g.se
    ndv = np.clip(ny * ce + nz * se, 0.0, 1.0)
    out = 0.07 + 0.26 * (1.0 - ndv) ** 2.0
    for light, broad, tight in (((-0.55, 0.45, 0.70), 0.22, 0.90), ((0.75, 0.35, 0.56), 0.16, 0.70)):
        hx, hy, hz = light[0], light[1] + ce, light[2] + se
        norm = math.sqrt(hx * hx + hy * hy + hz * hz)
        ndh = np.clip((nx * hx + ny * hy + nz * hz) / norm, 0.0, 1.0)
        out += broad * ndh ** 18 + tight * ndh ** 200
    return out


def draw_cup_body(g, cup, lat, cB):
    """Forward-render the wall as a surface of revolution and keep the body silhouette."""
    n_th, n_h = 1800, 700
    th = np.linspace(0.0, 2.0 * np.pi, n_th, endpoint=False)[:, None]
    hh = np.linspace(0.0, 1.0, n_h)[None, :]
    ct, st = np.cos(th), np.sin(th)
    sx, sy, z = g.surface(ct, hh)
    sx, sy, z = sx.ravel(), sy.ravel(), z.ravel()
    slope = (g.R - g.Rb) / g.Hc
    nx = np.broadcast_to(ct, (n_th, n_h)).ravel()
    nz = np.broadcast_to(st, (n_th, n_h)).ravel()
    ny = np.full_like(nx, -slope)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = glass_shade(nx / norm, ny / norm, nz / norm, g)
    wisps = fbm(sx / (70.0 * g.s), sy / (70.0 * g.s), lat, 3)
    shade *= 0.70 + 0.60 * np.clip(0.5 + 0.8 * wisps, 0.0, 1.0)
    acc = Layer(g.w, g.h)
    cnt = np.zeros((g.h, g.w))
    deposit(acc.i, sx, sy, shade)
    deposit(cnt, sx, sy, 1.0)
    body = acc.i / np.maximum(cnt, 1e-9) * cB
    cup.i += body
    cup.k += body * WARM_BODY


def draw_cup_filaments(g, cup, back, rng, lat, q):
    """Lathe-like streaks on the wall: rings and meridians, back ones are seen through the body."""
    for kind, count, strength in (("ring", 24, 1.0), ("meridian", 10, 0.6)):
        for _ in range(int(count * q)):
            if kind == "ring":
                t = np.linspace(0.0, rng.uniform(0.9, 2.0 * math.pi), 1400)
                th = t + rng.uniform(0.0, 2.0 * math.pi)
                hh = np.full_like(t, rng.uniform(0.05, 0.95))
                hh = hh + 0.012 * noise1(th * 2.2 + rng.uniform(0, 100), lat)
            else:
                t = np.linspace(0.0, 1.0, 900)
                hh = 0.02 + 0.96 * t
                th = rng.uniform(0.0, 2.0 * math.pi) + 0.05 * noise1(t * 9.0 + rng.uniform(0, 100), lat)
            sx, sy, z = g.surface(th, hh)
            s = t / t[-1]
            env = np.sin(np.pi * s) ** 0.6
            streak = 0.3 + 0.7 * np.clip(0.5 + 1.2 * noise1(t * 5.0 + rng.uniform(0, 100), lat), 0.0, 1.0) ** 1.3
            w = 0.24 * strength * env * streak
            front = z > 0
            for layer, mask, gain in ((cup, front, 1.0), (back, ~front, 0.9)):
                layer.add(sx[mask], sy[mask], gain * w[mask], WARM_BODY)
                for _copy in range(2):
                    layer.add(sx[mask] + rng.normal(0.0, 3.0 * g.s, mask.sum()),
                              sy[mask] + rng.normal(0.0, 3.0 * g.s, mask.sum()),
                              gain * 0.25 * w[mask], WARM_BODY)


def draw_top(g, cup, rng, lat):
    """Coffee surface with a swirl, the lip and the bright rim."""
    X, Y = pixel_grid(g)
    xr, yr = X - g.cx, Y - g.ytop
    c_open = ellipse_coverage(g, X, Y, 1.0)
    c_liq = ellipse_coverage(g, X, Y, LIQUID)
    a, b = g.R * LIQUID, g.R * g.se * LIQUID
    u, v = xr / a, yr / b
    r = np.hypot(u, v)
    liquid = 0.13 + 0.07 * (1.0 - r * r)
    liquid += 0.35 * np.exp(-((r - 0.86) / 0.09) ** 2)                          # crema ring
    liquid += 0.29 * np.exp(-(r / 0.22) ** 2)                                   # hot core
    liquid += 0.18 * np.exp(-(((u + 0.35) / 0.5) ** 2 + ((v + 0.3) / 0.4) ** 2))  # sheen
    cup.i += liquid * c_liq
    cup.k += liquid * c_liq * WARM_LIQUID
    lip = (0.17 + 0.38 * smoothstep(0.9, 1.0, r * LIQUID)) * c_open * (1.0 - c_liq)
    cup.i += lip
    cup.k += lip * WARM_BODY

    # two spiral arms on the surface
    phi = np.linspace(0.0, 3.2 * math.pi, 1500)
    rs = 0.06 * np.exp(0.36 * phi)
    keep = rs < 0.80
    phi, rs = phi[keep], rs[keep]
    s = np.linspace(0.0, 1.0, phi.size)
    for arm in range(2):
        ang = phi + arm * math.pi + 0.5
        sx = g.cx + a * rs * np.cos(ang)
        sy = g.ytop + b * rs * np.sin(ang)
        w = 0.85 * (1.0 - rs / 0.85) ** 0.8 * np.sin(np.pi * s) ** 0.4
        cup.add(sx, sy, w, WARM_LIQUID)
        for _copy in range(2):
            cup.add(sx + rng.normal(0.0, 3.0 * g.s, s.size), sy + rng.normal(0.0, 1.2 * g.s, s.size),
                    0.3 * w, WARM_LIQUID)

    # rim tube along the ellipse
    n = 5000
    phi = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    px, py = g.cx + g.R * np.cos(phi), g.ytop + g.R * g.se * np.sin(phi)
    tx, ty = -g.R * np.sin(phi), g.R * g.se * np.cos(phi)
    tn = np.hypot(tx, ty)
    nx, ny = ty / tn, -tx / tn
    arc = np.sum(np.hypot(np.diff(px), np.diff(py))) / n          # px per sample
    us = np.linspace(-1.0, 1.0, 25)[:, None]
    prof = np.exp(-4.2 * us ** 2)
    prof *= (2.0 / (us.size - 1)) / prof.sum()                      # sums to 1 across the tube
    rt = 0.032 * g.R
    sx = px[None, :] + rt * us * nx[None, :]
    sy = py[None, :] + rt * us * ny[None, :]
    cup.add(sx, sy, np.broadcast_to(1.9 * prof * arc, sx.shape), WARM_BODY * 0.7)


def draw_handle(g, cup, cB):
    """Handle: a glass tube swept along an ear-shaped arc, hidden where it enters the wall."""
    hcx, hcy, a, b, rt = g.handle
    phi = np.linspace(math.radians(-112), math.radians(110), 1600)
    px, py = hcx + a * np.cos(phi), hcy + b * np.sin(phi)
    tx, ty = -a * np.sin(phi), b * np.cos(phi)
    tn = np.hypot(tx, ty)
    n2x, n2y = ty / tn, -tx / tn                                     # 2D normal (points outward)
    arc = np.sum(np.hypot(np.diff(px), np.diff(py))) / phi.size
    us = np.linspace(-1.0, 1.0, 41)[:, None]                         # cos(psi) across the tube
    sz = np.sqrt(1.0 - us ** 2)                                      # sin(psi), front half only
    sx = px[None, :] + rt * us * n2x[None, :]
    sy = py[None, :] + rt * us * n2y[None, :] + rt * sz * g.se
    shade = glass_shade(us * n2x[None, :], us * n2y[None, :], np.broadcast_to(sz, sx.shape), g)
    body = np.zeros((g.h, g.w))
    deposit(body, sx, sy, 1.6 * shade * arc)   # weight = value x spacing keeps the sum per pixel equal to shade
    cup.i += body * (1.0 - cB)
    cup.k += body * (1.0 - cB) * WARM_BODY


def draw_particles(g, fx, rng, samples, q):
    """Sparks: mostly clustered along the steam ribbons, some scattered around the cup."""
    x = np.concatenate([s[0] for s in samples])
    y = np.concatenate([s[1] for s in samples])
    w = np.concatenate([s[2] for s in samples])
    pick = rng.choice(x.size, size=min(x.size, int(600 * q)), p=w / w.sum())
    n = max(10, int(900 * q))
    n_near = pick.size
    px = np.concatenate([x[pick] + rng.normal(0.0, 22.0 * g.s, n_near),
                         g.cx + rng.uniform(-2.6, 2.6, n - n_near) * g.R])
    py = np.concatenate([y[pick] + rng.normal(0.0, 22.0 * g.s, n_near),
                         g.ytop - rng.uniform(-1.2, 5.4, n - n_near) * g.R])
    sigma = np.maximum((0.55 + 1.6 * rng.random(n) ** 3) * g.s, 0.4)      # gaussian PSF radius in px
    amp = 0.25 + 1.6 * rng.random(n) ** 5
    offs = np.arange(-3, 4)
    ker = np.exp(-(offs[:, None, None] ** 2 + offs[None, :, None] ** 2) / (2.0 * sigma ** 2)[None, None, :])
    ker /= ker.sum(axis=(0, 1))[None, None, :]
    for i in range(offs.size):
        for j in range(offs.size):
            fx.add(px + offs[i], py + offs[j], amp * ker[i, j], WARM_SPARK)


# ----------------------------------------------------------------------------- grading

def ramp(stops, t):
    pos = np.array([p for p, _ in stops])
    cols = np.array([c for _, c in stops], dtype=np.float64) / 255.0
    out = np.empty(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, pos, cols[:, c])
    return out


def grade(g, back, cup, front, fx, cB, palette, lat, X, Y):
    """Composite the depth layers, bloom, tone-map, add floor reflection / haze and colour."""
    s = g.s
    trans = 1.0 - cB * (1.0 - CUP_TRANSMISSION)
    I = back.i * trans + cup.i + front.i + fx.i
    bloom = ((5.0, 0.22), (16.0, 0.14), (48.0, 0.10), (140.0, 0.06), (420.0, 0.05))
    hdr = I.copy()
    for sigma, gain in bloom:
        hdr += gain * gaussian_blur(I, sigma * s)
    warm = None
    if palette == "mixed":
        K = back.k * trans + cup.k + front.k + fx.k
        hdr_k = K.copy()
        for sigma, gain in bloom:
            hdr_k += gain * gaussian_blur(K, sigma * s)
        warm = np.clip(hdr_k / (hdr + 1e-4), 0.0, 1.0)

    t = 1.0 - np.exp(-EXPOSURE * hdr)

    # glossy table: mirrored, blurred and fading copy of everything above the contact line
    fy = int(round(g.floor))
    rows = g.h - fy
    if rows > 2:
        refl = gaussian_blur(t[:fy][::-1][:rows], 2.5 * s)
        dy = np.arange(rows)[:, None]
        fade = (1.0 - np.exp(-dy / (6.0 * s))) * np.exp(-dy / (110.0 * s))   # eases in, no seam at the contact line
        t[fy:] += 0.32 * refl * fade
        if warm is not None:
            strong = refl > 0.02
            below = warm[fy:]
            below[strong] = (hdr_k / (hdr + 1e-4))[:fy][::-1][:rows][strong]
            warm[fy:] = below

    # dark haze with a faint halo around the spirit
    haze = fbm(X / (420.0 * s), Y / (420.0 * s), lat, 2)
    hx, hy = (X - g.cx) / (2.2 * g.R), (Y - (g.ytop - 1.5 * g.R)) / (4.5 * g.R)
    bg = 0.010 + 0.012 * (0.5 + 0.5 * haze) ** 2 + 0.04 * np.exp(-(hx * hx + hy * hy))
    bg *= 1.0 - 0.25 * smoothstep(g.floor - 0.02 * g.R, g.floor + 0.1 * g.R, Y)
    t = t + bg

    rgb = ramp(BLUE, t)
    if palette == "coffee":
        rgb = ramp(COFFEE, t)
    elif palette == "mixed":
        rgb = rgb * (1.0 - warm[..., None]) + ramp(COFFEE, t) * warm[..., None]

    # vignette and dithering against banding
    vx, vy = (X - g.w / 2) / (g.w / 2), (Y - 0.55 * g.h) / (0.62 * g.h)
    rgb *= (1.0 - 0.5 * np.clip(vx * vx + vy * vy, 0.0, 1.0) ** 1.1)[..., None]
    rgb += np.random.default_rng(12345).uniform(-0.5 / 255.0, 0.5 / 255.0, rgb.shape)
    return (np.clip(rgb, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def render(palette="blue", scale=1.0, seed=11, quality=1.0):
    """Render one picture; returns an uint8 RGB array."""
    rng = np.random.default_rng(seed)
    w, h = int(round(W0 * scale)), int(round(H0 * scale))
    g = Geometry(w, h)
    lat = make_lattice(seed)
    use_warm = palette == "mixed"
    back, cup, front, fx = (Layer(w, h, use_warm) for _ in range(4))
    X, Y = pixel_grid(g)
    cB = cup_body_coverage(g, X, Y)
    draw_cup_body(g, cup, lat, cB)
    draw_cup_filaments(g, cup, back, rng, lat, quality)
    draw_top(g, cup, rng, lat)
    draw_handle(g, cup, cB)
    samples = draw_steam(g, front, rng, lat, quality)
    draw_swirls(g, front, back, rng, lat, quality)
    draw_floor(g, back, front, fx, rng, lat, quality)
    draw_particles(g, fx, rng, samples, quality)
    return grade(g, back, cup, front, fx, cB, palette, lat, X, Y)


def main():
    ap = argparse.ArgumentParser(description="Render a coffee patronus.")
    ap.add_argument("--palette", default="all", choices=PALETTES + ("all",))
    ap.add_argument("--scale", type=float, default=1.0, help="output scale (1.0 = 1080x1920)")
    ap.add_argument("--quality", type=float, default=1.0, help="sample-count multiplier")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    for palette in PALETTES if args.palette == "all" else (args.palette,):
        t0 = time.time()
        img = render(palette, args.scale, args.seed, args.quality)
        path = os.path.join(args.out_dir, f"coffee-patronus-{palette}.png")
        Image.fromarray(img).save(path, optimize=True)
        print(f"{path}: {img.shape[1]}x{img.shape[0]} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
