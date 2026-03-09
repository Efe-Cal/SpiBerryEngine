import os
from time import sleep
from ..app.main import Controller
from socket import socket, AF_INET, SOCK_STREAM


class RemoteDriveController(Controller):
    def __init__(self):
        super().__init__()
        
        with open(os.path.join(__file__, "remote_drive_code.py"), "r") as f:
            self.code = f.read()

    def retrieve_actions_log(self):
        self.state.transport.serial.write(b"exit\n")
        log_data = b""
        while True:
            chunk = self.state.transport.serial.readline()
            if chunk.startswith(b";;") and chunk.endswith(b";;"):
                log_data += chunk[2:-2]
                break
            log_data += chunk
        self.actions = log_data.decode("utf-8")
    
    def start_with_socket(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(("0.0.0.0", 8080))
        self.sock.listen(1)
        print("Waiting for connection...")
        conn, addr = self.sock.accept()
        print(f"Connected by {addr}")
        
        self.run_code()

        buffer = ""
        while True:
            chunk = conn.recv(1024).decode("utf-8")
            if not chunk:
                break

            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                parts = line.split(";")
                command = parts[0]

                if command == "move":
                    speed = parts[1] if len(parts) > 1 else "0"
                    self.state.transport.serial.write(b"move;" + speed.encode("utf-8") + b"\n")

                elif command == "stop_move":
                    self.state.transport.serial.write(b"stop\n")

                elif command == "turn":
                    turn_motor = parts[1]
                    motor_direction = parts[2] if len(parts) > 2 else "1"
                    self.state.transport.serial.write(b"turn;" + turn_motor.encode("utf-8") + b";" + motor_direction.encode("utf-8") + b"\n")

                elif command == "stop_turn":
                    turn_motor = parts[1]
                    self.state.transport.serial.write(b"stop_turn;" + turn_motor.encode("utf-8") + b"\n")

                elif command == "two_wheel_turn":
                    turn_direction = parts[1]
                    self.state.transport.serial.write(b"two_wheel_turn;" + turn_direction.encode("utf-8") + b"\n")

                elif command == "stop_two_wheel_turn":
                    self.state.transport.serial.write(b"stop_two_wheel_turn\n")

                elif command == "retrieve_log":
                    self.retrieve_actions_log()
                    conn.sendall(self.actions.encode("utf-8"))

                elif command == "exit":
                    self.work_event.clear()
                    self.stop()
                    conn.close()
                    self.sock.close()
                    return

        conn.close()
        self.sock.close()

    def start_with_controller(self):
        from approxeng.input.selectbinder import ControllerResource
        self.run_code()
        
        with ControllerResource(deadzone=0.15) as joystick:
            while joystick.connected:
                joystick.check_presses()
                
                if joystick.presses.square:
                    self.state.transport.serial.write(b"move;"+str(int(joystick.ly*1000)).encode("utf-8")+b"\n")
                    while not joystick.releases.square:
                        joystick.check_presses()
                        sleep(0.01)
                    self.state.transport.serial.write(b"stop\n")
                elif abs(joystick.lx) > 0.5:
                    # determin motor and turn direction 
                    turn_motor = "right" if joystick.rx > 0 else "left"
                    motor_direction = 1 if joystick.rx > 0 else -1
                    self.state.transport.serial.write(b"turn;"+turn_motor.encode("utf-8")+b";"+str(motor_direction).encode("utf-8")+b"\n")
                    while abs(joystick.lx) > 0.5:
                        sleep(0.01)
                    self.state.transport.serial.write(b"stop_turn;"+turn_motor.encode("utf-8")+b"\n")
                
                elif joystick.presses.dright or joystick.presses.dleft:
                    turn_direction = -1 if joystick.presses.dright else 1
                    self.state.transport.serial.write(b"two_wheel_turn;"+str(turn_direction).encode("utf-8")+b"\n")
                    while not (joystick.releases.dright or joystick.releases.dleft):
                        sleep(0.01)
                    self.state.transport.serial.write(b"stop_two_wheel_turn\n")
                
                elif joystick.presses.ls and joystick.presses.rs:
                    self.retrieve_actions_log()

                
if __name__ == "__main__":
    controller = RemoteDriveController()
    controller.start_with_controller()