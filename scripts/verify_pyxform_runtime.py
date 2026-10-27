"""Run inside the pinned pyxform candidate with read-only synthetic XLSX input."""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, '/app')
from main import app

path = Path('/control.xlsx')
before = path.read_bytes()
client = app().test_client()
response = client.post('/api/v1/convert', data=before,
                       headers={'X-XlsForm-FormId-Fallback': 'lastcopy_runtime_control'})
assert response.status_code == 200, response.get_json()
body = response.get_json()
xml = ET.fromstring(body['result'])
ns = {'x': 'http://www.w3.org/2002/xforms'}
instance = xml.find('.//x:instance', ns)
assert instance is not None and instance[0].attrib['id'] == 'lastcopy_runtime_control'
namespace = instance[0].tag.split('}', 1)[0] + '}' if instance[0].tag.startswith('{') else ''
assert instance[0].find(namespace + 'condition') is not None
assert client.post('/api/v1/convert', data=b'not a workbook').status_code == 400
assert path.read_bytes() == before
print(json.dumps({'status': 'passed', 'input_sha256': hashlib.sha256(before).hexdigest(),
                  'scope': 'Actual XLSForm conversion and Java validation; isolated network-none process',
                  'valid_conversion': 200, 'malformed_workbook': 400, 'input_unchanged': True}))
