# Deprecated: See the VS Code Extension for easier code deployment. This script is still supported but the extension provides a more user-friendly interface.
import sys
import zipfile
import tempfile
import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import paramiko
import keyboard

def send_robot_code(zip_path, remote_dir, remote_host, remote_user, remote_pass, raspi_path=None):
    # Extract zip to temp dir
	with tempfile.TemporaryDirectory() as temp_dir:
		with zipfile.ZipFile(zip_path, 'r') as zip_ref:
			zip_ref.extractall(temp_dir)

		# Read projectbody.json
		json_path = os.path.join(temp_dir, "projectbody.json")
		if not os.path.exists(json_path):
			messagebox.showerror("Error", "projectbody.json not found in zip.")
			sys.exit(1)
		with open(json_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		main_code = data.get("main")
		if main_code is None:
			messagebox.showerror("Error", '"main" key not found in projectbody.json.')
			sys.exit(1)

		# Write to robot_code.py
		robot_code_path = os.path.join(temp_dir, "robot_code.py")
		with open(robot_code_path, "w", encoding="utf-8") as f:
			f.write(main_code)

		# Copy raspi_functions.py if provided
		raspi_functions_path = None
		if raspi_path:
			if not os.path.exists(raspi_path):
				messagebox.showerror("Error", f"Raspi Functions file not found: {raspi_path}")
				sys.exit(1)
			raspi_functions_path = os.path.join(temp_dir, "raspi_functions.py")
			with open(raspi_path, "r", encoding="utf-8") as src, open(raspi_functions_path, "w", encoding="utf-8") as dst:
				dst.write(src.read())

		# Send to remote machine using paramiko
		remote_path = f"/home/{remote_user}/{remote_dir}/robot_code.py"
		remote_raspi_path = f"/home/{remote_user}/{remote_dir}/raspi_functions.py"
		try:
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(remote_host, username=remote_user, password=remote_pass)
			sftp = ssh.open_sftp()
			# Ensure remote dir exists
			try:
				sftp.stat(f"/home/{remote_user}/{remote_dir}")
			except FileNotFoundError:
				sftp.mkdir(f"/home/{remote_user}/{remote_dir}")
			sftp.put(robot_code_path, remote_path)
			if raspi_functions_path:
				sftp.put(raspi_functions_path, remote_raspi_path)
			sftp.close()
			ssh.close()
			msg = f"robot_code.py sent to {remote_host}:{remote_path}"
			if raspi_functions_path:
				msg += f"\nraspi_functions.py sent to {remote_host}:{remote_raspi_path}"
			messagebox.showinfo("Success", msg)
		except Exception as e:
			messagebox.showerror("SCP Error", f"Failed to send file via paramiko: {e}")


def main():
	keyboard.add_hotkey('ctrl+shift+d', lambda: submit())
	config_path = "deploy_config.json"
	config = {}
	if os.path.exists(config_path):
		try:
			with open(config_path, "r", encoding="utf-8") as f:
				config = json.load(f)
		except Exception:
			config = {}

	def save_config():
		cfg = {
			"zip_path": zip_var.get(),
			"raspi_path": raspi_var.get(),
			"remote_dir": dir_var.get(),
			"remote_host": host_var.get(),
			"remote_user": user_var.get(),
			"remote_pass": pass_var.get()
		}
		with open(config_path, "w", encoding="utf-8") as f:
			json.dump(cfg, f)

	def browse_zip():
		path = filedialog.askopenfilename(title="Select .llsp3 zip file", filetypes=[("Zip Files", "*.zip;*.llsp3")])
		if path:
			zip_var.set(path)

	def browse_raspi():
		path = filedialog.askopenfilename(title="Select Raspi Functions (.py)", filetypes=[("Python Files", "*.py")])
		if path:
			raspi_var.set(path)

	root = tk.Tk()
	root.title("Deploy Robot Code")
	root.resizable(False, False)

	zip_var = tk.StringVar(value=config.get("zip_path", ""))
	raspi_var = tk.StringVar(value=config.get("raspi_path", ""))
	dir_var = tk.StringVar(value=config.get("remote_dir", ""))
	host_var = tk.StringVar(value=config.get("remote_host", ""))
	user_var = tk.StringVar(value=config.get("remote_user", ""))
	pass_var = tk.StringVar(value=config.get("remote_pass", ""))

	frame = tk.Frame(root, padx=20, pady=20)
	frame.grid(row=0, column=0)

	# Zip file
	tk.Label(frame, text=".llsp3 File:").grid(row=0, column=0, sticky="w", pady=(0,5))
	zip_entry = tk.Entry(frame, textvariable=zip_var, width=32)
	zip_entry.grid(row=1, column=0, sticky="ew", pady=(0,10))
	tk.Button(frame, text="Browse", command=browse_zip, width=10).grid(row=1, column=1, padx=(8,0), pady=(0,10))

	# Raspi Functions file
	tk.Label(frame, text="Raspi Functions:").grid(row=2, column=0, sticky="w", pady=(0,5))
	raspi_entry = tk.Entry(frame, textvariable=raspi_var, width=32)
	raspi_entry.grid(row=3, column=0, sticky="ew", pady=(0,10))
	tk.Button(frame, text="Browse", command=browse_raspi, width=10).grid(row=3, column=1, padx=(8,0), pady=(0,10))

	# Remote Directory
	tk.Label(frame, text="Remote Directory:").grid(row=4, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=dir_var, width=32).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0,10))

	# Remote Host
	tk.Label(frame, text="Remote Host:").grid(row=6, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=host_var, width=32).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0,10))

	# Remote User
	tk.Label(frame, text="Remote User:").grid(row=8, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=user_var, width=32).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0,10))

	# Remote Password
	tk.Label(frame, text="Remote Password:").grid(row=10, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=pass_var, show='*', width=32).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0,10))

	def submit():
		if not zip_var.get():
			messagebox.showerror("Error", "No zip file selected.")
			return
		# Raspi Functions is optional, but check if field is empty before sending
		raspi_path = raspi_var.get() if raspi_var.get() else None
		save_config()

		send_robot_code(
			zip_var.get(),
			dir_var.get(),
			host_var.get(),
			user_var.get(),
			pass_var.get(),
			raspi_path
		)
	tk.Button(frame, text="Deploy", command=submit, width=20).grid(row=12, column=0, columnspan=2, pady=(15,0))

	# Hotkey info
	hotkey_label = tk.Label(frame, text="Press Ctrl+Shift+D to deploy", fg="gray")
	hotkey_label.grid(row=13, column=0, columnspan=2, pady=(10,0))

	root.mainloop()


if __name__ == "__main__":
	main()
