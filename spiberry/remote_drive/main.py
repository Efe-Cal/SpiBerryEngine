import configparser
import os
from pathlib import Path
import tempfile
from time import sleep
from spiberry.app.main import Controller
from socket import socket, AF_INET, SOCK_STREAM


DEVICE_TRACE_PREFIX = "TRACE:"
CONFIG_PATH = Path.home() / "spiberry_config.ini"


class RemoteDriveController(Controller):
    def __init__(self):
        self.init_mp_device()
        self.robot_code_source_path = Path(os.path.dirname(__file__)) / "remote_drive_code.py"
        self.robot_code_path = str(self._create_runtime_code_file())
        
        with open(self.robot_code_path, "r", encoding="utf-8") as f:
            self.code = f.read()

    def _create_runtime_code_file(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)

        left_motor = config.get("RemoteDrive", "left_motor", fallback="port.A").strip() or "port.A"
        right_motor = config.get("RemoteDrive", "right_motor", fallback="port.B").strip() or "port.B"

        with open(self.robot_code_source_path, "r", encoding="utf-8") as f:
            remote_drive_code = f.read()

        before_replace = remote_drive_code
        remote_drive_code = remote_drive_code.replace("SOL_TEKER = port.A", f"SOL_TEKER = {left_motor}")
        remote_drive_code = remote_drive_code.replace("SAG_TEKER = port.B", f"SAG_TEKER = {right_motor}")

        if remote_drive_code == before_replace:
            print("[host] Warning: failed to apply one or more motor port config values.")

        runtime_code_path = Path(tempfile.gettempdir()) / "spiberry_remote_drive_code_runtime.py"
        with open(runtime_code_path, "w", encoding="utf-8") as f:
            f.write(remote_drive_code)

        print(f"[host] Remote drive motor config -> left={left_motor}, right={right_motor}")
        return runtime_code_path

    def run_code(self):
        self.robot_code_path = str(self._create_runtime_code_file())
        super().run_code()

    def _trace(self, message):
        print(f"[host] {message}")

    def _trace_serial_in(self, payload):
        if not payload:
            return
        for line in payload.decode("utf-8", errors="replace").splitlines():
            if not line:
                continue
            print(f"[serial<-device] {line}")

    def _drain_serial(self):
        self._trace_serial_in(self.state.transport.serial.read_all())

    def _write_serial_line(self, line):
        self._trace(f"serial->device {line}")
        self.state.transport.serial.write(f"{line}\n".encode("utf-8"))

    def retrieve_actions_log(self):
        self._trace("requesting action log")
        self._write_serial_line("exit")
        log_lines = []
        while True:
            chunk = self.state.transport.serial.readline().decode("utf-8", errors="replace").strip()
            if not chunk:
                continue
            if chunk.startswith(DEVICE_TRACE_PREFIX):
                print(f"[serial<-device] {chunk}")
                continue
            if chunk.startswith(";;") and chunk.endswith(";;"):
                log_lines.append(chunk[2:-2])
                break
            print(f"[serial<-device] {chunk}")
            log_lines.append(chunk)
        self.actions = "\n".join(log_lines)
        self._trace(f"received action log {self.actions}")
    
    def start_with_socket(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(("0.0.0.0", 8080))
        self.sock.listen(1)
        print("Waiting for connection...")
        conn, addr = self.sock.accept()
        print(f"Connected by {addr}")
        
        try:
            self.run_code()

            buffer = ""
            while True:
                self._drain_serial()
                
                chunk = conn.recv(1024).decode("utf-8")
                if not chunk:
                    break

                self._trace(f"socket->host {chunk!r}")

                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    self._trace(f"host parsed command {line}")

                    parts = line.split(";")
                    command = parts[0]

                    if command == "move":
                        speed = parts[1] if len(parts) > 1 else "0"
                        self._write_serial_line(f"move;{speed}")

                    elif command == "stop_move":
                        self._write_serial_line("stop")

                    elif command == "turn":
                        turn_motor = parts[1]
                        motor_direction = parts[2] if len(parts) > 2 else "1"
                        self._write_serial_line(f"turn;{turn_motor};{motor_direction}")

                    elif command == "stop_turn":
                        turn_motor = parts[1]
                        self._write_serial_line(f"stop_turn;{turn_motor}")

                    elif command == "two_wheel_turn":
                        turn_direction = parts[1]
                        self._write_serial_line(f"two_wheel_turn;{turn_direction}")

                    elif command == "stop_two_wheel_turn":
                        self._write_serial_line("stop_two_wheel_turn")

                    elif command == "retrieve_log":
                        self.retrieve_actions_log()
                        conn.sendall(self.actions.encode("utf-8"))

                    elif command == "exit":
                        self._trace("socket requested shutdown")
                        self.stop(self.state)
                        return
        finally:
            conn.close()
            self.sock.close()

    def start_with_controller(self):
        from approxeng.input.selectbinder import ControllerResource
        self.run_code()
        
        with ControllerResource(deadzone=0.15) as joystick:
            while joystick.connected:
                self._drain_serial()
                joystick.check_presses()
                
                if joystick.presses.square:
                    command = f"move;{int(joystick.ly*1000)}"
                    self._trace(f"controller action {command}")
                    self._write_serial_line(command)
                    while not joystick.releases.square:
                        joystick.check_presses()
                        sleep(0.01)
                    self._trace("controller action stop")
                    self._write_serial_line("stop")
                elif abs(joystick.lx) > 0.5:
                    # determin motor and turn direction 
                    turn_motor = "right" if joystick.rx > 0 else "left"
                    motor_direction = 1 if joystick.rx > 0 else -1
                    command = f"turn;{turn_motor};{motor_direction}"
                    self._trace(f"controller action {command}")
                    self._write_serial_line(command)
                    while abs(joystick.lx) > 0.5:
                        joystick.check_presses()
                        sleep(0.01)
                    self._trace(f"controller action stop_turn;{turn_motor}")
                    self._write_serial_line(f"stop_turn;{turn_motor}")
                
                elif joystick.presses.dright or joystick.presses.dleft:
                    turn_direction = -1 if joystick.presses.dright else 1
                    command = f"two_wheel_turn;{turn_direction}"
                    self._trace(f"controller action {command}")
                    self._write_serial_line(command)
                    while not (joystick.releases.dright or joystick.releases.dleft):
                        joystick.check_presses()
                        sleep(0.01)
                    self._trace("controller action stop_two_wheel_turn")
                    self._write_serial_line("stop_two_wheel_turn")
                
                elif joystick.presses.ls and joystick.presses.rs:
                    self.retrieve_actions_log()
                    print("Actions log:", self.actions)
                                    
if __name__ == "__main__":
    controller = RemoteDriveController()
    controller.start_with_controller()