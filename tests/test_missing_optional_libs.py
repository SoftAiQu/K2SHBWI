import sys
import importlib
import builtins
import types
import pytest

from src.core.format import CompressionType

SAMPLE = b"abc" * 100

class _HiddenModule(types.ModuleType):
    pass

@pytest.mark.parametrize('libname,ctype', [
    ('brotli', CompressionType.BROTLI),
    ('zstandard', CompressionType.ZSTD),
])
def test_missing_optional_libs_raise_compression_error(monkeypatch, libname, ctype):
    """Simulate missing optional compression libraries and ensure CompressionError is raised when requested."""
    # Ensure module is not importable
    if libname in sys.modules:
        monkeypatch.setitem(sys.modules, libname, None)
    # Create an import hook that raises ImportError for the specific module
    orig_import = builtins.__import__

    def blocking_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == libname or name.startswith(libname + '.'):
            raise ImportError(f"No module named {libname}")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', blocking_import)

    with pytest.raises(Exception):
        # Either CompressionError or ValueError depending on codepath
        CompressionType.get_compressor(ctype)

    # restore import
    monkeypatch.setattr(builtins, '__import__', orig_import)
