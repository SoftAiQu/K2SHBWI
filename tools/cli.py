"""Simple CLI for K2SHBWI encode/decode operations.

Usage examples:
  python -m tools.cli encode --image tests/assets/sample.png --out out.k2sh --adaptive
  python -m tools.cli decode --file out.k2sh --outdir ./out
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'src' package can be imported when running this script directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.encoder import K2SHBWIEncoder
from src.core.decoder import K2SHBWIDecoder
from src.algorithms.registry import registry, init_registry
from PIL import features as _pil_features
import sys

# Initialize algorithm registry
init_registry()


def cmd_encode(args):
    enc = K2SHBWIEncoder()
    # Set compression algorithm if specified
    if hasattr(args, 'algorithm'):
        setattr(enc, 'compression_algorithm', args.algorithm)
    enc.adaptive_compression = args.adaptive
    # wire pyramid enable and quality
    enc.image_pyramid_enabled = bool(getattr(args, 'pyramid', False))
    enc.pyramid_quality = int(getattr(args, 'pyramid_quality', args.pyramid_quality)) if hasattr(args, 'pyramid_quality') else args.pyramid_quality
    if args.image:
        enc.set_image(str(args.image))
    if args.metadata:
        with open(args.metadata, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        enc.add_metadata(meta)
    if args.hotspots:
        with open(args.hotspots, 'r', encoding='utf-8') as f:
            hotspots = json.load(f)
        for h in hotspots:
            coords = tuple(h.get('coords', (0,0,0,0)))
            enc.add_hotspot(coords, h.get('data', {}))
    if args.layers:
        with open(args.layers, 'r', encoding='utf-8') as f:
            layers = json.load(f)
        for k, v in layers.items():
            enc.add_data_layer(k, v)

    # If pyramid requested, wire parsed formats (or enable auto-selection)
    if getattr(args, 'pyramid', False):
        parsed = getattr(args, '_parsed_pyramid_formats', None)
        if parsed:
            # assign explicit formats to encoder
            enc.pyramid_level_formats = parsed  # type: ignore
            # If user explicitly asked for webp but runtime lacks support, warn
            if 2 in parsed:
                try:
                    webp_ok = _pil_features.check('webp')
                except Exception:
                    webp_ok = False
                if not webp_ok:
                    print('Warning: WEBP was requested for pyramid levels but this Python/Pillow build does not support WEBP; WEBP will be skipped and PNG/JPEG used instead.', file=sys.stderr)
        else:
            # No explicit formats -> enable auto-selection in encoder
            enc.pyramid_level_formats = None

    out_path = Path(args.out)
    enc.encode(str(out_path))
    print(f"Wrote: {out_path}")


def cmd_decode(args):
    dec = K2SHBWIDecoder()
    dec.decode(str(args.file))
    outdir = Path(args.outdir or '.')
    outdir.mkdir(parents=True, exist_ok=True)
    # Write metadata
    md = dec.get_metadata()
    if md:
        with open(outdir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(md, f, indent=2)
    # Write image
    img = dec.get_image()
    if img:
        img.save(outdir / 'image.png')
    # Write hotspots and layers
    with open(outdir / 'hotspots.json', 'w', encoding='utf-8') as f:
        import json as _json
        _json.dump(dec.get_hotspots(), f, indent=2)
    with open(outdir / 'data_layers.json', 'w', encoding='utf-8') as f:
        import json as _json
        _json.dump(dec.data_layers, f, indent=2)
    print(f"Extracted contents to {outdir}")


def main():
    p = argparse.ArgumentParser(prog='k2sh-cli')
    sub = p.add_subparsers(dest='cmd')

    e = sub.add_parser('encode')
    e.add_argument('--image', type=Path, help='Path to base image')
    e.add_argument('--metadata', type=Path, help='Path to metadata JSON')
    e.add_argument('--hotspots', type=Path, help='Path to hotspots JSON')
    e.add_argument('--layers', type=Path, help='Path to data layers JSON')
    e.add_argument('--out', required=True, help='Output .k2sh file')
    e.add_argument('--adaptive', action='store_true', help='Enable adaptive compression')
    e.add_argument('--algorithm', choices=registry.list_compression_algos(),
                  default='smart', help='Choose compression algorithm')
    e.add_argument('--pyramid', action='store_true', help='Enable image pyramid generation')
    e.add_argument('--pyramid-formats', type=str, help='Comma-separated per-level formats (png,jpeg,webp)')
    e.add_argument('--pyramid-quality', type=int, default=80, help='Quality for JPEG/WEBP levels (0-100)')

    d = sub.add_parser('decode')
    d.add_argument('--file', type=Path, required=True, help='Input .k2sh file')
    d.add_argument('--outdir', type=Path, help='Output directory')

    args = p.parse_args()
    if args.cmd == 'encode':
        # wire pyramid options
        if getattr(args, 'pyramid', False):
            # parse formats if provided
            if getattr(args, 'pyramid_formats', None) or getattr(args, 'pyramid-formats', None):
                # support either attribute name style
                fmt_str = getattr(args, 'pyramid_formats', None) or getattr(args, 'pyramid-formats', None)
            else:
                fmt_str = args.pyramid_formats if hasattr(args, 'pyramid_formats') else None
            args._parsed_pyramid_formats = None
            if fmt_str:
                parts = [p.strip().lower() for p in fmt_str.split(',')]
                mapping = []
                for p in parts:
                    if p in ('png', '0'):
                        mapping.append(0)
                    elif p in ('jpeg', 'jpg', '1'):
                        mapping.append(1)
                    elif p in ('webp', '2'):
                        mapping.append(2)
                    else:
                        mapping.append(0)
                args._parsed_pyramid_formats = mapping
        cmd_encode(args)
    elif args.cmd == 'decode':
        cmd_decode(args)
    else:
        p.print_help()


if __name__ == '__main__':
    main()