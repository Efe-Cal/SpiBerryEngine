import threading
from time import sleep
import argparse

import RPi.GPIO as GPIO # type: ignore
from RGBLED import RGBLED

import sys
import serial.serialutil
import importlib
try:
    import raspi_functions
except ImportError:
    pass

parser = argparse.ArgumentParser(description="SpiBerryEngine GPIO pin configuration")
parser.add_argument('--button', type=int, default=11, help='GPIO pin for button (default: 11)')
parser.add_argument('--red', type=int, default=22, help='GPIO pin for RGBLED red (default: 22)')
parser.add_argument('--green', type=int, default=10, help='GPIO pin for RGBLED green (default: 10)')
parser.add_argument('--blue', type=int, default=9, help='GPIO pin for RGBLED blue (default: 9)')
args = parser.parse_args()

GPIO.setmode(GPIO.BCM)
GPIO.setup(args.button, GPIO.HIGH, pull_up_down=GPIO.PUD_UP)
rgbLED = RGBLED(args.red, args.green, args.blue, active_high=False)

try:
    from mpremote import commands, transport
    from mpremote.main import State
except ModuleNotFoundError:
    rgbLED.blink("red", duration=0.2, count=2)
    print("mpremote module not found.")
    sys.exit(0)

state = State()
try:
    commands.do_connect(state)
except (transport.TransportError, commands.CommandError) as e:
    rgbLED.blink("red", duration=0.2, count=3)
    print("Error connecting to the device:")
    sys.exit(0)

def stop(state:State):
    commands.do_disconnect(state)
    commands.do_connect(state)
    commands.do_soft_reset(state)


with open("robot_code.py","r") as f:
    code = f.read()
    
work_event = threading.Event()
worker_thread = None

def read_function_call(state:State):
    try:
        func_call = state.transport.read_until(8, b":",timeout=999)
    except serial.serialutil.SerialException as e:
        if "ClearCommError" in str(e):
            if not work_event.is_set():
                sys.exit(1)
            print("Serial port error")
        else:
            raise e
    func_call = func_call.decode()[:-1].strip()
    return func_call

def run_function(func_call:str):
    result_string = ""
    if not func_call=="" and func_call.isprintable():
        try:
            result_string = eval("raspi_functions."+func_call)
        except NameError as e:
            rgbLED.blink("blue", duration=0.5, count=2)
            print("NameError in function call: ", e)
            result_string = ""
        except Exception as e:
            print("Error in function call: ", e)
            result_string = ""
    return result_string

def worker():
    try:
        state.transport.enter_raw_repl()
    except transport.TransportError as e:
        rgbLED.blink("blue", duration=0.2, count=3)
        print("Error entering raw REPL:", e)
        sys.exit(0)
    try:
        state.transport.exec_raw_no_follow(code)
    except transport.TransportError as e:
        rgbLED.blink("red", duration=0.2, count=3)
        print("Error executing code:", e)
        sys.exit(0)

    rgbLED.green()
    
    func_call = read_function_call(state)
    
    while func_call!="exit" and work_event.is_set():
        sleep(0.05)
        print("Function call: ",func_call)
        
        result_string = run_function(func_call)
        
        state.transport.serial.write(f"{result_string}\r\n".encode())
        state.transport.read_until(8,result_string.encode()) # clean up the acknowledgment
        
        func_call = read_function_call(state)
    print("Code finished.")
    work_event.clear()
    
try:
    while True:
        if GPIO.input(args.button_pin)==0:
            if work_event.is_set():
                print("Button pressed, stopping work...")
                work_event.clear()
                stop(state)
                rgbLED.red()
            else:
                with open("robot_code.py","r") as f:
                    code = f.read()
                importlib.reload(raspi_functions)
                work_event.set()
                worker_thread = threading.Thread(target=worker)
                worker_thread.start()
                print("Button pressed, starting work...")

                rgbLED.yellow()

            sleep(0.3)
except Exception as e:
    print("Error occurred: ",e)
except KeyboardInterrupt:
    print("KeyboardInterrupt received, stopping...")
    if work_event.is_set():
        work_event.clear()
        stop(state)
        rgbLED.red()
    else:
        print("No work to stop.")
finally:
    print("Cleaning up GPIO")
    GPIO.cleanup()
    print("Exiting program")