import threading
from time import sleep

import RPi.GPIO as GPIO # type: ignore
from RGBLED import RGBLED
import sys

try:
    from raspi_functions import *
except ImportError:
    pass

GPIO.setmode(GPIO.BCM)
GPIO.setup(11, GPIO.HIGH, pull_up_down=GPIO.PUD_UP)
rgbLED = RGBLED(22, 10, 9, active_high=False)

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

work = False
def worker():
    global work
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
    func_call = state.transport.read_until(8,b":")
    func_call =func_call.decode()[:-1].strip()
    print("func call:",func_call)
    
    while func_call!="***" and work:
        sleep(0.05)
        print("Function call: ",func_call)
        result_string = ""
        if not func_call=="" and func_call.isprintable():
            try:
                result_string = eval(func_call)
            except NameError as e:
                rgbLED.blink("blue", duration=0.5, count=2)
                print("NameError in function call: ", e)
                result_string = ""
            except Exception as e:
                print("Error in function call: ", e)
                result_string = ""
        state.transport.serial.write(f"{result_string}\r\n".encode())
        
        # state.transport.follow(timeout=10,data_consumer=lambda x: print("Follow Data: ",x,"\n\n"))
        
        func_call = state.transport.read_until(8,b":")
        func_call = func_call.decode()[:-1].strip()    

try:
    while True:
        if GPIO.input(11)==0:
            if work:
                print("Button pressed, stopping work...")
                work = False
                stop(state)
                rgbLED.red()
            else:
                t = threading.Thread(target=worker)
                t.start()
                print("Button pressed, starting work...")
                work = True
                rgbLED.yellow()
            sleep(0.3)
except Exception as e:
    print("error occurred: ",e)
finally:
    print("Cleaning up GPIO")
    GPIO.cleanup()
    print("Exiting program")