import json
from pathlib import Path
capture = json.loads(Path('/tmp/drive-samples.json').read_text())
phases = json.loads(Path('/tmp/drive-phases.json').read_text())
assert not capture['hardware_commands'], 'dry-run published to hardware command topic'
results = []
for phase in phases:
    name = phase['name']
    if name in ('discovery', 'arming'): continue
    margin = .4 if name == 'stale_status' else .35 if name == 'timeout' else .15
    values = [s for s in capture['samples'] if phase['start'] + margin < s[0] < phase['end']]
    assert len(values) >= 5, (name, 'missing output', len(values))
    moving = name in ('bounded', 'before_stop', 'rearmed')
    for _, x, z in values:
        assert abs(x - (.20 if moving else 0)) < 1e-9, (name, x)
        assert abs(z - (-.25 if moving else 0)) < 1e-9, (name, z)
    results.append(dict(phase=name, samples=len(values), passed=True))
print(json.dumps(dict(isolated=True, hardware_commands=0, results=results), indent=2))
