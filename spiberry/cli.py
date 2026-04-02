import os

def init_env():
    import subprocess
    from pathlib import Path
    from spiberry.app.config import create_default_config, CONFIG_PATH

    create_default_config()
    
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not editor:
        editor = "nano"
    
    print(f"Opening config file {CONFIG_PATH} for review in {editor}...")
    try:
        subprocess.run([editor, str(CONFIG_PATH)], check=True)
    except Exception as e:
        print(f"Error opening editor: {e}")
        return

    # After exiting the editor, create the directories and files specified in the config
    import configparser
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    
    try:
        code_path = Path(config.get("Code", "path")).expanduser()
        functions_path = Path(config.get("Code", "raspi_functions_path")).expanduser()
        
        code_path.parent.mkdir(parents=True, exist_ok=True)
        functions_path.mkdir(parents=True, exist_ok=True)
        
        if not code_path.exists():
            print(f"Creating default robot code at {code_path}")
            with open(code_path, "w") as f:
                f.write("# Default SpiBerryEngine robot code\n\ndef main():\n    print('Hello SpiBerry!')\n\nif __name__ == '__main__':\n    main()\n")
                
        print("Environment initialization complete.")
    except Exception as e:
        print(f"Error creating files/directories: {e}")

def run_engine(robot_code_path=None):
    from spiberry.app.main import Controller

    Controller(robot_code_path=robot_code_path).main()


def run_remote_drive():
    from spiberry.remote_drive.main import RemoteDriveController

    RemoteDriveController().start_with_controller()


def run_remote_drive_socket():
    from spiberry.remote_drive.main import RemoteDriveController

    RemoteDriveController().start_with_socket()


def install_service_cli(args):
    from spiberry.service import install_service
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

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SpiBerryEngine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run-engine", help="Run the SpiBerryEngine application")
    run_parser.add_argument("robot_code", nargs="?", help="Path to the robot code file (optional)", default=None)
    subparsers.add_parser("run-remote-drive", help="Run the remote drive controller with a connected game controller")
    subparsers.add_parser("run-remote-drive-socket", help="Run the remote drive controller with socket interface")
    
    install_parser = subparsers.add_parser("install-service", help="Install SpiBerryEngine as a systemd service")
    install_parser.add_argument("--service-name", default="sbe.service", help="Systemd service file name")
    install_parser.add_argument("--start", action="store_true", help="Start the service immediately")
    install_parser.add_argument(
        "--app-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Arguments passed to spiberry.app.main (use after --app-args)",
    )

    subparsers.add_parser("start-service", help="Start the SpiBerryEngine systemd service")
    subparsers.add_parser("stop-service", help="Stop the SpiBerryEngine systemd service")
    subparsers.add_parser("restart-service", help="Restart the SpiBerryEngine systemd service")
    subparsers.add_parser("enable-service", help="Enable the SpiBerryEngine systemd service")
    subparsers.add_parser("disable-service", help="Disable the SpiBerryEngine systemd service")
    subparsers.add_parser("status-service", help="Check the status of the SpiBerryEngine systemd service")
    subparsers.add_parser("extract-package", help="Extract the contents of the spiberry package to the user's home directory")
    subparsers.add_parser("init", help="Initialize the SpiBerryEngine environment by creating default config and files")
    args = parser.parse_args()

    if args.command == "run-engine":
        if args.robot_code:
            run_engine(robot_code_path=args.robot_code)
        else:
            run_engine()
    elif args.command == "run-remote-drive":
        run_remote_drive()
    elif args.command == "run-remote-drive-socket":
        run_remote_drive_socket()
    elif args.command == "install-service":
        install_service_cli(args)
    elif args.command == "start-service":
        start_service()
    elif args.command == "stop-service":
        stop_service()
    elif args.command == "restart-service":
        restart_service()
    elif args.command == "enable-service":
        enable_service()
    elif args.command == "disable-service":
        disable_service()
    elif args.command == "status-service":
        status_service()
    elif args.command == "extract-package":
        extract_package_content()
    elif args.command == "init":
        init_env()

if __name__ == "__main__":
    main()