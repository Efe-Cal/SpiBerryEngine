import motor # type: ignore
import motor_pair # type: ignore
import runloop # type: ignore
from hub import motion_sensor, port # type: ignore
import utime # type: ignore
import color_sensor # type: ignore
import hub # type: ignore
import sys
import select


TRACE_PREFIX = "TRACE:"


def trace(message):
    print(f"{TRACE_PREFIX}{message}")

print("Battery Voltage:",hub.battery_voltage())
print("Battery Current:",hub.battery_current())
print("Battery Temp:",hub.battery_temperature())

SOL_TEKER = port.A
SAG_TEKER = port.B


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

motors = {
    "left": SOL_TEKER,
    "right": SAG_TEKER
}

def main_loop():
    global angle
    actions_log = []
    command = None
    move_init_time = None
    turn_init_gyro = None

    motor_pair.pair(motor_pair.PAIR_1, SOL_TEKER, SAG_TEKER)
    trace("paired drive motors")
    
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            line = sys.stdin.readline().strip()
            trace(f"rx {line}")
            command = line.split(";")

        if isinstance(command, list) and command[0] == "move":
            if not move_init_time:
                move_init_time = utime.ticks_ms()
            adj = int(angle-getGyro())
            trace(f"branch move speed={command[1]} adj={adj}")
            motor_pair.move_tank(motor_pair.PAIR_1, int(command[1]) + adj, int(command[1]) - adj)
        
        elif isinstance(command, list) and command[0] == "stop":
            move_duration = utime.ticks_diff(utime.ticks_ms(), move_init_time)
            trace(f"branch stop duration_ms={move_duration}")
            actions_log.append(("move", move_duration))
            motor_pair.stop(motor_pair.PAIR_1)
            command = None
            utime.sleep_ms(30)
        
        elif isinstance(command, list) and command[0] == "turn":
            if not turn_init_gyro:
                turn_init_gyro = getGyro()
            utime.sleep_ms(30)
            motor_to_turn = motors[command[1]]
            trace(f"branch turn motor={command[1]} direction={command[2]}")
            motor.run(motor_to_turn, int(command[2])*100)
            command = None
            
        elif isinstance(command, list) and command[0] == "stop_turn":
            motor_to_turn = motors[command[1]]
            motor.stop(motor_to_turn, stop=motor.HOLD)
            utime.sleep_ms(30)
            turn_final_gyro = getGyro()
            turn_delta = turn_final_gyro - turn_init_gyro
            angle = turn_final_gyro
            trace(f"branch stop_turn motor={command[1]} delta={turn_delta}")

            actions_log.append(("turn", turn_delta))
            turn_init_gyro = None
            command = None


        elif isinstance(command, list) and command[0] == "two_wheel_turn":
            if not turn_init_gyro:
                turn_init_gyro = getGyro()
            utime.sleep_ms(30)
            trace(f"branch two_wheel_turn direction={command[1]}")
            motor_pair.move_tank(motor_pair.PAIR_1, -100*int(command[1]), 100*int(command[1]))
            command = None

        elif isinstance(command, list) and command[0] == "stop_two_wheel_turn":
            motor_pair.stop(motor_pair.PAIR_1, stop=motor.HOLD)
            utime.sleep_ms(30)
            turn_final_gyro = getGyro()
            turn_delta = turn_final_gyro - turn_init_gyro
            angle = turn_final_gyro
            trace(f"branch stop_two_wheel_turn delta={turn_delta}")
            
            actions_log.append(("two_wheel_turn", turn_delta))
            turn_init_gyro = None
            command = None
        
        elif isinstance(command, list) and command[0] == "exit":
            trace("branch exit")
            break
        elif command is not None:
            trace(f"unknown command {command}")
            command = None

    print(";;" + str(actions_log) + ";;")

if __name__ == "__main__":
    main_loop()