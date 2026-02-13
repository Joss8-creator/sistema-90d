import sys
import os
import shutil
import subprocess

def check_gemini():
    candidatos = []
    
    # 1. Scripts de Python
    scripts_path = os.path.join(sys.prefix, 'Scripts')
    candidatos.append(os.path.join(scripts_path, 'gemini-cli.exe'))
    candidatos.append(os.path.join(scripts_path, 'gemini.exe'))
    
    # User site path
    if hasattr(sys, 'getusersitepackages'):
            user_site = sys.getusersitepackages()
            user_scripts = os.path.normpath(os.path.join(user_site, '..', '..', 'Scripts'))
            candidatos.append(os.path.join(user_scripts, 'gemini-cli.exe'))
            candidatos.append(os.path.join(user_scripts, 'gemini.exe'))

    # 2. PATH global
    if shutil.which('gemini-cli'):
        candidatos.append('gemini-cli')
    if shutil.which('gemini'):
        candidatos.append('gemini')
    
    print(f"Candidatos: {candidatos}")
    
    for cmd in candidatos:
        if not cmd: continue
        if os.path.isabs(cmd) and not os.path.exists(cmd):
            print(f"[SKIP] {cmd} (no existe)")
            continue
            
        print(f"[TEST] {cmd}")
        try:
            res = subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=5, shell=True)
            print(f"  ReturnCode: {res.returncode}")
            print(f"  Stdout: {res.stdout.strip()[:100]}")
            print(f"  Stderr: {res.stderr.strip()[:100]}")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    check_gemini()
