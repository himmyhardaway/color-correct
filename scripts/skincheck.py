#!/usr/bin/env python3
"""Skin-tone safety gate: compare skin pixels before vs after a grade.

Usage: python3 skincheck.py original.jpg graded.jpg

Detects likely-skin pixels in the ORIGINAL, then measures how the grade
moved those same pixels:
- hue shift (degrees)   — >6 deg reads as wrong skin
- saturation change (%) — oompa-loompa (+) or corpse (-) risk
- luma change           — did the grade darken/brighten faces
- DENSITY metrics       — the ashy/washed failure mode (see below)

Verdict: PASS / SOFTEN (halve the look) / FAIL (rethink the grade).
Exit code 0 = pass, 1 = soften, 2 = fail (script-friendly).

--- Why the density metrics exist -------------------------------------
Hue+sat means alone cannot see "washed out". A matte look that lifts the
black floor drains contrast *inside* deep skin while leaving mean hue and
mean saturation almost untouched — it passes a hue/sat gate and still
looks ashy. Where a subject's skin sits in the tonal range decides who
this hits: lighter skin sits in the upper mids, so a black lift only
touches background shadow (reads as "filmic"); deeper skin sits in and
just above the lifted range, so the same lift lands on the face.

So we also measure, over skin pixels only:
- spread   p90-p10 of skin luma   -> facial modeling / dimensionality
- floor    p10 of skin saturation -> the ashiness canary
- specular p99 of skin luma       -> the sheen that models deep skin

--- Why the detector floor is low -------------------------------------
The classic YCbCr skin box is usually paired with a luma floor near
y>60. That floor silently drops shadowed deep-skin pixels from the
sample *before* any measurement, so the gate ends up judging a brighter,
cherry-picked subset of the face — the part most likely to pass. The
floor here is y>28, with saturation bounds doing the wall-rejection work
instead. Run with --debug to dump a mask overlay and check by eye.
"""
import sys
import numpy as np
from PIL import Image

HUE_SOFTEN, HUE_FAIL = 6.0, 10.0       # degrees (calibrated: approved subtle looks pass)
SAT_SOFTEN, SAT_FAIL = 25.0, 45.0      # relative %
SPREAD_SOFTEN, SPREAD_FAIL = 12.0, 22.0   # relative % drop in skin luma spread
FLOOR_SOFTEN, FLOOR_FAIL = 12.0, 22.0     # relative % drop in skin saturation floor
SPEC_SOFTEN = 8.0                          # relative % drop in skin specular ceiling
MIN_SKIN_FRACTION = 0.02               # need >2% of frame to judge

LUMA_FLOOR = 28                        # keep shadowed deep skin in the sample


