import os
import sys
import subprocess
import venv
import shutil
import zipfile
from pathlib import Path
import importlib.metadata as metadata

def _getch():
    """Read a single keypress without waiting for Enter (cross-platform)."""
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in ("\x03", "\x04"):
        raise KeyboardInterrupt
    return ch


VENV_DIR = "venv"
EXTRACT_DIR = "spiberry_app"


def running_in_correct_venv():
    if sys.prefix == sys.base_prefix or Path(sys.prefix) != Path(__file__).resolve().parent.parent / VENV_DIR:
        return False

    libs = set([d.metadata["Name"].lower() for d in metadata.distributions()])
    for lib in ("gpiozero","mpremote","pyserial","watchdog","rpi-gpio"):
        if lib not in libs:
            return False
    
    return True

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

def install_extra(python, libs=None):
    if libs is None:
        libs = ["python3-picamera2", "ultralytics[export]", "opencv-python", "python3-scipy"]
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
    
    if "python3-scipy" in libs:
        apt_cmd = [
            "sudo",
            "apt",
            "install",
            "-y",
            "python3-scipy",
            "--no-install-recommends",
        ]
        subprocess.check_call(apt_cmd)
        libs.remove("python3-scipy")

    if libs:
        pip_cmd = [
            str(python),
            "-m",
            "pip",
            "install",
            *libs,
        ]

        subprocess.check_call(pip_cmd)

def interactive_setup_menu():
    """Interactive multi-select menu for library installation."""
    libraries = [
        ("python3-picamera2",   "Programmatic camera access"),
        ("opencv-python",       "Computer vision"),
        ("ultralytics[export]", "YOLO / AI models"),
        ("python3-scipy",       "Scientific computing"),
    ]
    selected = [False] * len(libraries)
    name_width = max(len(name) for name, _ in libraries)

    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"
    GREEN   = "\033[32m"
    CYAN    = "\033[36m"
    YELLOW  = "\033[33m"
    MAGENTA = "\033[35m"
    WHITE   = "\033[97m"

    max_desc = max(len(d) for _, d in libraries)
    W = 13 + name_width + max_desc + 3
    W = max(W, 50)

    def row(text, visible_len):
        return f"  {MAGENTA}║{RESET}{text}{' ' * (W - visible_len)}{MAGENTA}║{RESET}"

    def sep(left="╠", right="╣"):
        return f"  {MAGENTA}{left}{'═' * W}{right}{RESET}"

    def render():
        out = []
        out.append("")
        out.append(f"  {MAGENTA}╔{'═' * W}╗{RESET}")

        title = "SpiBerry Setup"
        deco = f"✦  {title}  ✦"
        p = (W - len(deco)) // 2
        out.append(row(
            f"{' ' * p}{DIM}✦{RESET}  {BOLD}{WHITE}{title}{RESET}  {DIM}✦{RESET}",
            p + len(deco)
        ))

        out.append(sep())
        out.append(row("", 0))
        out.append(row(f"  {BOLD}Select libraries to install:{RESET}", 30))
        out.append(row("", 0))

        for i, (name, desc) in enumerate(libraries):
            n = str(i + 1)
            padded = name.ljust(name_width)
            if selected[i]:
                mark = f"{GREEN}●{RESET}"
                nm = f"{GREEN}{BOLD}{padded}{RESET}"
            else:
                mark = f"{DIM}○{RESET}"
                nm = f"{WHITE}{padded}{RESET}"

            vis = f"   [{n}] X  {padded}   {desc}"
            colored = f"   [{CYAN}{n}{RESET}] {mark}  {nm}   {DIM}{desc}{RESET}"
            out.append(row(colored, len(vis)))

        out.append(row("", 0))
        out.append(sep())

        ctrl_vis = f"  1-{len(libraries)} Toggle │ a All │ c Confirm │ s Skip"
        ctrl = (
            f"  {CYAN}1-{len(libraries)}{RESET} Toggle "
            f"{DIM}│{RESET} {GREEN}a{RESET} All "
            f"{DIM}│{RESET} {GREEN}c{RESET} Confirm "
            f"{DIM}│{RESET} {YELLOW}s{RESET} Skip"
        )
        out.append(row(ctrl, len(ctrl_vis)))

        out.append(f"  {MAGENTA}╚{'═' * W}╝{RESET}")
        out.append("")

        print("\n".join(out))
        return len(out)

    count = 0
    while True:
        if count > 0:
            print(f"\033[{count}A\033[J", end="")
        count = render()
        print(f"  {MAGENTA}▸{RESET} ", end="", flush=True)

        try:
            choice = _getch().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if choice == "s":
            print()
            return None
        elif choice == "c":
            result = [libraries[i][0] for i in range(len(libraries)) if selected[i]]
            if result:
                names = ", ".join(result)
                print(f"\n\n  {GREEN}✓{RESET} {BOLD}Installing:{RESET} {names}\n")
            else:
                print()
            return result or None
        elif choice == "a":
            toggle = not all(selected)
            selected = [toggle] * len(libraries)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(libraries):
                selected[idx] = not selected[idx]


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
    # is running root?
    if os.name != "nt":
        geteuid = getattr(os, "geteuid", None)
        if geteuid is not None and geteuid() != 0:
            print("This application must be run as root. Please use sudo.")
            sys.exit(1)

    zip_path = Path(os.getcwd()) / Path(__file__).resolve().parent.name
    work_dir = zip_path.parent
    extract_dir = work_dir / EXTRACT_DIR
    venv_path = work_dir / VENV_DIR
    
    print(f"Zip path: {zip_path}")
    print(f"Working directory: {work_dir}")
    print(f"Extract directory: {extract_dir}")
    print(f"Virtualenv path: {venv_path}")

    if running_in_correct_venv():
        from app.main import main as app_main
        app_main()
        return
    else:
        create_venv(venv_path)
        first_setup = True

    extract_if_needed(zip_path, extract_dir)

    # first_setup = not venv_path.exists()

    if first_setup:
        # create_venv(venv_path)
        python = venv_python(venv_path)
        pip_install(python, extract_dir)
    else:
        python = venv_python(venv_path)

    if first_setup:
        extra_libs = interactive_setup_menu()
        if extra_libs:
            install_extra(python, extra_libs)

    if os.name != "nt" and not os.path.exists("/etc/systemd/system/sbe.service"):
        template = extract_dir / "sbe.service"
        service = template.read_text()
        service = service.replace("<execstart>", str(python) + " -m app.main" + " " + " ".join(sys.argv[1:]))
        service = service.replace("<workingdirectory>", str(extract_dir))
        destination = Path("/etc/systemd/system/sbe.service")
        destination.write_text(service)
        subprocess.check_call(["systemctl", "daemon-reload"])
        subprocess.check_call(["systemctl", "enable", "sbe.service"])
        subprocess.check_call(["systemctl", "start", "sbe.service"])
    else:
        reexec_in_venv(python, extract_dir, sys.argv[1:])


if __name__ == "__main__":
    main()
