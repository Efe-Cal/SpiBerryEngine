import threading
from time import sleep
import argparse
import logging
import sys
import serial.serialutil
import importlib

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

from gpiozero import RGBLED, Button

parser = argparse.ArgumentParser(description="SpiBerryEngine GPIO pin configuration")
parser.add_argument('--button', type=int, default=11, help='GPIO pin for button (default: 11)')
parser.add_argument('--red', type=int, default=22, help='GPIO pin for RGBLED red (default: 22)')
parser.add_argument('--green', type=int, default=10, help='GPIO pin for RGBLED green (default: 10)')
parser.add_argument('--blue', type=int, default=9, help='GPIO pin for RGBLED blue (default: 9)')
args = parser.parse_args()

rgbLED = RGBLED(args.red, args.green, args.blue, active_high=False)
button = Button(args.button,pull_up=True)

try:
    from mpremote import commands, transport
    from mpremote.main import State
except ModuleNotFoundError:
    # Blink red 5 times
    rgbLED.blink(on_time=0.1, off_time=0.1, n=5, on_color=(1,0,0), off_color=(0,0,0), background=False)
    logger.critical("mpremote module not found.")
    sys.exit(0)

try:
    import raspi_functions
except ImportError:
    # Blink red 2 times
    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(1,0,0), off_color=(0,0,0), background=False)
    logger.critical("raspi_functions import error.")
    sys.exit(0)

state = State()
try:
    commands.do_connect(state)
    logger.info("Connected to device successfully.")
except (transport.TransportError, commands.CommandError) as e:
    # Blink red 5 times
    rgbLED.blink(on_time=0.3, off_time=0.3, n=5, on_color=(1,0,0), off_color=(0,0,0), background=False)
    logger.critical(f"Error connecting to the device: {e}")
    sys.exit(0)

def stop(state:State):
    logger.info("Stopping and resetting device connection.")
    commands.do_disconnect(state)
    commands.do_connect(state)
    commands.do_soft_reset(state)

with open("robot_code.py","r") as f:
    code = f.read()
    logger.info("Loaded robot_code.py.")

work_event = threading.Event()
worker_thread = None

def read_function_call(state:State):
    try:
        func_call = state.transport.read_until(8, b":",timeout=999)
    except serial.serialutil.SerialException as e:
        if "ClearCommError" in str(e):
            if not work_event.is_set():
                logger.warning("Serial port ClearCommError, exiting.")
                sys.exit(0)
        else:
            logger.error("SerialException reading function call: %s", e)
    except (TypeError,OSError) as e:
        logger.warning("TypeError/OSError reading function call: %s", e)
        return ""
    except Exception as e:
        logger.error("Error reading function call: %s", e)
        return ""
    
    func_call = func_call.decode()[:-1].strip()
    logger.debug(f"Read function call: {func_call}")
    return func_call

def run_function(func_call:str):
    result_string = ""
    if not func_call=="" and func_call.isprintable():
        try:
            logger.info(f"Evaluating function call: {func_call}")
            result_string = eval("raspi_functions."+func_call)
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
        sys.exit(0)
    try:
        logger.info("Executing robot_code.py on device.")
        state.transport.exec_raw_no_follow(code)
    except transport.TransportError as e:
        # Blink blue 5 times
        rgbLED.blink(on_time=0.1, off_time=0.1, n=5, on_color=(0,0,1), off_color=(0,0,0), background=False)
        logger.critical(f"Error executing code: {e}")
        sys.exit(0)

    # Blink green 2 times (background)
    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,0), off_color=(0,0,0), background=True)
    logger.info("Code execution started. Awaiting function calls.")
    
    func_call = read_function_call(state)
    
    while func_call!="exit" and work_event.is_set():
        sleep(0.05)
        logger.info(f"Function call received: {func_call}")
        
        result_string = run_function(func_call)
        
        state.transport.serial.write(f"{result_string}\r\n".encode())
        state.transport.read_until(8,result_string.encode()) # clean up the acknowledgment
        
        func_call = read_function_call(state)
    logger.info("Code stopped/finished.")
    work_event.clear()
    # Blink green 2 times
    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,0), off_color=(0,0,0), background=False)

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
                with open("robot_code.py","r") as f:
                    new_code = f.read()
                    if new_code != code:
                        logger.info("Reloaded robot_code.py")
                        # Blink cyan 3 times (background)
                        rgbLED.blink(on_time=0.2, off_time=0.2, n=3, on_color=(0,1,1), off_color=(0,0,0), background=True)
                    code = new_code
                old_raspi_funcs = len(raspi_functions.__dict__.keys())
                importlib.reload(raspi_functions)
                if len(raspi_functions.__dict__.keys()) != old_raspi_funcs:
                    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,1), off_color=(0,0,0), background=True)
                    logger.info("Reloaded raspi_functions module.")
                
                # Check the serial connection
                state.transport.serial.flushInput()
                state.transport.serial.flushOutput()
                if not state.transport.serial.is_open:
                    logger.warning("Serial port is not open, reconnecting...")
                    commands.do_disconnect(state)
                    commands.do_connect(state)
                
                # Start the worker thread
                work_event.set()
                worker_thread = threading.Thread(target=worker)
                worker_thread.start()
                logger.info("Button pressed, starting work...")
                rgbLED.color = (1,1,0)  # yellow

            sleep(0.3)
except Exception as e:
    logger.exception(f"Error occurred: {e}")
except KeyboardInterrupt:
    logger.info("KeyboardInterrupt received, stopping...")
    if work_event.is_set():
        work_event.clear()
        stop(state)
    else:
        logger.info("No work to stop.")
    rgbLED.off()