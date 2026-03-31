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
EXTRACT_DIR = "spiberry"

# ANSI color codes for terminal styling
class Colors:
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"
    GREEN   = "\033[32m"
    CYAN    = "\033[36m"
    YELLOW  = "\033[33m"
    MAGENTA = "\033[35m"
    WHITE   = "\033[97m"
    RED     = "\033[31m"


class MenuRenderer:
    """Reusable box-drawing renderer for interactive menus."""
    
    def __init__(self, width, title):
        self.width = max(width, 50)
        self.title = title
        self.c = Colors
    
    def row(self, text, visible_len):
        """Render a row with borders and proper padding."""
        padding = ' ' * (self.width - visible_len)
        return f"  {self.c.MAGENTA}║{self.c.RESET}{text}{padding}{self.c.MAGENTA}║{self.c.RESET}"
    
    def sep(self, left="╠", right="╣"):
        """Render a separator line."""
        return f"  {self.c.MAGENTA}{left}{'═' * self.width}{right}{self.c.RESET}"
    
    def header(self):
        """Render the menu header with title."""
        out = []
        out.append("")
        out.append(f"  {self.c.MAGENTA}╔{'═' * self.width}╗{self.c.RESET}")
        
        deco = f"✦  {self.title}  ✦"
        p = (self.width - len(deco)) // 2
        out.append(self.row(
            f"{' ' * p}{self.c.DIM}✦{self.c.RESET}  {self.c.BOLD}{self.c.WHITE}{self.title}{self.c.RESET}  {self.c.DIM}✦{self.c.RESET}",
            p + len(deco)
        ))
        out.append(self.sep())
        return out
    
    def footer(self):
        """Render the menu footer."""
        return [f"  {self.c.MAGENTA}╚{'═' * self.width}╝{self.c.RESET}", ""]
    
    @staticmethod
    def clear_lines(count):
        """Clear specified number of lines from terminal."""
        print(f"\033[{count}A\033[J", end="")
    
    @staticmethod
    def prompt():
        """Display the input prompt."""
        print(f"  {Colors.MAGENTA}▸{Colors.RESET} ", end="", flush=True)


