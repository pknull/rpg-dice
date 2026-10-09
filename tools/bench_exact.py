"""Reproducible timings for the exact engine.

Each expression runs in a fresh interpreter (first call, no warm caches),
three times; the script prints the fastest and slowest wall-clock seconds,
the number of joint outcomes and the unresolved explosion mass.

    venv/bin/python tools/bench_exact.py                 # default cases
    venv/bin/python tools/bench_exact.py '10d6kh3' ...   # chosen cases
    venv/bin/python tools/bench_exact.py --depth 20 '10d10>=8x>=10'
"""
import json
import platform
import subprocess
import sys

DEFAULT_CASES = ['10d6kh3', '10d10kh3', '8d6kh3', '4d6dl1', '2d20=+5kh1t>=15ns20nf1',
                 '5d6>=6f<=1', '10d10>=8x>=10', '20d6', '50d6', '100d6']

CHILD = '''
import json, sys, time
sys.path.insert(0, %r)
from dice_roller.exact import exact
start = time.perf_counter()
result = exact(%r, explode_depth=%d)
elapsed = time.perf_counter() - start
print(json.dumps({"seconds": elapsed, "outcomes": len(result.joint),
                  "unresolved": float(result.unresolved)}))
'''


def run(expression, depth, root, repeats=3):
    samples = []
    for _ in range(repeats):
        out = subprocess.run([sys.executable, '-c', CHILD % (root, expression, depth)],
                             capture_output=True, text=True, check=True, timeout=3600)
        samples.append(json.loads(out.stdout))
    times = sorted(s['seconds'] for s in samples)
    return times[0], times[-1], samples[0]['outcomes'], samples[0]['unresolved']


def main(argv):
    import pathlib
    root = str(pathlib.Path(__file__).resolve().parents[1])
    depth = 10
    if argv[:1] == ['--depth']:
        depth, argv = int(argv[1]), argv[2:]
    cases = argv or DEFAULT_CASES
    print(f'# python {platform.python_version()} on {platform.machine()}, '
          f'{platform.processor() or "unknown cpu"}; explode_depth={depth}')
    print(f'{"expression":32} {"best s":>9} {"worst s":>9} {"outcomes":>9} {"unresolved":>11}')
    for expression in cases:
        best, worst, outcomes, unresolved = run(expression, depth, root)
        print(f'{expression:32} {best:9.4f} {worst:9.4f} {outcomes:9d} {unresolved:11.3g}')


if __name__ == '__main__':
    main(sys.argv[1:])
