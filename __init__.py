# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright 2026 Max Planck Institute for Intelligent Systems
import os
import sys
import site
import subprocess
import threading
from pathlib import Path

if "bpy" in locals():
    # Re-entry via `System → Reload Scripts`: force submodules to re-import so
    # edits inside subpackages take effect without restarting Blender.
    import importlib
    from . import utils, preferences, properties, operators, panels, handlers, install_utils
    importlib.reload(utils)
    importlib.reload(preferences)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(handlers)
    importlib.reload(install_utils)
else:
    from . import utils, preferences, properties, operators, panels, handlers, install_utils

import bpy

# Map: import_name -> [pip_spec, optional_extra_index]
PACKAGES = {
    "torch": ["torch", "https://download.pytorch.org/whl/cu132"],
    "torchvision": ["torchvision", "https://download.pytorch.org/whl/cu132"],
    "torchgeometry": ["torchgeometry"],
    "torchaudio": ["torchaudio"],
    "huggingface_hub": ["huggingface_hub"],
    "gdown": ["gdown"],
    "cv2": ["opencv-python"],
    "OpenGL": ["PyOpenGL"],
    "OpenGL_accelerate": ["PyOpenGL_accelerate"],
    "pycocotools": ["pycocotools"],
    "pafy": ["pafy"],
    "youtube_dl": ["youtube-dl"],
    "scipy": ["scipy"],
    "PIL": ["pillow>=7.1.0"],
    "easydict": ["easydict"],
    "Cython": ["cython"],
    "cffi": ["cffi"],
    "msgpack": ["msgpack"],
    "yaml": ["pyyaml"],
    "tensorboardX": ["tensorboardX"],
    "tqdm": ["tqdm"],
    "jinja2": ["jinja2"],
    "smplx": ["smplx"],
    "sklearn": ["scikit-learn"],
    "requests": ["requests"],
    "git": ["gitpython"],
}

def get_modules_path():
    """Returns the path of Blender's user modules directory."""
    return bpy.utils.user_resource("SCRIPTS", path="modules", create=True)

def append_modules_to_sys_path(modules_path):
    """Ensure Blender prioritizes user installed modules."""
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)
    site.addsitedir(modules_path)

def install_package(package_spec, modules_path, extra_index=None):
    """Install a single package using Blender's embedded Python executable."""
    python_exe = sys.executable

    try:
        print(f"[Installer] Installing {package_spec}...")
        args = [
            python_exe,
            "-m",
            "pip",
            "install",
            "--no-build-isolation",
            "--target",
            modules_path,
            package_spec,
        ]

        if extra_index:
            # Use --extra-index-url so PyPI can still satisfy standard dependencies
            args.extend(["--extra-index-url", extra_index])

        subprocess.check_call(args)
        print(f"[Installer] Successfully installed {package_spec}.")
    
    except subprocess.CalledProcessError as e:
        print(f"[Installer] Error occurred while installing {package_spec}: {e}")

def run_installation():
    modules_path = get_modules_path()
    append_modules_to_sys_path(modules_path)

    # 1. Install missing package dependencies
    for (import_name, pkg_args) in PACKAGES.items():
        try:
            __import__(import_name)
            print(f"[Installer] '{import_name}' is already installed.")
        except ImportError:
            print(f"[Installer] installing '{import_name}'.")
            package_spec = pkg_args[0]
            extra_index = pkg_args[1] if len(pkg_args) > 1 else None
            install_package(package_spec, modules_path, extra_index=extra_index)

    install_utils.ensure_ninja_installed(modules_path)

    env = os.environ.copy()
    env = install_utils.setup_msvc_env(env)
    
    # Ensure C++/CUDA compilers find torch and ninja from target modules
    env["PYTHONPATH"] = f"{modules_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["PATH"] = f"{modules_path}{os.pathsep}{env.get('PATH', '')}"
    env["DISTUTILS_USE_SDK"] = "1"

    # 2. Build detectron2
    try: 
        __import__("detectron2")
    except ImportError:
        install_utils.build_detectron2(modules_path, env)

    cwd = Path(__file__).parent.resolve()
    frankmocap_path = os.path.join(cwd, "frankmocap")

    # 3. Frankmocap setup scripts
    install_utils.install_pose_2d(frankmocap_path)

    install_utils.download_data_body_module(frankmocap_path)

    install_utils.install_hand_detectors(frankmocap_path, modules_path, env)

    install_utils.download_data_hand_module(frankmocap_path)

    install_utils.install_models(frankmocap_path)

    print("[Installer] finished installation")

def register():
    print("[Installer] Begining installation")
    threading.Thread(target=run_installation, daemon=True).start()
    preferences.register()
    properties.register()
    operators.register()
    panels.register()
    handlers.register()


def unregister():
    handlers.unregister()
    panels.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()
