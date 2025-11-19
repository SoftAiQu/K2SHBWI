# K2SHBWI Format Specification

## File Format Overview

### Magic Bytes
- First 4 bytes: `0x4B 0x32 0x53 0x48` (ASCII: "K2SH")
- Version (2 bytes): Major.Minor (e.g., 1.0)
- Flags (2 bytes): Feature flags

### File Structure
1. Header Section
2. Metadata Section
3. Image Pyramid Section
4. Hotspot Map
5. Data Layers

## Detailed Specification

### Header Format
```
┌─────────────────────────────────────────────┐
│ Magic Bytes (4 bytes): "K2SH"               │
│ Version (2 bytes): Major.Minor              │
│ Flags (2 bytes): Feature flags              │
│ Metadata Offset (8 bytes)                   │
│ Image Pyramid Offset (8 bytes)              │
│ Hotspot Map Offset (8 bytes)                │
│ Data Layers Offset (8 bytes)                │
│ Reserved (16 bytes): For future use         │
└─────────────────────────────────────────────┘
```

### Metadata Section
- Length (4 bytes)
- Compression Algorithm (1 byte)
- JSON Data Structure containing:
  - title
  - author
  - created_date
  - modified_date
  - description
  - tags
  - custom_fields