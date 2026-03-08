import os
import threading
from time import sleep
from ..app.main import Controller
from socket import socket, AF_INET, SOCK_STREAM


class RemoteDriveController(Controller):
    def __init__(self):
        super().__init__()
        
        with open(os.path.join(__file__, "remote_drive_code.py"), "r") as f:
            self.code = f.read()

    def run_code(self):
        self.work_event.set()
        worker_thread = threading.Thread(target=self.worker)
        worker_thread.start()

    def start_with_socket(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(("0.0.0.0", 8080))
        self.sock.listen(1)
        print("Waiting for connection...")
        conn, addr = self.sock.accept()
        print(f"Connected by {addr}")
        
        while True:
            data = conn.recv(1024)
            data = data.decode("utf-8")
            if data == "init":
                self.run_code()
            elif data == "stop":
                self.work_event.clear()
                self.stop()
                break
            else:
                self.state.transport.serial.write(data.encode("utf-8"))

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
        
if __name__ == "__main__":
    controller = RemoteDriveController()
    controller.start_with_controller()