"""Run real pytest; retain its exact exit status and bounded native CI evidence.

The sandbox cannot download Actions logs from the redirected log-storage host.
Annotations retain failures/summaries without changing or replacing any test.
"""
import os
import subprocess
import sys

env = dict(os.environ, PYTHONIOENCODING='utf-8')
proc = subprocess.run([sys.executable, '-m', 'pytest', *sys.argv[1:]],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    encoding='utf-8', errors='replace', env=env)
print(proc.stdout, flush=True)
if os.getenv('GITHUB_ACTIONS'):
    retained = proc.stdout[-10000:] if proc.returncode else proc.stdout[-1200:]
    for index in range(0, len(retained), 2400):
        payload = retained[index:index + 2400].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::notice title=Real native pytest output::' + payload, flush=True)
sys.exit(proc.returncode)
