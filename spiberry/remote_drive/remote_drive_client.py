import tkinter as tk
from socket import socket, AF_INET, SOCK_STREAM


class RemoteDriveClient:
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.sock = None

        self.root = tk.Tk()
        self.root.title("SpiBerry Remote Drive")
        self.root.resizable(False, False)

        self._build_ui()
        self._bind_keys()

    def _build_ui(self):
        # Connection frame
        conn_frame = tk.LabelFrame(self.root, text="Connection", padx=5, pady=5)
        conn_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(conn_frame, text="Host:").grid(row=0, column=0)
        self.host_entry = tk.Entry(conn_frame, width=15)
        self.host_entry.insert(0, self.host)
        self.host_entry.grid(row=0, column=1, padx=5)

        tk.Label(conn_frame, text="Port:").grid(row=0, column=2)
        self.port_entry = tk.Entry(conn_frame, width=6)
        self.port_entry.insert(0, str(self.port))
        self.port_entry.grid(row=0, column=3, padx=5)

        self.connect_btn = tk.Button(conn_frame, text="Connect", command=self._connect)
        self.connect_btn.grid(row=0, column=4, padx=5)

        self.status_label = tk.Label(conn_frame, text="Disconnected", fg="red")
        self.status_label.grid(row=0, column=5, padx=5)

        # Move frame
        move_frame = tk.LabelFrame(self.root, text="Move (W/S or buttons)", padx=5, pady=5)
        move_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(move_frame, text="Speed:").pack(side="left")
        self.speed_entry = tk.Entry(move_frame, width=6)
        self.speed_entry.insert(0, "500")
        self.speed_entry.pack(side="left", padx=5)

        tk.Button(move_frame, text="Move", command=self._move).pack(side="left", padx=2)
        tk.Button(move_frame, text="Stop Move", command=self._stop_move).pack(side="left", padx=2)

        # Turn frame
        turn_frame = tk.LabelFrame(self.root, text="Single-Wheel Turn", padx=5, pady=5)
        turn_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(turn_frame, text="Motor:").pack(side="left")
        self.turn_motor_var = tk.StringVar(value="left")
        tk.Radiobutton(turn_frame, text="Left", variable=self.turn_motor_var, value="left").pack(side="left")
        tk.Radiobutton(turn_frame, text="Right", variable=self.turn_motor_var, value="right").pack(side="left")

        tk.Label(turn_frame, text="Direction:").pack(side="left", padx=(10, 0))
        self.turn_dir_var = tk.StringVar(value="1")
        tk.Radiobutton(turn_frame, text="Forward (1)", variable=self.turn_dir_var, value="1").pack(side="left")
        tk.Radiobutton(turn_frame, text="Backward (-1)", variable=self.turn_dir_var, value="-1").pack(side="left")

        tk.Button(turn_frame, text="Turn", command=self._turn_selected).pack(side="left", padx=5)
        tk.Button(turn_frame, text="Stop Turn", command=self._stop_turn_selected).pack(side="left", padx=2)

        # Two-wheel turn frame
        tw_frame = tk.LabelFrame(self.root, text="Two-Wheel Turn (Q/E)", padx=5, pady=5)
        tw_frame.pack(padx=10, pady=5, fill="x")

        tk.Button(tw_frame, text="Turn Left (-1)", command=lambda: self._two_wheel_turn("-1")).pack(side="left", padx=2)
        tk.Button(tw_frame, text="Turn Right (1)", command=lambda: self._two_wheel_turn("1")).pack(side="left", padx=2)
        tk.Button(tw_frame, text="Stop", command=self._stop_two_wheel_turn).pack(side="left", padx=2)

        # Actions frame
        actions_frame = tk.LabelFrame(self.root, text="Actions", padx=5, pady=5)
        actions_frame.pack(padx=10, pady=5, fill="x")

        tk.Button(actions_frame, text="Retrieve Log", command=self._retrieve_log).pack(side="left", padx=2)
        tk.Button(actions_frame, text="Exit", command=self._exit).pack(side="left", padx=2)

        # Log display
        self.log_text = tk.Text(self.root, height=6, width=60, state="disabled")
        self.log_text.pack(padx=10, pady=5)

    def _bind_keys(self):
        self.root.bind("<KeyPress-w>", lambda e: self._move())
        self.root.bind("<KeyRelease-w>", lambda e: self._stop_move())
        self.root.bind("<KeyPress-s>", lambda e: self._move())
        self.root.bind("<KeyRelease-s>", lambda e: self._stop_move())
        self.root.bind("<KeyPress-a>", lambda e: self._turn_selected())
        self.root.bind("<KeyRelease-a>", lambda e: self._stop_turn_selected())
        self.root.bind("<KeyPress-d>", lambda e: self._turn_selected())
        self.root.bind("<KeyRelease-d>", lambda e: self._stop_turn_selected())
        self.root.bind("<KeyPress-q>", lambda e: self._two_wheel_turn("1"))
        self.root.bind("<KeyRelease-q>", lambda e: self._stop_two_wheel_turn())
        self.root.bind("<KeyPress-e>", lambda e: self._two_wheel_turn("-1"))
        self.root.bind("<KeyRelease-e>", lambda e: self._stop_two_wheel_turn())

    def _log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _send(self, command):
        if not self.sock:
            self._log("Not connected!")
            return
        try:
            self.sock.sendall((command + "\n").encode("utf-8"))
            self._log(f"Sent: {command}")
        except Exception as e:
            self._log(f"Error: {e}")

    def _connect(self):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((host, port))
            self.status_label.config(text="Connected", fg="green")
            self._log(f"Connected to {host}:{port}")
        except Exception as e:
            self.sock = None
            self._log(f"Connection failed: {e}")

    def _move(self):
        speed = self.speed_entry.get()
        self._send(f"move;{speed//1000}")

    def _stop_move(self):
        self._send("stop_move")

    def _turn(self, motor, direction):
        self._send(f"turn;{motor};{direction}")

    def _turn_selected(self):
        self._turn(self.turn_motor_var.get(), self.turn_dir_var.get())

    def _stop_turn(self, motor):
        self._send(f"stop_turn;{motor}")

    def _stop_turn_selected(self):
        self._stop_turn(self.turn_motor_var.get())

    def _two_wheel_turn(self, direction):
        self._send(f"two_wheel_turn;{direction}")

    def _stop_two_wheel_turn(self):
        self._send("stop_two_wheel_turn")

    def _retrieve_log(self):
        self._send("retrieve_log")
        if self.sock:
            try:
                data = self.sock.recv(4096).decode("utf-8")
                self._log(f"Log: {data}")
            except Exception as e:
                self._log(f"Error receiving log: {e}")

    def _exit(self):
        self._send("exit")
        if self.sock:
            self.sock.close()
            self.sock = None
        self.status_label.config(text="Disconnected", fg="red")
        self._log("Disconnected.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    RemoteDriveClient().run()
