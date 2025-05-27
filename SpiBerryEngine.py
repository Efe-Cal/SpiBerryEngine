from mpremote import commands
from mpremote.main import State

import threading
from time import sleep

import RPi.GPIO as GPIO # type: ignore
from RGBLED import RGBLED
try:
    from raspi_functions import *
except ImportError:
    pass

GPIO.setmode(GPIO.BCM)
GPIO.setup(11, GPIO.HIGH, pull_up_down=GPIO.PUD_UP)
rgbLED = RGBLED(22, 10, 9, active_high=False)

state = State()
commands.do_connect(state)

def stop(state:State):
    commands.do_disconnect(state)
    commands.do_connect(state)
    commands.do_soft_reset(state)


with open("robot_code.py","r") as f:
    code = f.read()

work = False
def worker():
    global work
    state.transport.enter_raw_repl()
    state.transport.exec_raw_no_follow(code)
    rgbLED.green()
    func_call = state.transport.read_until(8,b":")
    func_call =func_call.decode()[:-1].strip()
    print("func call:",func_call)
    
    while func_call!=":" and work:
        sleep(0.01)
        print("Function call: ",func_call)
        result_string = eval(func_call)
        state.transport.serial.write(f"{result_string}\r\n".encode())
        
        state.transport.follow(timeout=10,data_consumer=lambda x: print("Follow Data: ",x,"\n\n"))
        
        func_call = state.transport.read_until(8,b":")
        func_call = func_call.decode()[:-1].strip()
        
        print("Function called: ",func_call)
    
    print("Soft reset")
    stop(state)
    

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
            t.join()
            sleep(0.1)
except Exception as e:
    print("error occurred: ",e)
finally:
    print("Cleaning up GPIO")
    GPIO.cleanup()
    print("Exiting program")