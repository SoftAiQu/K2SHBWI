"""Micro-benchmark for SSIM implementations.

Compares three paths:
 - skimage.metrics.structural_similarity (if available)
 - NumPy vectorized SSIM (if numpy available)
 - Pure-Python downsampled fallback

Usage: python -m tools.ssim_benchmark
"""
import time
import json
from PIL import Image
import io
import random
import math
from pathlib import Path

def make_noise_image(size):
    img = Image.new('RGB', size)
    pixels = [ (random.randint(0,255), random.randint(0,255), random.randint(0,255)) for _ in range(size[0]*size[1]) ]
    img.putdata(pixels)
    return img

def make_solid_image(size, color=(128,128,128)):
    return Image.new('RGB', size, color=color)

def skimage_ssim(img1, img2):
    try:
        from skimage.metrics import structural_similarity as ssim
        import numpy as _np
        a = _np.asarray(img1.convert('L'))
        b = _np.asarray(img2.convert('L'))
        return float(ssim(a, b))
    except Exception:
        return None

def numpy_ssim(img1, img2):
    try:
        import numpy as _np
        a = _np.asarray(img1.convert('L'), dtype=_np.float32)
        b = _np.asarray(img2.convert('L'), dtype=_np.float32)
        if a.size == 0 or b.size == 0 or a.size != b.size:
            return None
        mean_a = a.mean()
        mean_b = b.mean()
        var_a = a.var(ddof=1)
        var_b = b.var(ddof=1)
        cov = _np.mean((a - mean_a) * (b - mean_b)) * (a.size / max(1, a.size - 1))
        L = 255.0
        C1 = (0.01 * L) ** 2
        C2 = (0.03 * L) ** 2
        denom1 = (mean_a * mean_a + mean_b * mean_b + C1)
        denom2 = (var_a + var_b + C2)
        if denom1 == 0 or denom2 == 0:
            return 0.0
        ssim_val = ((2 * mean_a * mean_b + C1) * (2 * cov + C2)) / (denom1 * denom2)
        return float(ssim_val)
    except Exception:
        return None

def pure_python_ssim(img1, img2, downsample=256):
    # downsample
    img1_small = img1.copy()
    img2_small = img2.copy()
    if max(img1_small.size) > downsample:
        img1_small.thumbnail((downsample, downsample), resample=Image.LANCZOS)
    if max(img2_small.size) > downsample:
        img2_small.thumbnail((downsample, downsample), resample=Image.LANCZOS)
    a_bytes = list(img1_small.convert('L').getdata())
    b_bytes = list(img2_small.convert('L').getdata())
    n = len(a_bytes)
    if n == 0 or n != len(b_bytes):
        return None
    mean_a = sum(a_bytes) / n
    mean_b = sum(b_bytes) / n
    var_a = sum((x - mean_a) ** 2 for x in a_bytes) / (n - 1 if n > 1 else 1)
    var_b = sum((y - mean_b) ** 2 for y in b_bytes) / (n - 1 if n > 1 else 1)
    cov = sum((a_bytes[i] - mean_a) * (b_bytes[i] - mean_b) for i in range(n)) / (n - 1 if n > 1 else 1)
    L = 255.0
    C1 = (0.01 * L) ** 2
    C2 = (0.03 * L) ** 2
    denom1 = (mean_a * mean_a + mean_b * mean_b + C1)
    denom2 = (var_a + var_b + C2)
    if denom1 == 0 or denom2 == 0:
        return 0.0
    ssim_val = ((2 * mean_a * mean_b + C1) * (2 * cov + C2)) / (denom1 * denom2)
    return float(ssim_val)

def time_func(func, a, b, runs=5):
    times = []
    result = None
    for _ in range(runs):
        t0 = time.perf_counter()
        result = func(a, b)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return (sum(times)/len(times), result)

def run():
    sizes = [(128,128), (256,256), (512,512), (1024,1024)]
    out = {}
    for size in sizes:
        a = make_noise_image(size)
        b = a.copy()
        # create a slightly different image for comparison too
        c = make_noise_image(size)
        entry = {}
        for name, fn in (('skimage', skimage_ssim), ('numpy', numpy_ssim), ('python', pure_python_ssim)):
            try:
                t, val = time_func(fn, a, b)
                t2, val2 = time_func(fn, a, c)
                entry[name] = {'same_ms': t*1000.0, 'diff_ms': t2*1000.0, 'same_score': val, 'diff_score': val2}
            except Exception as e:
                entry[name] = {'error': str(e)}
        out[f'{size[0]}x{size[1]}'] = entry
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    run()
