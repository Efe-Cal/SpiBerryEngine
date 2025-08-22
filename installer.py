
# --- Tkinter GUI for argument input ---
import os
import subprocess
import tarfile
import tkinter as tk
from tkinter import messagebox
import paramiko


def get_args_gui():
    root = tk.Tk()
    root.title("SpiBerry Installer")
    root.geometry("300x220")
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

    result = {}
    def submit():
        nonlocal result
        result = {k: v.get() for k, v in entries.items()}
        root.quit()
        root.destroy()

    btn = tk.Button(root, text="Start Installation", command=submit)
    btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

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
try:
    stdin, stdout, stderr = ssh.exec_command(ssh_commands)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        raise Exception(stderr.read().decode())
except Exception as e:
    messagebox.showerror("Error", f"SSH command failed: {e}")
    ssh.close()
    raise SystemExit(1)

ssh.close()