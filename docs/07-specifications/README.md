# 🏗️ Technical Specifications

This folder contains detailed technical specifications for K2SHBWI format and components.

## 📚 What's in This Folder?

| File | Purpose |
|------|---------|
| **01-k2sh-format-spec.md** | Complete K2SH file format specification |
| **02-compression-algorithms.md** | Available algorithms and details |
| **03-metadata-format.md** | Metadata structure and fields |
| **04-hotspot-specification.md** | Hotspot definition and coordinates |
| **05-encoding-details.md** | Encoding process technical details |
| **06-security-specifications.md** | Security features (current & planned) |

## 🎯 Who Should Read This?

### Format Designers
→ Read `01-k2sh-format-spec.md` (complete format details)

### Developers (Compression)
→ Read `02-compression-algorithms.md` (algorithm details)

### Developers (Metadata)
→ Read `03-metadata-format.md` (metadata structure)

### Developers (Hotspots)
→ Read `04-hotspot-specification.md` (coordinate systems)

### Low-level Developers
→ Read `05-encoding-details.md` (binary format)

### Security Researchers
→ Read `06-security-specifications.md` (encryption & safety)

## 📖 Quick Overview

### K2SH Format Structure
```
┌─────────────────────────────────┐
│ Header (32 bytes)               │
│ - Magic: "K2SH" (4 bytes)       │
│ - Version: 1.0 (2 bytes)        │
│ - Flags (2 bytes)               │
│ - Reserved (24 bytes)           │
├─────────────────────────────────┤
│ Metadata (variable)             │
│ - Author, date, description     │
│ - Compression settings          │
├─────────────────────────────────┤
│ Image Pyramid                   │
│ - Thumbnail (256x256)           │
│ - Low-res (1024x1024)           │
│ - Medium (2048x2048)            │
│ - High-res (full)               │
├─────────────────────────────────┤
│ Hotspot Map                     │
│ - Coordinates, IDs, types       │
├─────────────────────────────────┤
│ Data Layers (compressed)        │
│ - Layer 0 data                  │
│ - Layer 1 data                  │
│ - ...                           │
├─────────────────────────────────┤
│ Index & CRC                     │
│ - Offset index                  │
│ - Checksum verification         │
└─────────────────────────────────┘
```

### Available Compression Algorithms
- **Images:** WebP, JPEG-XL, PNG, AVIF
- **Data:** Brotli, ZSTD, LZ4
- **Special:** Differential, Deduplication

### Supported Image Formats
- ✅ JPEG/JPG
- ✅ PNG
- ✅ WebP
- ✅ TIFF
- ✅ BMP
- ✅ GIF (single frame)

### File Size Characteristics
- **Minimum:** ~50 KB (tiny image, no data)
- **Typical:** 300-500 KB (1-2 MB base image + data)
- **Maximum:** Tested to 5+ GB (with compression)
- **Compression ratio:** 90-95% typical

## 📊 Technical Specifications

### Version Information
- **Current Version:** 1.0
- **Format Stability:** Stable (no breaking changes expected)
- **Backward Compatibility:** Maintained

### Performance Targets
- **Load time:** <100ms (first 50% visible)
- **Interaction latency:** <20ms
- **Memory usage:** <500MB typical
- **Compression time:** <5 seconds average

### Limits
- **Image dimensions:** Up to 16384x16384
- **Hotspots:** Up to 10,000 per file
- **Data size:** No fixed limit
- **Metadata fields:** 128 per file

## 🔐 Security Features

### Current (v1.0)
- ✅ CRC checksums
- ✅ Format validation
- ✅ Safe extraction

### Coming (v1.1-1.2)
- 🔹 AES-256 encryption
- 🔹 Digital signatures
- 🔹 Access control

## 🔗 Related Documentation

- 📖 **Guides:** `/docs/02-guides/`
- 🛠️ **API Reference:** `/docs/03-api-reference/`
- 📚 **Use Cases:** `/docs/08-use-cases/`

## ✅ Reading Prerequisites

- ✅ Basic understanding of binary formats
- ✅ Familiarity with compression algorithms
- ✅ Understanding of image file formats
- ✅ Some experience with Python (optional)

## 💡 Quick Reference

### Magic Bytes
```
Offset: 0x00-0x03
Value: 0x4B325348 (ASCII: "K2SH")
```

### Version Field
```
Offset: 0x04-0x05
Format: Little-endian uint16
v1.0 = 0x0100
```

### Flags Byte (0x06)
```
Bit 0: Has encryption
Bit 1: Has audio
Bit 2: Has video
Bit 3: Has 3D
Bit 4: Has animation
Bits 5-7: Reserved
```

## 📝 File Descriptions

### 01-k2sh-format-spec.md
Complete format specification:
- File header structure
- Section definitions
- Data types
- Encoding rules
- Examples with byte offsets

### 02-compression-algorithms.md
Compression algorithm details:
- Available algorithms
- When to use each
- Performance characteristics
- Configuration options
- Benchmarks

### 03-metadata-format.md
Metadata structure:
- Required fields
- Optional fields
- Field encoding
- Size limits
- Examples

### 04-hotspot-specification.md
Hotspot definition:
- Coordinate systems
- Supported shapes
- Data association
- Z-ordering
- Performance notes

### 05-encoding-details.md
Encoding process:
- Step-by-step process
- Memory requirements
- Performance optimization
- Error handling

### 06-security-specifications.md
Security features:
- Current security model
- Encryption plans
- Signature verification
- Threat model
- Best practices

## 🧮 Math & Algorithms

All files include:
- ✅ Algorithm explanations
- ✅ Pseudocode
- ✅ Performance analysis
- ✅ Worked examples

## 📚 Learning Path

**For format understanding:**
1. Start with `01-k2sh-format-spec.md`
2. Read `03-metadata-format.md`
3. Understand `04-hotspot-specification.md`
4. Review `05-encoding-details.md`

**For implementation:**
1. Read `02-compression-algorithms.md`
2. Study `05-encoding-details.md`
3. Check `/docs/03-api-reference/02-encoder-decoder.md`
4. Review examples in `/docs/02-guides/`

**For optimization:**
1. Study `02-compression-algorithms.md`
2. Review performance data
3. Check benchmarks
4. Follow best practices

## 🛠️ Tool Integration

Specifications support:
- ✅ Custom encoder implementations
- ✅ Format converters
- ✅ Validation tools
- ✅ Debugging utilities

## 📞 Questions or Issues?

- 📧 Email: specs@k2shbwi.org
- 🐦 Twitter: @k2shbwi
- 💬 GitHub: https://github.com/k2shbwi/k2shbwi/discussions

---

**Last Updated:** November 16, 2025

**Complete and detailed technical reference for K2SHBWI format** 📋
