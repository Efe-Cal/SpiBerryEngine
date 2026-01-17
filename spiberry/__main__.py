import os
import sys
import subprocess
import venv
import shutil
import zipfile
from pathlib import Path

APP_NAME = "spiberry"
VENV_DIR = ".venv"
EXTRACT_DIR = ".bootstrap"


def running_in_venv():
    return sys.prefix != sys.base_prefix


def extract_if_needed(zip_path, target):
    if target.exists():
        return

    with zipfile.ZipFile(zip_path) as z:
        z.extractall(target)


def create_venv(venv_path):
    builder = venv.EnvBuilder(with_pip=True)
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


def reexec_in_venv(python, extract_dir):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(extract_dir)

    cmd = [
        str(python),
        "-m",
        "app.main",
        *sys.argv[1:],
    ]

    os.execve(cmd[0], cmd, env)


def main():
    # is running root?
    if os.name != "nt" and os.geteuid() != 0:
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

    if os.name != "nt" and not os.path.exists("/etc/systemd/system/sbe.service"):
        template = extract_dir / "sbe.service"
        service = template.read_text()
        service = service.replace("<execstart>", str(python) + " " + str(extract_dir / "app" / "main.py"))
        service = service.replace("<workingdirectory>", str(extract_dir))
        template.write_text(service)

        shutil.copyfile(template, "/etc/systemd/system/sbe.service")
        subprocess.check_call(["systemctl", "daemon-reload"])
        subprocess.check_call(["systemctl", "enable", "sbe.service"])
        subprocess.check_call(["systemctl", "start", "--now", "sbe.service"])
    else:
        reexec_in_venv(python, extract_dir)


if __name__ == "__main__":
    main()
