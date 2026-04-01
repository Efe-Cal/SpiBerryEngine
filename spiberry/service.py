import os
import subprocess
import sys
from pathlib import Path


def _require_root_on_linux():
    if os.name == "nt":
        raise SystemExit("Systemd service installation is only supported on Linux.")

    geteuid = getattr(os, "geteuid", None)
    if geteuid is not None and geteuid() != 0:
        raise SystemExit("Please run service installation with sudo/root privileges.")


def install_service(
    service_name="sbe.service",
    app_args=None,
    start=False,
    python_executable=None,
    template_path=None,
    working_directory=None,
):
    _require_root_on_linux()

    if app_args is None:
        app_args = []

    package_root = Path(__file__).resolve().parent
    resolved_template = Path(template_path) if template_path is not None else package_root / "sbe.service"
    if not resolved_template.exists():
        raise SystemExit(f"Service template not found: {resolved_template}")

    python = Path(python_executable).resolve() if python_executable is not None else Path(sys.executable).resolve()
    exec_start = f"{python} -m spiberry.app.main"
    if app_args:
        exec_start += " " + " ".join(app_args)

    service_content = resolved_template.read_text(encoding="utf-8")
    service_content = service_content.replace("<execstart>", exec_start)
    service_working_directory = Path(working_directory) if working_directory is not None else package_root
    service_content = service_content.replace("<workingdirectory>", str(service_working_directory))

    destination = Path("/etc/systemd/system") / service_name
    destination.write_text(service_content, encoding="utf-8")

    subprocess.check_call(["systemctl", "daemon-reload"])
    subprocess.check_call(["systemctl", "enable", service_name])
    if start:
        subprocess.check_call(["systemctl", "start", service_name])

    print(f"Installed {service_name} with ExecStart: {exec_start}")
