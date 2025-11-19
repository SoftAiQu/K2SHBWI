SSIM and CI notes
==================

Recommendations for contributors and CI regarding SSIM-based heuristics used by the encoder:

- Dependencies
  - For best speed and accuracy install:
    - numpy
    - scikit-image (provides structural_similarity implementation)
  - Pillow should include WebP support if you want WEBP output; install system `libwebp` or `pillow[webp]` where available.

- Defaults
  - The encoder now enables `pyramid_use_ssim = True` by default to prefer perceptual similarity when choosing lossy formats for pyramid levels.
  - A safe, downsampled pure-Python fallback is used when NumPy/skimage are not available; this keeps CI fast and deterministic.

- CI guidance (suggested)
  - In CI jobs where you want the most accurate heuristics and the micro-benchmark run, install `numpy` and `scikit-image` in the environment before running tests/benchmarks.
  - Example (GitHub Actions):

    - name: Install deps
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-ci.txt

- Performance
  - The code includes a small micro-benchmark script under `tools/ssim_benchmark.py` to compare the pure-Python fallback, NumPy vectorized path, and skimage path on representative images. Use it to tune thresholds or to decide whether to preinstall numpy/skimage in your CI.

Notes
- SSIM is used only to help decide whether lossy formats (WEBP/JPEG) are acceptable for a pyramid level; actual stored bytes are unchanged by SSIM (SSIM does not alter image data).
- If you want deterministic results across environments, enable `pyramid_use_ssim = False` in the encoder and pass explicit `pyramid_level_formats` via the CLI.

