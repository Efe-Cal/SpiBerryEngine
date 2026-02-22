import os
import sys
import subprocess
import venv
import shutil
import zipfile
from pathlib import Path
from argparse import ArgumentParser

APP_NAME = "spiberry"
VENV_DIR = ".venv"
EXTRACT_DIR = ".bootstrap"

argument_parser = ArgumentParser(description="SpiBerry Engine")
argument_parser.add_argument(
    "--vision",
    type=int,
    choices=[0, 1, 2],
    help="Install vision dependencies level: 0=picamera2, 1=picamera2+opencv, 2=picamera2+opencv+ultralytics",
)


def running_in_venv():
    return sys.prefix != sys.base_prefix


def extract_if_needed(zip_path, target):
    if target.exists():
        return

    # Validate zip file before extraction
    try:
        with zipfile.ZipFile(zip_path) as z:
            # Test zip file integrity
            bad_file = z.testzip()
            if bad_file is not None:
                raise zipfile.BadZipFile(f"Corrupted file in archive: {bad_file}")
            
            # Extract files
            z.extractall(target)
    except (zipfile.BadZipFile, OSError) as e:
        # Clean up target directory if extraction fails
        if target.exists():
            try:
                shutil.rmtree(target)
            except OSError:
                # Ignore cleanup errors to preserve original exception
                pass
        raise RuntimeError(f"Failed to extract {zip_path}: {e}") from e


def create_venv(venv_path):
    builder = venv.EnvBuilder(with_pip=True, system_site_packages=True)
    builder.create(venv_path)


def venv_python(venv_path):
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def pip_install(python, extract_dir):
    wheels = extract_dir / "wheels"
    reqs = extract_dir / "requirements.txt"

    cmd = [
        str(python),
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(wheels),
        "-r",
        str(reqs),
    ]

    subprocess.check_call(cmd)

def install_vision(python, libs=None):
    if libs is None:
        libs = ["python3-picamera2", "ultralytics[export]", "opencv-python"]
    libs = list(libs)

    if "python3-picamera2" in libs:
        apt_cmd = [
            "sudo",
            "apt",
            "install",
            "-y",
            "python3-picamera2",
            "--no-install-recommends",
        ]
        subprocess.check_call(apt_cmd)
        libs.remove("python3-picamera2")

    if libs:
        pip_cmd = [
            str(python),
            "-m",
            "pip",
            "install",
            *libs,
        ]

        subprocess.check_call(pip_cmd)

def reexec_in_venv(python, extract_dir, app_args):
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        env["PYTHONPATH"] = str(extract_dir) + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = str(extract_dir)

    cmd = [
        str(python),
        "-m",
        "app.main",
        *app_args,
    ]

    try:
        result = subprocess.run(cmd, env=env)
        # Handle None returncode (e.g., terminated by signal on Unix)
        sys.exit(result.returncode if result.returncode is not None else 1)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Failed to execute command: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    bootstrap_args, app_args = argument_parser.parse_known_args(sys.argv[1:])

    # is running root?
    if os.name != "nt":
        geteuid = getattr(os, "geteuid", None)
        if geteuid is not None and geteuid() != 0:
            print("This application must be run as root. Please use sudo.")
            sys.exit(1)

    zip_path = Path(__file__).resolve()
    work_dir = zip_path.parent
    extract_dir = work_dir / EXTRACT_DIR
    venv_path = work_dir / VENV_DIR

    if running_in_venv():
        from app.main import main as app_main
        app_main()
        return

    extract_if_needed(zip_path, extract_dir)

    if not venv_path.exists():
        create_venv(venv_path)
        python = venv_python(venv_path)
        pip_install(python, extract_dir)
    else:
        python = venv_python(venv_path)

    if bootstrap_args.vision is not None:
        vision_libs = ["python3-picamera2"]
        if bootstrap_args.vision >= 1:
            vision_libs.append("opencv-python")
        if bootstrap_args.vision >= 2:
            vision_libs.append("ultralytics[export]")
        install_vision(python, vision_libs)

    if os.name != "nt" and not os.path.exists("/etc/systemd/system/sbe.service"):
        template = extract_dir / "sbe.service"
        service = template.read_text()
        service = service.replace("<execstart>", str(python) + " -m app.main" + " " + " ".join(app_args))
        service = service.replace("<workingdirectory>", str(extract_dir))
        destination = Path("/etc/systemd/system/sbe.service")
        destination.write_text(service)
        subprocess.check_call(["systemctl", "daemon-reload"])
        subprocess.check_call(["systemctl", "enable", "sbe.service"])
        subprocess.check_call(["systemctl", "start", "sbe.service"])
    else:
        reexec_in_venv(python, extract_dir, app_args)


if __name__ == "__main__":
    main()
