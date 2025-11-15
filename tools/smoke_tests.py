import sys
from pathlib import Path

# Ensure project root is on sys.path so 'src' package can be imported when running this script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

print('Starting smoke tests...')
errors = []

# HotspotMapper test
try:
    from src.creator.hotspot_mapper import HotspotMapper
    hm = HotspotMapper(800, 600)
    hid = hm.add_hotspot((10, 10, 100, 100), {'title': 't1'})
    found = hm.find_hotspot_at_point(50, 50)
    assert found is not None and found.id == hid
    all_map = hm.export_map()
    assert isinstance(all_map, list) and len(all_map) >= 1
    print('HotspotMapper: OK')
except Exception as e:
    errors.append(('HotspotMapper', str(e)))

# DataLayerManager test
try:
    from src.creator.data_layer import DataLayer, DataLayerManager
    mgr = DataLayerManager()
    lid1 = mgr.add_layer({'a': 1, 'b': {'c': 2}})
    lid2 = mgr.add_layer({'a': 1, 'b': {'c': 3}})
    layer1 = mgr.get_layer(lid1)
    assert layer1 is not None
    similar = mgr.find_similar_layers(layer1)
    print('DataLayerManager: OK (layers added, similar count=', len(similar), ')')
except Exception as e:
    errors.append(('DataLayerManager', str(e)))

# Validator test
try:
    from src.creator.validator import K2SHBWIValidator
    from PIL import Image
    validator = K2SHBWIValidator()
    img = Image.new('RGB', (512, 512), color=(255, 0, 0))
    ok = validator.validate_all(img, [], {'title':'test'}, {})
    # Should return True but may have warnings if no hotspots; we'll just ensure no exception
    print('Validator: OK (valid returned:', ok, ')')
except Exception as e:
    errors.append(('Validator', str(e)))

# Builder smoke test (writes test_output.k2sh)
try:
    from src.creator.builder import K2SHBWIBuilder
    from PIL import Image
    tmp_img = Path('tools') / 'smoke_sample.png'
    Image.new('RGB', (512, 512), color=(128, 128, 200)).save(tmp_img)
    builder = K2SHBWIBuilder()
    builder.set_base_image(str(tmp_img))
    hid = builder.add_hotspot((20, 20, 120, 120), {'title': 'smoke'})
    out = Path('test_output.k2sh')
    builder.build(str(out), validate=False, verbose=False)
    assert out.exists()
    print('Builder smoke test: OK (wrote', out, ')')
except Exception as e:
    errors.append(('Builder', str(e)))

print('\nSmoke test summary:')
if errors:
    for name, msg in errors:
        print(' -', name, 'FAILED:', msg)
    sys.exit(2)
else:
    print('All smoke tests passed')
    sys.exit(0)
