import sys
import re
import logging
import threading
import argparse
import importlib
from time import sleep

import gpiozero
from gpiozero import RGBLED, Button

import serial.serialutil

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("spiberryengine.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SpiBerryEngine")

PRINT_LEVEL = 25
logging.addLevelName(PRINT_LEVEL, "PRINT")

def print_log(self, message, *args, **kwargs):
    if self.isEnabledFor(PRINT_LEVEL):
        self._log(PRINT_LEVEL, message, args, **kwargs)

logging.Logger.print = print_log

parser = argparse.ArgumentParser(description="SpiBerryEngine GPIO pin configuration")
parser.add_argument('--button', type=int, default=17, help='GPIO pin for button')
parser.add_argument('--red', type=int, default=0, help='GPIO pin for RGBLED red')
parser.add_argument('--green', type=int, default=11, help='GPIO pin for RGBLED green')
parser.add_argument('--blue', type=int, default=9, help='GPIO pin for RGBLED blue')
parser.add_argument('code_path', nargs='?', default='robot_code.py', help='Path to the robot code file')
args = parser.parse_args()
ROBOT_CODE = args.code_path

rgbLED = RGBLED(args.red, args.green, args.blue, active_high=False)
button = Button(args.button,pull_up=True)

supported_devices = ["distance_sensor", "servo"]

try:
    from mpremote import commands, transport
    from mpremote.main import State
except ModuleNotFoundError:
    # Blink red 5 times
    rgbLED.blink(on_time=0.1, off_time=0.1, n=5, on_color=(1,0,0), off_color=(0,0,0), background=False)
    logger.critical("mpremote module not found.")
    sys.exit(1)

try:
    import raspi_functions
except ImportError:
    # Blink red 2 times
    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(1,0,0), off_color=(0,0,0), background=False)
    logger.warning("raspi_functions module not found")

with open(ROBOT_CODE,"r") as f:
    code = f.read()
    logger.info("Loaded robot_code.py.")

class HotReloadHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_code = code

    def on_modified(self, event):
        global code
        if event.src_path.endswith(ROBOT_CODE):
            with open(ROBOT_CODE, "r") as f:
                new_code = f.read()
                if new_code != self.last_code:
                    logger.info("Hot reloaded robot_code.py")
                    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,1), off_color=(0,0,0), background=False)
                    code = new_code
                    self.last_code = new_code
                    
        elif event.src_path.endswith("raspi_functions.py"):
            importlib.reload(raspi_functions)
            logger.info("Hot reloaded raspi_functions module.")
            rgbLED.blink(on_time=0.2, off_time=0.2, n=3, on_color=(0,1,1), off_color=(0,0,0), background=False)

observer = Observer()
event_handler = HotReloadHandler()
observer.schedule(event_handler, ".", recursive=False)
observer.start()

state = State()
try:
    commands.do_connect(state)
    logger.info("Connected to device successfully.")
except (transport.TransportError, commands.CommandError) as e:
    # Blink red 5 times
    rgbLED.blink(on_time=0.3, off_time=0.3, n=5, on_color=(1,0,0), off_color=(0,0,0), background=False)
    logger.critical(f"Error connecting to the device: {e}")
    sys.exit(1)

def stop(state:State):
    global devices
    logger.info("Stopping and resetting device connection.")
    commands.do_disconnect(state)
    commands.do_connect(state)
    sleep(0.1)
    commands.do_soft_reset(state)
    del devices
    devices = {}

work_event = threading.Event()
worker_thread = None

devices = {}

def handle_device_function_call(func_call:str):
    global devices
    result_string = ""
    function, params = func_call.split("(")
    function = function.split(".")[1:]
    inside_paranthesis = params[:-1]
    params = inside_paranthesis.split(",") # type, name, pin(s), arg(s)
    params = [p.strip() for p in params]
    
    # devices.register(servo, s1, 17)
    # devices.register(distance_sensor, d1, 15, 16, 4)
    if len(function) == 1:
        if params and params[0] in supported_devices:
            if params[0] == "distance_sensor":
                devices[params[1]] = gpiozero.DistanceSensor(echo=int(params[2]), trigger=int(params[3]), max_distance=float(params[4]))
            elif params[0] == "servo":
                devices[params[1]] = gpiozero.AngularServo(int(params[2]),min_angle=int(params[3]),max_angle=int(params[4]),min_pulse_width=float(params[5]),max_pulse_width=float(params[6]),initial_angle=int(params[7]))
    # devices.d1.get_distance()
    # devices.s1.set_angle(90)
    elif len(function) == 2:
        if function[0] in devices.keys():
            if "get_distance" in function[1]:
                result_string = str(devices[function[0]].distance*100)
            elif "get_angle" in function[1]:
                result_string = str(devices[function[0]].angle)
            elif "set_angle" in function[1]:
                angle = params[0]
                devices[function[0]].angle = int(angle)
                result_string = f"Set angle of {function[1]} to {angle}"
            else:
                result_string = "error-unknown_device"
                logger.warning(f"Unknown device function: {function[0]}")
    return result_string

