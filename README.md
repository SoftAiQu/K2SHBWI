# K2SHBWI - Image Metadata & Hotspot Management Tool

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Tests](https://img.shields.io/badge/Tests-19%2F19%20Passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)

[![K2SHBWI Native Format](https://img.shields.io/badge/🎨%20View%20Native%20K2SHBWI%20Format-Historic%20First%20%7C%20GitHub%20Renders%20Natively-9C27B0?style=for-the-badge)](https://htmlpreview.github.io/?https://github.com/Ritam-jash/K2SHBWI/blob/main/demo/formats/k2shbwi/sample_format.k2shbwi)

## Overview

K2SHBWI embeds **rich metadata and interactive hotspots** directly into image files without modifying the original image data.

### Key Features

- 📸 **Add Metadata** - Annotations, descriptions, custom data
- 🎯 **Interactive Hotspots** - Clickable regions with links
- 🔄 **Multi-Format Export** - HTML, PDF, PowerPoint
- 📊 **Batch Processing** - Convert hundreds of images
- 🔍 **Validation** - Ensure file integrity

### Use Cases

**E-commerce** • **Education** • **Documentation** • **Presentations** • **Digital Archives**

---

## 🎨 Experience K2SHBWI Live!

### 📦 View the Native Format Package

**Click below to see the complete `.k2shbwi` format** - rendered live in your browser!


[![K2SHBWI ULTIMATE](https://img.shields.io/badge/🎨%20ULTIMATE-Historic%20First%20%7C%2087.3%25%20Compression%20%7C%20Zero%20Setup-FF6B00?style=for-the-badge)](https://ghproxy.com/https://raw.githubusercontent.com/Ritam-jash/K2SHBWI/main/demo/formats/k2shbwi/sample_format.k2shbwi)

This interactive package includes:
- ✅ Performance metrics & specifications
- ✅ Research data & analysis
- ✅ Complete format manifest
- ✅ 100% offline capability

**Other sample formats:**
- [Interactive HTML](demo/formats/interactive/index.html)
- [Sample Gallery](demo/formats/)
- [Full Showcase](demo/showcase_hub.html)

---

## Quick Start

### Installation

```bash
cd K2SHBWI
python -m venv venv
.\venv\Scripts\activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### Basic Usage

```bash
# Create K2SHBWI file
python tools/cli_click.py create -i photo.png -o output.k2sh -t "My Photo"

# View file info
python tools/cli_click.py info output.k2sh

# Validate integrity
python tools/cli_click.py validate output.k2sh

# Extract image
python tools/cli_click.py decode output.k2sh -o extracted.png

# Convert formats
python tools/cli_click.py convert output.k2sh -f html -o output.html
python tools/cli_click.py convert output.k2sh -f pdf -o output.pdf
python tools/cli_click.py convert output.k2sh -f pptx -o output.pptx

# View in browser
python tools/cli_click.py view output.k2sh

# Batch process
python tools/cli_click.py batch -i input_dir -o output_dir
```

---

## 8 Main Commands

| Command | Purpose | Example |
|---------|---------|---------|
| **create** | Create K2SHBWI from image | `create -i img.png -o out.k2sh -t "Title"` |
| **info** | Display file information | `info output.k2sh -v` |
| **validate** | Check file integrity | `validate output.k2sh` |
| **batch** | Process directory | `batch -i input/ -o output/` |
| **encode** | Low-level encode | `encode -i img.png -o out.k2sh` |
| **decode** | Extract image | `decode out.k2sh -o img.png` |
| **convert** | Export to formats | `convert out.k2sh -f html -o out.html` |
| **view** | Open viewer | `view out.k2sh -t web` |

### Command Details

#### Create
```bash
python tools/cli_click.py create \
  -i image.png \
  -o output.k2sh \
  -t "Image Title" \
  -d "Description" \
  -m '{"custom": "value"}' \
  -v
```

#### Convert (HTML/PDF/PPTX)
```bash
# HTML - Interactive web viewer
python tools/cli_click.py convert file.k2sh -f html -o output.html

# PDF - Professional document
python tools/cli_click.py convert file.k2sh -f pdf -o output.pdf

# PPTX - Multi-slide presentation
python tools/cli_click.py convert file.k2sh -f pptx -o output.pptx
```

#### View (Web/Desktop)
```bash
# Web browser viewer
python tools/cli_click.py view file.k2sh -t web

# Desktop GUI viewer
python tools/cli_click.py view file.k2sh -t desktop
```

---

## Documentation

### Quick Navigation

| Need | Location |
|------|----------|
| **Getting Started** | `docs/01-getting-started/` |
| **Usage Guides** | `docs/02-guides/` |
| **API Reference** | `docs/03-api-reference/` |
| **FAQ** | `docs/06-faq/` |
| **Contributing** | `CONTRIBUTING.md` |
| **Documentation Hub** | `docs/00-index.md` |

### Documentation Structure

```
docs/
├── 00-index.md              # Documentation hub
├── 01-getting-started/      # Installation & setup
├── 02-guides/               # How-to guides
├── 03-api-reference/        # API documentation
├── 04-roadmap/              # Future plans
├── 05-contributing/         # Contributing guidelines
├── 06-faq/                  # FAQ
├── 07-specifications/       # Technical specs
└── 08-use-cases/            # Real-world examples
```

---

## Project Structure

```
K2SHBWI/
├── src/                     # Core source code
│   ├── algorithms/          # 17+ optimization algorithms
│   ├── converters/          # HTML, PDF, PPTX converters
│   ├── core/                # Encoder, decoder, validator
│   ├── creator/             # Builder modules
│   ├── utils/               # Utilities
│   └── viewers/             # Web & desktop viewers
│
├── tools/                   # CLI tools
│   ├── cli_click.py         # Main CLI (8 commands)
│   └── [10+ utility scripts]
│
├── tests/                   # Test suite (19 tests)
│   ├── comprehensive_test_suite.py
│   └── [15+ test modules]
│
├── docs/                    # Documentation (8 sections)
├── demo/                    # Demo platform
├── logs/                    # Logs & metrics
├── examples/                # Usage examples
└── requirements*.txt        # Dependencies
```

---

## Dependencies

### Core Requirements (Required)

```bash
pip install -r requirements.txt
```

**Includes:** Click, Pillow, python-pptx, beautifulsoup4, numpy, pytest, brotli, zstandard

### Optional Requirements

```bash
# Demo platform
pip install -r requirements-demo.txt

# Development tools
pip install -r requirements-dev.txt

# Install everything
pip install -r requirements.txt -r requirements-demo.txt -r requirements-dev.txt
```

---

## Testing

### Run Test Suite

```bash
# Run all 19 tests
python comprehensive_test_suite.py
```

**Current Results:**
```
[PASS] Passed:  19
[FAIL] Failed:  0
[TIME] Time:    ~20 seconds

*** ALL TESTS PASSED! ***
```

### Test Coverage

- ✅ 8 CLI commands
- ✅ 3 format converters
- ✅ 2 viewer modules
- ✅ Core encoding/decoding
- ✅ Validation & integrity

---

## Architecture

### Core Components

**Encoder** (`src/core/encoder.py`)
- Converts images to K2SHBWI format
- Embeds metadata and hotspots

**Decoder** (`src/core/decoder.py`)
- Extracts data from K2SHBWI files
- Validates file integrity

**Converters** (`src/converters/`)
- **HTMLConverter**: Interactive web viewer
- **PDFConverter**: Professional documents
- **PPTXConverter**: PowerPoint presentations

**Viewers** (`src/viewers/`)
- **WebViewer**: Browser-based viewer
- **DesktopViewer**: Tkinter GUI

---

## Performance

- **Test execution**: ~20 seconds (19 tests)
- **Create command**: <100ms
- **HTML conversion**: <50ms
- **PDF conversion**: <100ms
- **PPTX conversion**: <150ms
- **Batch processing**: ~300ms for 3 images

---

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'src.core.encoder'"**
```bash
# Ensure you're in project root
cd K2SHBWI
python tools/cli_click.py --help
```

**"Missing option '-o' / '--output'"**
```bash
# Correct: specify output path
python tools/cli_click.py convert file.k2sh -f html -o output.html
```

**"File not found" errors**
```bash
# Use absolute or relative paths from project root
python tools/cli_click.py info ./output.k2sh
```

**Desktop Viewer not opening**
```bash
# Use web viewer instead
python tools/cli_click.py view file.k2sh -t web
```

---

## Verbose Mode

Enable detailed output with `-v` flag:

```bash
python tools/cli_click.py create -i img.png -o out.k2sh -v
python tools/cli_click.py convert out.k2sh -f html -o out.html -v
```

---

## Privacy & Security

### Public (GitHub)

✅ `/docs/` - User documentation  
✅ `/src/` - Open-source code  
✅ `/tools/` - CLI utilities  
✅ `/tests/` - Test suite  

### Private (Local Only - `.gitignore`)

🔒 `/logs/logs_development/` - Development history  
🔒 `/internal_docs/` - Internal analysis  
🔒 `/Project_Detailds/` - Sensitive algorithms  
🔒 `/Redundant_&_Unnecessary_doc/` - Redundant documentation  
🔒 `/docs/08-archive/` - Historical documentation  

---

## Contributing

1. Make changes to relevant modules
2. Update tests in `comprehensive_test_suite.py`
3. Run test suite: `python comprehensive_test_suite.py`
4. Ensure all 19 tests pass
5. Update README if adding features

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

---

## License

MIT License - See [`LICENSE`](LICENSE) for details.

---

## Version

**v1.0.0** - Click Migration Complete
- ✅ 19/19 tests passing
- ✅ 8 commands implemented
- ✅ 3 format converters
- ✅ Full documentation

---

**Last Updated:** November 19, 2025  
**Status:** ✅ Complete - All Tests Passing  
**Test Score:** 19/19 (100%)