def load(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((960, 960))
    return np.asarray(im, dtype=np.float64)


def skin_mask(rgb):
    """Tightened YCbCr skin box + saturation bounds.

    The classic box (Cb 77-127, Cr 133-173) also matches beige walls,
    concrete and blonde hair — measured 41% "skin" on an outdoor talking
    head. Tighter chroma + requiring moderate saturation rejects most
    architecture while keeping real skin.

    The luma floor is deliberately low (28, not 60): a high floor drops
    shadowed deep skin from the sample entirely, which biases every
    downstream metric toward the brightest part of the face. Measured on
    a deep-skin talking head, one face spanned y=69 (shadowed cheek) to
    y=214 (lit cheek) — a y>60 floor silently discards the lower third.

    A warm beige wall is the main false positive and is genuinely close
    to skin in chroma. Two bounds do most of the rejecting: cb>=97 (warm
    wall clusters tightly near cb 94, skin runs 100-118) and an upper
    limit on cr-cb (wall ~64, skin ~48-55). Measured on that same frame
    this cut wall leakage 58% -> 20% while keeping 14.7% of frame as
    skin. Separation is imperfect by nature — always spot-check with
    --debug on new footage rather than trusting the number."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
    cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    return (
        (cb >= 97) & (cb <= 122) & (cr >= 138) & (cr <= 170) & ((cr - cb) <= 58)
        & (y > LUMA_FLOOR) & (y < 235) & (sat > 0.15) & (sat < 0.70)
    )


def hue_sat_luma(px):
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    mx, mn = px.max(axis=1), px.min(axis=1)
    delta = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / delta) % 6,
        np.where(mx == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60.0
    s = np.where(mx > 0, delta / np.maximum(mx, 1e-6), 0)
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # circular mean of hue
    rad = np.deg2rad(h)
    mean_h = np.rad2deg(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())) % 360
    return mean_h, s.mean() * 100, y.mean()


def density(px):
    """Modeling metrics over skin pixels: luma spread, saturation floor, specular ceiling."""
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    mx, mn = px.max(axis=1), px.min(axis=1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0) * 100
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    spread = np.percentile(y, 90) - np.percentile(y, 10)
    return spread, np.percentile(s, 10), np.percentile(y, 99)


def rel(new, old):
    return (new - old) / max(abs(old), 1e-6) * 100


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    debug = '--debug' in sys.argv
    orig, graded = load(args[0]), load(args[1])
    if orig.shape != graded.shape:
        h = min(orig.shape[0], graded.shape[0]); w = min(orig.shape[1], graded.shape[1])
        orig, graded = orig[:h, :w], graded[:h, :w]

    mask = skin_mask(orig)
    frac = mask.mean()
    if frac < MIN_SKIN_FRACTION:
        print(f"skin: {frac*100:.2f}% of frame — too little to judge (b-roll?). SKIP")
        sys.exit(0)

    if debug:
        vis = orig.copy()
        vis[~mask] *= 0.25                      # dim everything the gate ignores
        Image.fromarray(vis.astype(np.uint8)).save('skinmask_debug.jpg', quality=90)
        print("wrote skinmask_debug.jpg (lit pixels = what the gate measures)")

    h0, s0, y0 = hue_sat_luma(orig[mask])
    h1, s1, y1 = hue_sat_luma(graded[mask])
    sp0, fl0, pk0 = density(orig[mask])
    sp1, fl1, pk1 = density(graded[mask])

    dh = (h1 - h0 + 180) % 360 - 180  # signed shortest hue distance
    ds = rel(s1, s0)
    dy = y1 - y0
    dsp, dfl, dpk = rel(sp1, sp0), rel(fl1, fl0), rel(pk1, pk0)

    print(f"skin px: {frac*100:.1f}% of frame")
    print(f"hue:  {h0:.1f} -> {h1:.1f} deg  (shift {dh:+.1f} deg)")
    print(f"sat:  {s0:.1f}% -> {s1:.1f}%  ({ds:+.1f}% relative)")
    print(f"luma: {y0:.0f} -> {y1:.0f}  ({dy:+.0f})")
    print(f"density  spread {sp0:.1f} -> {sp1:.1f} ({dsp:+.1f}%) | "
          f"sat floor {fl0:.1f} -> {fl1:.1f} ({dfl:+.1f}%) | "
          f"specular {pk0:.0f} -> {pk1:.0f} ({dpk:+.1f}%)")

    # --- hue / saturation failures (wrong skin colour) ---
    if abs(dh) >= HUE_FAIL or abs(ds) >= SAT_FAIL:
        print("VERDICT: FAIL — grade breaks skin; rethink (fix WB first? wrong look?)")
        sys.exit(2)

    # --- density failures (right colour, dead skin) ---
    if -dsp >= SPREAD_FAIL or -dfl >= FLOOR_FAIL:
        print("VERDICT: FAIL (ASHY) — skin lost its modeling. Anchor the black floor at 0/0, "
              "replace any eq=saturation<1 with vibrance, and keep the white anchor >=0.96.")
        sys.exit(2)
    if -dsp >= SPREAD_SOFTEN or -dfl >= FLOOR_SOFTEN or -dpk >= SPEC_SOFTEN:
        print("VERDICT: SOFTEN (ASHY) — skin is flattening: less contrast/saturation inside "
              "the face. Halve the matte lift and re-check.")
        sys.exit(1)

    if abs(dh) >= HUE_SOFTEN or abs(ds) >= SAT_SOFTEN:
        print("VERDICT: SOFTEN — halve the look strength and re-check")
        sys.exit(1)
    print("VERDICT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