def read_function_call(state:State):
    try:
        line:str = state.transport.serial.readline().decode('utf-8').strip()
        if line.strip() == "":
            return ""
        if func_call := re.match(r"^;(.+?);$", line.strip()):
            func_call = func_call.group(1).strip()
            logger.info(f"Read function call: {func_call}")
        else:
            logger.print(f"{line.strip()}")
            func_call = None
            
    except serial.serialutil.SerialException as e:
        if "ClearCommError" in str(e):
            if not work_event.is_set():
                logger.warning("Serial port ClearCommError, exiting.")
                sys.exit(0)
        else:
            logger.error("Unknown SerialException reading function call: %s", e)
            return ""
    except (TypeError,OSError) as e:
        logger.warning("TypeError/OSError reading function call: %s", e)
        return ""
    except Exception as e:
        logger.error("Error reading function call: %s", e)
        return ""
    
    return func_call

def run_function(func_call:str):
    result_string = ""
    if not func_call=="" and func_call.isprintable():
        if "devices" in func_call:
            # devics.
            try:
                result_string = handle_device_function_call(func_call)
            except Exception as e:
                logger.error(f"Error processing device function call '{func_call}': {e}")
                result_string = "error-unknown"
        else:
            # raspi_functions.
            try:
                logger.info(f"Evaluating function call: {func_call}")
                result_string = eval(func_call)
            except(NameError, AttributeError)as e:
                rgbLED.blink("blue", duration=0.3, count=2)
                logger.warning(f"NameError/AttributeError in function call '{func_call}': {e}")
                result_string = ""
            except Exception as e:
                logger.error(f"Exception in function call '{func_call}': {e}")
                result_string = ""
    return result_string

def worker():
    try:
        logger.info("Entering raw REPL.")
        state.transport.enter_raw_repl()
    except transport.TransportError as e:
        # Blink blue 2 times
        rgbLED.blink(on_time=0.1, off_time=0.1, n=2, on_color=(0,0,1), off_color=(0,0,0), background=False)
        logger.critical(f"Error entering raw REPL: {e}")
        sys.exit(1)
    try:
        logger.info("Executing robot_code.py on device.")
        state.transport.exec_raw_no_follow(code)
    except transport.TransportError as e:
        # Blink blue 5 times
        rgbLED.blink(on_time=0.1, off_time=0.1, n=5, on_color=(0,0,1), off_color=(0,0,0), background=False)
        logger.critical(f"Error executing code: {e}")
        sys.exit(1)

    # Blink green 2 times (background)
    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,0), off_color=(0,0,0), background=True)
    logger.info("Code execution started. Awaiting function calls.")
    
    while work_event.is_set():
        sleep(0.05)
        
        func_call = read_function_call(state)
        
        if func_call is None:
            continue
        
        if func_call == "exit":
            logger.info("Exit command received, stopping worker thread.")
            break
        
        # Run the function call and send the result
        result_string = run_function(func_call)
        print(f"Result: {result_string}")
        try:
            state.transport.serial.write(f"{result_string}\n".encode())
            # ack = state.transport.read_until(1,result_string.encode()) # clean up the acknowledgment
            # print(f"Ack: {ack}")
        except (serial.serialutil.SerialException, OSError) as e:
            logger.error(f"Error writing result to serial: {e}")
            
    logger.info("Code stopped/finished.")
    work_event.clear()
    # Blink green 2 times
    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,0), off_color=(0,0,0), background=False)

def main():
    try:
        rgbLED.color = (0,1,0)  # green
        logger.info("System ready. Waiting for button press.")
        while True:
            if button.is_pressed:
                if work_event.is_set():
                    logger.info("Button pressed, stopping work...")
                    # Stop the robot
                    work_event.clear()
                    stop(state)
                    # Blink red 3 times
                    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(1,0,0), off_color=(0,0,0), background=False)
                    sleep(0.2)
                    rgbLED.color = (0,1,0)  # green
                else:
                    # Reload the code and raspi_functions module
                    with open(ROBOT_CODE,"r") as f:
                        new_code = f.read()
                        if new_code != code:
                            logger.info("Reloaded robot_code.py")
                            # Blink cyan 3 times (background)
                            rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,1), off_color=(0,0,0), background=True)
                        code = new_code
                    old_raspi_funcs = len(raspi_functions.__dict__.keys())
                    importlib.reload(raspi_functions)
                    if len(raspi_functions.__dict__.keys()) != old_raspi_funcs:
                        rgbLED.blink(on_time=0.2, off_time=0.2, n=3, on_color=(0,1,1), off_color=(0,0,0), background=True)
                        logger.info("Reloaded raspi_functions module.")
                    
                    # Check the serial connection
                    if not state.transport.serial.is_open:
                        logger.error("Serial port is not open, reconnecting...")
                        commands.do_disconnect(state)
                        commands.do_connect(state)
                    else:
                        state.transport.serial.flushInput()
                        state.transport.serial.flushOutput()

                    # Start the worker thread
                    work_event.set()
                    worker_thread = threading.Thread(target=worker)
                    worker_thread.start()
                    logger.info("Button pressed, starting work...")
                    rgbLED.color = (1,1,0)  # yellow

                sleep(0.2)  # Debounce delay
    except Exception as e:
        logger.exception(f"Error occurred: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, stopping...")
        if work_event.is_set():
            work_event.clear()
            stop(state)
        else:
            logger.info("No work to stop.")
        rgbLED.off()
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()