# Deprecated

import os
import subprocess
import tarfile
import tkinter as tk
from tkinter import messagebox
import paramiko


def get_args_gui():
    root = tk.Tk()
    root.title("SpiBerry Installer")
    root.geometry("300x360")  # Adjusted for hardware config area
    root.resizable(False, False)

    entries = {}
    labels = {
        "remote_host": "Remote Host",
        "remote_user": "Remote User",
        "remote_password": "Password",
        "remote_dir": "Remote Directory",
    }
    defaults = {
        "remote_user": "pi",
        "remote_host": "raspberrypi",
        "remote_password": "",
        "remote_dir": "",
    }

    for idx, key in enumerate(labels):
        tk.Label(root, text=labels[key]).grid(row=idx, column=0, padx=10, pady=8, sticky="w")
        if key == "remote_password":
            entry = tk.Entry(root, width=25, show="*")
        else:
            entry = tk.Entry(root, width=25)
        entry.insert(0, defaults[key])
        entry.grid(row=idx, column=1, padx=10, pady=8)
        entries[key] = entry

    # --- Hardware Config Area ---
    hardware_label = tk.Label(root, text="Hardware Config", font=("Arial", 10, "bold"))
    hardware_label.grid(row=len(labels), column=0, columnspan=2, pady=(10, 0))

    hw_fields = [
        ("r_pin", "R pin", "0"),
        ("b_pin", "B pin", "11"),
        ("g_pin", "G pin", "9"),
        ("button_pin", "Button pin", "17"),
    ]

    def validate_pin(P):
        return P.isdigit() and len(P) <= 2 or P == ""

    vcmd = (root.register(validate_pin), '%P')

    for i, (key, label, default) in enumerate(hw_fields):
        tk.Label(root, text=label).grid(row=len(labels)+1+i, column=0, padx=10, pady=5, sticky="w")
        entry = tk.Entry(root, width=5, validate="key", validatecommand=vcmd)
        entry.insert(0, default)
        entry.grid(row=len(labels)+1+i, column=1, padx=10, pady=5, sticky="w")
        entries[key] = entry

    result = {}
    def submit():
        nonlocal result
        result = {k: v.get() for k, v in entries.items()}
        root.quit()
        root.destroy()

    btn = tk.Button(root, text="Start Installation", command=submit)
    btn.grid(row=len(labels)+1+len(hw_fields), column=0, columnspan=2, pady=10)

    root.mainloop()
    return result

args = get_args_gui()
if not args:
    raise SystemExit(0)
remote_user = args["remote_user"]
remote_host = args["remote_host"]
remote_password = args["remote_password"]
remote_dir = f"/home/{remote_user}/"+args["remote_dir"]
requirements_file = "requirements.txt"

# --- Main logic ---
if not os.path.exists("dependencies.tar.gz"):
    # This code exists to install the dependencies but using the dependencies archive in the repo is strongly encouraged 
    os.makedirs("dependencies", exist_ok=True)
    try:
        subprocess.run([
            "pip", "download", "-r", requirements_file, "-d", "./dependencies","--platform", "manylinux2014_aarch64", "--only-binary", ":all:"
        ], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", "pip download failed.")
        if os.path.isdir("dependencies"):
            if os.name == 'nt':
                subprocess.run(["rmdir", "/S", "/Q", "dependencies"], shell=True)
            else:
                subprocess.run(["rm", "-rf", "dependencies"])
        raise SystemExit(1)

    with tarfile.open("dependencies.tar.gz", "w:gz") as tar:
        tar.add("dependencies", arcname="dependencies")

    if os.name == 'nt':
        subprocess.run(["rmdir", "/S", "/Q", "dependencies"], shell=True, check=True)
    else:
        subprocess.run(["rm", "-rf", "dependencies"], check=True)


# --- Paramiko SSH Setup ---
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(remote_host, username=remote_user, password=remote_password)
except Exception as e:
    messagebox.showerror("Error", f"SSH connection failed: {e}")
    raise SystemExit(1)

# mkdir -p REMOTE_DIR with SSH
try:
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        raise Exception(stderr.read().decode())
except Exception as e:
    messagebox.showerror("Error", f"SSH mkdir failed: {e}")
    ssh.close()
    raise SystemExit(1)


# Step 4: Send archive to remote machine using SFTP
try:
    sftp = ssh.open_sftp()
    sftp.put("dependencies.tar.gz", f"{remote_dir}/dependencies.tar.gz")
    sftp.put("SpiBerryEngine.py", f"{remote_dir}/SpiBerryEngine.py")
    sftp.close()
except Exception as e:
    messagebox.showerror("Error", f"SFTP failed: {e}")
    ssh.close()
    raise SystemExit(1)

# Step 5: Run extraction and install commands via SSH
ssh_commands = (
    f"mkdir -p {remote_dir} && "
    f"cd {remote_dir} && "
    "python3 -m venv venv && "
    "source venv/bin/activate && "
    "tar zxvf dependencies.tar.gz && "
    "cd dependencies && "
    "pip install * -f ./ --no-index"
)

run_sh=f"""#!/bin/bash
cd {remote_dir}
source venv/bin/activate
python3 SpiBerryEngine.py --red {args['r_pin']} --green {args['g_pin']} --blue {args['b_pin']} --button {args['button_pin'] }
"""

# Message box: Installation in progress...
messagebox.showinfo("Info", "Installation in progress. This may take a few minutes...")

try:
    stdin, stdout, stderr = ssh.exec_command(ssh_commands)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        raise Exception(stderr.read().decode())
    # Send run_sh as a file and make it runnable
    try:
        sftp = ssh.open_sftp()
        run_sh_path = f"/home/{remote_user}/run.sh"
        with sftp.file(run_sh_path, "w") as f:
            f.write(run_sh)
        sftp.chmod(run_sh_path, 0o755)
        sftp.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send run.sh: {e}")
        ssh.close()
        raise SystemExit(1)
except Exception as e:
    messagebox.showerror("Error", f"SSH command failed: {e}")
    ssh.close()
    raise SystemExit(1)

ssh.close()