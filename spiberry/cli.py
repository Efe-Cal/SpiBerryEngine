import argparse


def run_engine():
    from spiberry.app.main import Controller

    Controller().main()


def run_remote_drive():
    from spiberry.remote_drive.main import RemoteDriveController

    RemoteDriveController().start_with_controller()


def run_remote_drive_socket():
    from spiberry.remote_drive.main import RemoteDriveController

    RemoteDriveController().start_with_socket()


def install_service_cli():
    from spiberry.service import install_service

    parser = argparse.ArgumentParser(description="Install SpiBerryEngine as a systemd service.")
    parser.add_argument("--service-name", default="sbe.service", help="Systemd service file name")
    parser.add_argument("--start", action="store_true", help="Start the service immediately")
    parser.add_argument(
        "--app-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Arguments passed to spiberry.app.main (use after --app-args)",
    )

    args = parser.parse_args()
    install_service(service_name=args.service_name, app_args=args.app_args, start=args.start)


def _run_systemctl(command, service_name="sbe.service"):
    import subprocess
    import sys

    try:
        subprocess.run(["sudo", "systemctl", command, service_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command} on {service_name}: {e}", file=sys.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("systemctl or sudo not found. This command is intended for Linux.", file=sys.stderr)
        sys.exit(1)


def start_service():
    _run_systemctl("start")


def stop_service():
    _run_systemctl("stop")


def restart_service():
    _run_systemctl("restart")


def enable_service():
    _run_systemctl("enable")


def disable_service():
    _run_systemctl("disable")


def status_service():
    import subprocess
    # status doesn't need sudo usually, and we don't want it to exit with error if it's just stopped
    subprocess.run(["systemctl", "status", "sbe.service"])


def extract_package_content():
    import shutil
    from pathlib import Path
    
    home_dir = Path.home()
    target_dir = home_dir / "spiberry"
    package_dir = Path(__file__).resolve().parent
    
    print(f"Extracting package content from {package_dir} to {target_dir}...")
    
    if target_dir.exists():
        response = input(f"Target directory {target_dir} already exists. Do you want to overwrite it? (y/n)").lower()
        if response != "y":
            print("Extraction cancelled.")
            return
        shutil.rmtree(target_dir)
    
    try:
        # We want to copy everything in the package directory (spiberry/)
        shutil.copytree(package_dir, target_dir)
        print(f"Successfully extracted package content to {target_dir}")
    except Exception as e:
        print(f"Error during extraction: {e}")
