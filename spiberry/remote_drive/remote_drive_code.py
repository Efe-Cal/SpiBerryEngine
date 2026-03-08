import motor # type: ignore
import motor_pair # type: ignore
import runloop # type: ignore
from hub import motion_sensor, port # type: ignore
import utime # type: ignore
import color_sensor # type: ignore
import hub # type: ignore
import sys
import select

print("Battery Voltage:",hub.battery_voltage())
print("Battery Current:",hub.battery_current())
print("Battery Temp:",hub.battery_temperature())

SOL_TEKER = port.A
SAG_TEKER = port.B


class Device:
    def __init__(self, device_type, device_name, *args):
        self.device_type = device_type
        self.device_name = device_name
        self.args = args

    def __repr__(self):
        return f"Device(type={self.device_type}, name={self.device_name}, args={self.args})"

class Servo(Device):
    def get_angle(self, timeout=1):
        print(f";devices.{self.device_name}.get_angle();")
        return sys.stdin.readline().strip()
    def set_angle(self, angle, timeout=2):
        print(f";devices.{self.device_name}.set_angle({angle});")
        return sys.stdin.readline().strip()

class DistanceSensor(Device):
    def get_distance(self, timeout=1):
        print(f";devices.{self.device_name}.get_distance();")
        return sys.stdin.readline().strip()

class Raspi:
    def register_device(self, device_type, device_name, *args, timeout=1):
        print(f";devices.register({device_type}, {device_name}, {', '.join(args)});")
        sys.stdin.readline().strip()

        if device_type == "servo":
            return Servo(device_type, device_name, *args)
        elif device_type == "distance_sensor":
            return DistanceSensor(device_type, device_name, *args)
        else:
            raise ValueError(f"Unsupported device type: {device_type}")
    def func(self, func_string):
        print(f";raspi_functions.{func_string};")
        r = sys.stdin.readline().strip()
        print(r)
        return r


def getGyro():
    return -1*motion_sensor.tilt_angles()[0]

angle = getGyro()

def moveWithGyro(velocity:int):
    global angle
    utime.sleep_ms(30)
    motor_pair.stop(motor_pair.PAIR_1)
    start_time = utime.ticks_ms()
    
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            line = sys.stdin.readline().strip()
            break
        adj = int(angle-getGyro())
        motor_pair.move_tank(motor_pair.PAIR_1, velocity + adj, velocity - adj)

    motor_pair.stop(motor_pair.PAIR_1)
    utime.sleep_ms(30)
    
    return utime.ticks_diff(utime.ticks_ms(), start_time)

def twoWheelTurn(turn_direction, speed = 1):
    motor_pair.stop(motor_pair.PAIR_1,stop=motor.BRAKE)
    utime.sleep_ms(100)
    
    init_gyro = getGyro()
    
    motor_pair.move_tank(motor_pair.PAIR_1, -100*turn_direction*speed, 100*turn_direction*speed)
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            line = sys.stdin.readline().strip()
            break
        final_gyro = getGyro()

    motor_pair.stop(motor_pair.PAIR_1,stop=motor.HOLD)
    utime.sleep_ms(100)
    return final_gyro - init_gyro

def gyroTurn(motor_turn_direction, turning_motor, speed=1):

    utime.sleep_ms(30)
    
    init_gyro = getGyro()
    
    motor.run(turning_motor, motor_turn_direction*100*speed)

    while True:    
        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            line = sys.stdin.readline().strip()
            break
        
        final_gyro = getGyro()
          
    motor_pair.stop(motor_pair.PAIR_1, stop=motor.HOLD)
    utime.sleep_ms(100)
    
    return final_gyro - init_gyro

sequence = []

motors = {
    "left": SOL_TEKER,
    "right": SAG_TEKER
}

def main_loop():
    global angle
    turn_init_gyro = None
    while True:
        command = input().split(";")[0]
        
        if command[0] == "move":
            adj = int(angle-getGyro())
            motor_pair.move_tank(motor_pair.PAIR_1, int(command[1]) + adj, int(command[1]) - adj)
        
        elif command[0] == "stop":
            # TODO log action
            motor_pair.stop(motor_pair.PAIR_1)
        
        
        elif command[0] == "turn":
            turn_init_gyro = getGyro()
            utime.sleep_ms(30)
            motor_to_turn = motors[command[1]]
            motor.run(motor_to_turn, int(command[2])*100)
            
        elif command[0] == "stop_turn":
            motor_to_turn = motors[command[1]]
            motor.stop(motor_to_turn, stop=motor.HOLD)
            utime.sleep_ms(30)
            turn_final_gyro = getGyro()
            # TODO log action (turn_final_gyro - turn_init_gyro)
            turn_init_gyro = None


        elif command[0] == "two_wheel_turn":
            turn_init_gyro = getGyro()
            utime.sleep_ms(30)
            motor_pair.move_tank(motor_pair.PAIR_1, -100*command[1], 100*command[1])
        elif command[0] == "stop_two_wheel_turn":
            motor_pair.stop(motor_pair.PAIR_1, stop=motor.HOLD)
            utime.sleep_ms(30)
            turn_final_gyro = getGyro()
            # TODO log action (turn_final_gyro - turn_init_gyro)
            turn_init_gyro = None
        
        elif command[0] == "exit":
            break

if __name__ == "__main__":
    main_loop()