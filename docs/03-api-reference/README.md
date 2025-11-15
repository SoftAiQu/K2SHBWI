# 🛠️ API Reference

This folder contains technical API documentation for developers.

## 📚 What's in This Folder?

| File | Purpose | For |
|------|---------|-----|
| **01-core-api.md** | K2SHBWIBuilder and K2SHBWIViewer | Python developers |
| **02-encoder-decoder.md** | Low-level encoding/decoding | Advanced developers |
| **03-converters-api.md** | HTMLConverter, PDFConverter, etc. | Format conversion |
| **04-algorithms.md** | Compression algorithms | Algorithm researchers |
| **05-viewer-api.md** | Web and desktop viewer API | Integration developers |
| **06-plugin-system.md** | Creating custom plugins | Plugin developers |

## 🎯 Choose Your Reference

### "I want to create K2SH files programmatically"
→ Read `01-core-api.md`

### "I need low-level encoder/decoder details"
→ Read `02-encoder-decoder.md`

### "I want to convert formats programmatically"
→ Read `03-converters-api.md`

### "I want compression algorithm details"
→ Read `04-algorithms.md`

### "I want to embed the viewer in my app"
→ Read `05-viewer-api.md`

### "I want to create a custom plugin"
→ Read `06-plugin-system.md`

## 📊 API Reference Levels

| Level | Description | Files |
|-------|-------------|-------|
| 🟢 **Basic** | High-level APIs, simple usage | 01, 05 |
| 🟡 **Intermediate** | More detailed, specific use cases | 03, 06 |
| 🔴 **Advanced** | Low-level details, optimization | 02, 04 |

## 🔗 Related Documentation

- 📖 **Learning by examples?** → `/docs/02-guides/`
- 📚 **Want use cases?** → `/docs/08-use-cases/`
- 🔍 **Need specifications?** → `/docs/07-specifications/`
- 🤝 **Want to contribute?** → `/docs/05-contributing/`

## ✅ Prerequisites

- ✅ Python 3.8+ installed
- ✅ K2SHBWI installed
- ✅ Comfortable with Python programming
- ✅ Understanding of image formats (helpful but not required)

## 💻 Quick API Overview

### Creating a K2SH File
```python
from k2shbwi import K2SHBWIBuilder

builder = K2SHBWIBuilder()
builder.set_base_image("image.png")
builder.add_hotspot(coords=(100, 100, 300, 300), data={"info": "Click me!"})
builder.build("output.k2sh")
```

### Reading a K2SH File
```python
from k2shbwi import K2SHBWIViewer

viewer = K2SHBWIViewer("file.k2sh")
image = viewer.get_base_image()
hotspots = viewer.get_hotspots()
```

### Converting Formats
```python
from k2shbwi.converters import HTMLConverter

converter = HTMLConverter()
converter.convert("page.html", "output.k2sh")
```

## 📝 File Descriptions

### 01-core-api.md
High-level API for working with K2SH files:
- K2SHBWIBuilder class
- K2SHBWIViewer class
- Common methods and properties
- Error handling
- Examples

### 02-encoder-decoder.md
Low-level encoding/decoding operations:
- Encoding process
- Decoding process
- Binary format details
- Performance notes
- Advanced optimization

### 03-converters-api.md
APIs for converting other formats:
- HTMLConverter
- PDFConverter
- PowerPointConverter
- CustomConverter creation
- Options and settings

### 04-algorithms.md
Compression and algorithm details:
- Available algorithms
- Algorithm selection
- Compression parameters
- Performance characteristics
- When to use each algorithm

### 05-viewer-api.md
APIs for viewing K2SH files:
- Web viewer API
- Desktop viewer API
- Embedding viewers
- Custom viewers
- Event handling

### 06-plugin-system.md
Creating custom plugins:
- Plugin interface
- Lifecycle hooks
- Data access
- Example plugins
- Distribution

## 🔗 Code Examples

All API files include:
- ✅ Basic examples
- ✅ Advanced examples
- ✅ Common patterns
- ✅ Error handling
- ✅ Performance tips

## 📚 Learning Path

**For Python developers:**
1. Start with `01-core-api.md`
2. Try the examples in guides
3. Reference `04-algorithms.md` for optimization
4. Check `06-plugin-system.md` if extending

**For format conversion:**
1. Read `03-converters-api.md`
2. Review `07-specifications.md` for format details
3. Check examples in guides

**For viewer integration:**
1. Read `05-viewer-api.md`
2. Review embedded examples
3. Check `/docs/02-guides/04-using-viewers.md`

## ⚠️ Important Notes

- All examples tested and working
- API is stable as of v1.0
- Breaking changes documented in releases
- Performance tips included where relevant

## 🆘 Getting Help

- Check `/docs/06-faq/` for common questions
- Review examples in `/docs/08-use-cases/`
- See `/docs/02-guides/` for step-by-step tutorials
- Check GitHub issues for known problems

---

**Last Updated:** November 16, 2025
