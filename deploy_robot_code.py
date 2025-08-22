import sys
import zipfile
import tempfile
import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import paramiko
def send_robot_code(zip_path, remote_dir, remote_host, remote_user, remote_pass):
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

		# Send to remote machine using paramiko
		remote_path = f"/home/{remote_user}/{remote_dir}/robot_code.py"
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
			sftp.close()
			ssh.close()
			messagebox.showinfo("Success", f"robot_code.py sent to {remote_host}:{remote_path}")
		except Exception as e:
			messagebox.showerror("SCP Error", f"Failed to send file via paramiko: {e}")


	

def main():
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

	root = tk.Tk()
	root.title("Deploy Robot Code")
	root.resizable(False, False)

	zip_var = tk.StringVar(value=config.get("zip_path", ""))
	dir_var = tk.StringVar(value=config.get("remote_dir", ""))
	host_var = tk.StringVar(value=config.get("remote_host", ""))
	user_var = tk.StringVar(value=config.get("remote_user", ""))
	pass_var = tk.StringVar(value=config.get("remote_pass", ""))

	frame = tk.Frame(root, padx=20, pady=20)
	frame.grid(row=0, column=0)

	# Zip file
	tk.Label(frame, text=".llsp3 Zip File:").grid(row=0, column=0, sticky="w", pady=(0,5))
	zip_entry = tk.Entry(frame, textvariable=zip_var, width=32)
	zip_entry.grid(row=1, column=0, sticky="ew", pady=(0,10))
	tk.Button(frame, text="Browse", command=browse_zip, width=10).grid(row=1, column=1, padx=(8,0), pady=(0,10))

	# Remote Directory
	tk.Label(frame, text="Remote Directory:").grid(row=2, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=dir_var, width=32).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0,10))

	# Remote Host
	tk.Label(frame, text="Remote Host:").grid(row=4, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=host_var, width=32).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0,10))

	# Remote User
	tk.Label(frame, text="Remote User:").grid(row=6, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=user_var, width=32).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0,10))

	# Remote Password
	tk.Label(frame, text="Remote Password:").grid(row=8, column=0, sticky="w", pady=(0,5))
	tk.Entry(frame, textvariable=pass_var, show='*', width=32).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0,10))

	def submit():
		if not zip_var.get():
			messagebox.showerror("Error", "No zip file selected.")
			return
		zip_var.get()
		dir_var.get()
		host_var.get()
		user_var.get()
		pass_var.get()
		save_config()

		send_robot_code(
			zip_var.get(),
			dir_var.get(),
			host_var.get(),
			user_var.get(),
			pass_var.get()
		)
	tk.Button(frame, text="Deploy", command=submit, width=20).grid(row=10, column=0, columnspan=2, pady=(15,0))

	root.mainloop()




if __name__ == "__main__":
	main()
