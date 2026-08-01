import urllib.request
import zipfile
import os
import subprocess

def ensure_ninja_installed(modules_path):
    print("[Installer] Checking for Ninja...")
    """Downloads ninja.exe directly into modules_path if it doesn't exist."""
    ninja_exe = os.path.join(modules_path, "ninja.exe")
    
    if os.path.exists(ninja_exe):
        print("[Installer] Ninja executable found...")
        return ninja_exe

    print("[Installer] Downloading Ninja executable...")
    zip_path = os.path.join(modules_path, "ninja.zip")
    url = "https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-win.zip"
    
    try:
        # Download the standalone binary zip from GitHub
        urllib.request.urlretrieve(url, zip_path)
        
        # Extract ninja.exe directly into modules_path
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(modules_path)
            
        os.remove(zip_path) # Clean up zip
        print("[Installer] Ninja installed successfully.")
    except Exception as e:
        print(f"[Installer] Failed to download Ninja: {e}")
        
    return 

def setup_msvc_env(env):
    """Finds Visual Studio vcvarsall.bat and loads MSVC (cl.exe) variables into env."""
    vswhere_path = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    if not os.path.exists(vswhere_path):
        print("[Installer] Warning: vswhere.exe not found. Visual Studio installation could not be verified.")
        return env

    # Find MSVC installation folder
    try:
        vs_path = subprocess.check_output([
            vswhere_path,
            "-latest",
            "-products", "*",
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property", "installationPath"
        ], text=True).strip()

        if not vs_path:
            print("[Installer] Error: No valid Visual Studio C++ toolset found.")
            return env

        vcvars_bat = os.path.join(vs_path, r"VC\Auxiliary\Build\vcvarsall.bat")
        if not os.path.exists(vcvars_bat):
            print(f"[Installer] Error: vcvarsall.bat not found at {vcvars_bat}")
            return env

        print(f"[Installer] Found MSVC at: {vs_path}")
        # Run vcvarsall.bat and dump environment variables
        cmd = f'"{vcvars_bat}" x64 && set'
        output = subprocess.check_output(cmd, shell=True, text=True)

        for line in output.splitlines():
            if "=" in line:
                key, val = line.split("=", 1)
                env[key] = val

        print("[Installer] Successfully loaded MSVC x64 build tools environment!")
    except Exception as e:
        print(f"[Installer] Error setting up MSVC environment: {e}")

    return env