def running_in_correct_venv(expected_venv_path):
    if sys.prefix == sys.base_prefix or Path(sys.prefix) != expected_venv_path:
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
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Failed to install packages. Trying to install from PyPI as fallback.")

    cmd = [
        str(python),
        "-m",
        "pip",
        "install",
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

def interactive_installation_menu():
    """Interactive multi-select menu for library installation."""
    libraries = [
        ("python3-picamera2",   "Programmatic camera access"),
        ("opencv-python",       "Computer vision"),
        ("ultralytics[export]", "YOLO / AI models"),
        ("python3-scipy",       "Scientific computing"),
        ("approxeng.input",     "Game controller support"),
    ]
    selected = [False] * len(libraries)
    name_width = max(len(name) for name, _ in libraries)
    max_desc = max(len(d) for _, d in libraries)
    
    # Create menu renderer
    width = 13 + name_width + max_desc + 3
    menu = MenuRenderer(width, "SpiBerry Setup")
    c = Colors

    def render():
        out = menu.header()
        out.append(menu.row("", 0))
        out.append(menu.row(f"  {c.BOLD}Select libraries to install:{c.RESET}", 30))
        out.append(menu.row("", 0))

        for i, (name, desc) in enumerate(libraries):
            n = str(i + 1)
            padded = name.ljust(name_width)
            if selected[i]:
                mark = f"{c.GREEN}●{c.RESET}"
                nm = f"{c.GREEN}{c.BOLD}{padded}{c.RESET}"
            else:
                mark = f"{c.DIM}○{c.RESET}"
                nm = f"{c.WHITE}{padded}{c.RESET}"

            vis = f"   [{n}] X  {padded}   {desc}"
            colored = f"   [{c.CYAN}{n}{c.RESET}] {mark}  {nm}   {c.DIM}{desc}{c.RESET}"
            out.append(menu.row(colored, len(vis)))

        out.append(menu.row("", 0))
        out.append(menu.sep())

        ctrl_vis = f"  1-{len(libraries)} Toggle │ a All │ c Confirm │ s Skip"
        ctrl = (
            f"  {c.CYAN}1-{len(libraries)}{c.RESET} Toggle "
            f"{c.DIM}│{c.RESET} {c.GREEN}a{c.RESET} All "
            f"{c.DIM}│{c.RESET} {c.GREEN}c{c.RESET} Confirm "
            f"{c.DIM}│{c.RESET} {c.YELLOW}s{c.RESET} Skip"
        )
        out.append(menu.row(ctrl, len(ctrl_vis)))
        out.extend(menu.footer())

        print("\n".join(out))
        return len(out)

    count = 0
    while True:
        if count > 0:
            MenuRenderer.clear_lines(count)
        count = render()
        MenuRenderer.prompt()

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
                print(f"\n\n  {c.GREEN}✓{c.RESET} {c.BOLD}Installing:{c.RESET} {names}\n")
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

def interactive_pin_menu():
    """Interactive menu for configuring RGB LED and button pins."""
    # Default pin configuration
    defaults = {
        "--red": 0,
        "--green": 11,
        "--blue": 9,
        "--button": 17,
    }
    
    pins = defaults.copy()
    fields = [
        ("--red", "RGB LED - Red"),
        ("--green", "RGB LED - Green"),
        ("--blue", "RGB LED - Blue"),
        ("--button", "Button"),
    ]
    
    selected_idx = 0
    editing = False
    edit_buffer = ""
    
    # Create menu renderer
    name_width = max(len(desc) for _, desc in fields)
    width = name_width + 30
    menu = MenuRenderer(width, "Pin Configuration")
    c = Colors

    def render():
        out = menu.header()
        out.append(menu.row("", 0))
        out.append(menu.row(f"  {c.BOLD}Configure GPIO pins:{c.RESET}", 22))
        out.append(menu.row("", 0))

        for i, (key, desc) in enumerate(fields):
            n = str(i + 1)
            padded = desc.ljust(name_width)
            
            if i == selected_idx:
                mark = f"{c.CYAN}▸{c.RESET}"
                if editing:
                    value_str = edit_buffer + "█"
                    color_value = f"{c.YELLOW}{c.BOLD}{value_str}{c.RESET}"
                else:
                    value_str = str(pins[key])
                    color_value = f"{c.GREEN}{c.BOLD}{value_str}{c.RESET}"
                nm = f"{c.CYAN}{c.BOLD}{padded}{c.RESET}"
            else:
                mark = " "
                value_str = str(pins[key])
                color_value = f"{c.WHITE}{value_str}{c.RESET}"
                nm = f"{c.WHITE}{padded}{c.RESET}"

            vis = f" X  [{n}] {padded}  GPIO {value_str}"
            colored = f" {mark}  [{c.CYAN}{n}{c.RESET}] {nm}  {c.DIM}GPIO{c.RESET} {color_value}"
            out.append(menu.row(colored, len(vis)))

        out.append(menu.row("", 0))
        out.append(menu.sep())

        if editing:
            ctrl_vis = f"  0-9 Enter Pin │ Enter Save │ Esc Cancel"
            ctrl = (
                f"  {c.CYAN}0-9{c.RESET} Enter Pin "
                f"{c.DIM}│{c.RESET} {c.GREEN}Enter{c.RESET} Save "
                f"{c.DIM}│{c.RESET} {c.YELLOW}Esc{c.RESET} Cancel"
            )
        else:
            ctrl_vis = f"  1-4 Select │ d Defaults │ c Confirm │ s Skip"
            ctrl = (
                f"  {c.CYAN}1-4{c.RESET} Select "
                f"{c.DIM}│{c.RESET} {c.GREEN}d{c.RESET} Defaults "
                f"{c.DIM}│{c.RESET} {c.GREEN}c{c.RESET} Confirm "
                f"{c.DIM}│{c.RESET} {c.YELLOW}s{c.RESET} Skip"
            )
        out.append(menu.row(ctrl, len(ctrl_vis)))
        out.extend(menu.footer())

        print("\n".join(out))
        return len(out)

    count = 0
    while True:
        if count > 0:
            MenuRenderer.clear_lines(count)
        count = render()
        MenuRenderer.prompt()

        try:
            choice = _getch()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if editing:
            if choice == "\r" or choice == "\n":  # Enter
                if edit_buffer.isdigit() and 0 <= int(edit_buffer) <= 27:
                    pins[fields[selected_idx][0]] = int(edit_buffer)
                    editing = False
                    edit_buffer = ""
                elif edit_buffer == "":
                    editing = False
            elif choice == "\x1b":  # Escape
                editing = False
                edit_buffer = ""
            elif choice.isdigit():
                edit_buffer += choice
            elif choice == "\x7f" or choice == "\x08":  # Backspace
                edit_buffer = edit_buffer[:-1]
        else:
            choice_lower = choice.lower()
            if choice_lower == "s":
                print()
                return None
            elif choice_lower == "c":
                print(f"\n\n  {c.GREEN}✓{c.RESET} {c.BOLD}Pin configuration confirmed{c.RESET}\n")
                return pins
            elif choice_lower == "d":
                pins = defaults.copy()
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(fields):
                    selected_idx = idx
                    editing = True
                    edit_buffer = str(pins[fields[idx][0]])

def fix_permissions(work_dir):
    """Restore ownership of all files under work_dir to the invoking (non-root) user."""
    try:
        uid = int(os.environ["SUDO_UID"])
        gid = int(os.environ["SUDO_GID"])
    except (KeyError, ValueError):
        return  # Not running under sudo, nothing to fix

    for dirpath, dirnames, filenames in os.walk(work_dir):
        try:
            os.chown(dirpath, uid, gid)
        except OSError:
            pass
        for name in filenames:
            try:
                os.chown(os.path.join(dirpath, name), uid, gid)
            except OSError:
                pass


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

    zip_path = Path(__file__).resolve().parent
    work_dir = Path(os.getcwd())
    
    Path(work_dir / "spiberryengine.log").touch(exist_ok=True)

    # if zip_path.parent.parent != Path(os.getcwd()):
    #     print("Warning: The application is being run from a different directory than where it's located.")
    #     install_location = input("Install to 1) current directory 2) zip file's directory: ")
    #     if install_location == "1":
    #         pass
    #     elif install_location == "2":
    #         work_dir = zip_path.parent

    extract_dir = work_dir / EXTRACT_DIR
    # Keep the venv inside the extracted app directory.
    venv_path = extract_dir / VENV_DIR

    if running_in_correct_venv(venv_path):
        from spiberry.app.main import Controller
        Controller().main()
        return

    extract_if_needed(zip_path, extract_dir)

    if not venv_path.exists():
        print("Not running in (correct) virtual environment. Setting up...")
        create_venv(venv_path)
        first_setup = True
    else:
        first_setup = False

    # first_setup = not venv_path.exists()

    if first_setup:
        # create_venv(venv_path)
        python = venv_python(venv_path)
        pip_install(python, extract_dir)
    else:
        python = venv_python(venv_path)

    if first_setup:
        extra_libs = interactive_installation_menu()
        if extra_libs:
            install_extra(python, extra_libs)

    if len(sys.argv) > 1 and sys.argv[1] == "--set-pins":
        selected_pins = interactive_pin_menu()
        pin_args = [arg for arg in sys.argv[1:] if arg != "--set-pins"]
        if selected_pins:
            for key, value in selected_pins.items():
                pin_args.extend([key, str(value)])
    
    fix_permissions(work_dir)
    # Make scripts executable
    scripts_dir = extract_dir / "scripts"
    if os.name != "nt" and scripts_dir.exists():
        for script in scripts_dir.glob("*.sh"):
            script.chmod(0o755)


    if os.name != "nt" and not os.path.exists("/etc/systemd/system/sbe.service"):
        template = extract_dir / "sbe.service"
        service = template.read_text()
        service = service.replace("<execstart>", str(python) + " -m spiberry.app.main" + " " + " ".join(pin_args if 'pin_args' in locals() else sys.argv[1:]))
        service = service.replace("<workingdirectory>", str(extract_dir))
        destination = Path("/etc/systemd/system/sbe.service")
        destination.write_text(service)
        subprocess.check_call(["systemctl", "daemon-reload"])
        subprocess.check_call(["systemctl", "enable", "sbe.service"])
        subprocess.check_call(["systemctl", "start", "sbe.service"])
    else:
        reexec_in_venv(python, extract_dir, pin_args if 'pin_args' in locals() else sys.argv[1:])


if __name__ == "__main__":
    main()
