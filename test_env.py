import subprocess
import os
import sys

env = os.environ.copy()
env['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

try:
    result = subprocess.run(
        ['gemini-cli', '--version'],
        capture_output=True,
        text=True,
        timeout=15,
        shell=True,
        env=env
    )
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")
