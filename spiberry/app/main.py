import os
from pathlib import Path
import sys
import re
import ast
import json
import logging
import threading
import importlib
import importlib.util
from time import sleep

import gpiozero
from gpiozero import RGBLED, Button

import serial.serialutil

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from mpremote import commands, transport
from mpremote.main import State

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

from spiberry.app.config import config, create_default_config, RASPI_FUNCTIONS_MODULE_FILE, ROBOT_CODE

create_default_config()

starter_pin = Button(config.getint("GPIO", "starter", fallback=21), pull_up=True)
if not starter_pin.is_pressed and os.getenv("IGNORE_STARTER_PIN","0") == "0":
    logger.critical("Starter pin not connected to ground. Please connect pin %s to ground to start the program.", config.get("GPIO", "starter", fallback="21"))
    sys.exit(1)

class RGBLEDWrapper(RGBLED):
    def __init__(self, *args, **kwargs):
        self._enabled_in_hardware = False
        try:
            super().__init__(*args, **kwargs)
            self._enabled_in_hardware = True
        except (gpiozero.exc.GPIOPinMissing, gpiozero.exc.GPIOZeroError) as e:
            logger.warning("RGB LED not initialized: %s", e)

    def _is_allowed(self):
        return self._enabled_in_hardware and config.getboolean("GPIO", "rgb_led_enabled", fallback=True)

    def blink(self, *args, **kwargs):
        if self._is_allowed():
            super().blink(*args, **kwargs)

    def on(self):
        if self._is_allowed():
            super().on()

    def off(self):
        if self._is_allowed():
            super().off()

    @RGBLED.color.setter
    def color(self, value):
        if self._is_allowed():
            RGBLED.color.fset(self, value)

rgbLED = RGBLEDWrapper(config.getint("GPIO", "red", fallback=None), config.getint("GPIO", "green", fallback=None), config.getint("GPIO", "blue", fallback=None), active_high=config.getboolean("GPIO", "active_high", fallback=False))
button = Button(config.getint("GPIO", "button"), pull_up=True)

# Device constructor map - maps device type to constructor function
# Each entry: (min_params, constructor_lambda)
DEVICE_CONSTRUCTORS = {
    "distance_sensor": (3, lambda params: gpiozero.DistanceSensor(
        echo=int(params[0]),
        trigger=int(params[1]),
        max_distance=float(params[2]),
    )),
    "servo": (1, lambda params: (
        gpiozero.AngularServo(int(params[0])) 
        if len(params) == 1 
        else gpiozero.AngularServo(
            int(params[0]),
            min_angle=int(params[1]),
            max_angle=int(params[2]),
            min_pulse_width=float(params[3]),
            max_pulse_width=float(params[4]),
            initial_angle=int(params[5]),
        )
    )),
}

def _load_raspi_functions_module(module_file: Path):
    module_file.parent.mkdir(parents=True, exist_ok=True)
    if not module_file.exists():
        with open(module_file, "w") as f:
            f.write("# Add your Raspberry Pi functions here\n")

    is_package = module_file.name == "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "raspi_functions",
        str(module_file),
        submodule_search_locations=[str(module_file.parent)] if is_package else None,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {module_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["raspi_functions"] = module
    spec.loader.exec_module(module)
    return module


raspi_functions = _load_raspi_functions_module(RASPI_FUNCTIONS_MODULE_FILE)
logger.info("Loaded raspi_functions from %s", RASPI_FUNCTIONS_MODULE_FILE)

if config.getboolean("Vision", "enabled"):
    import spiberry.app.vision as vision
    logger.info("Vision module loaded.")


class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.last_code = controller.code

    def on_modified(self, event):
        if event.src_path.endswith(self.controller.robot_code_path):
            with open(self.controller.robot_code_path, "r") as f:
                new_code = f.read()
                if new_code != self.last_code:
                    logger.info("Hot reloaded robot_code.py")
                    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,1), off_color=(0,0,0), background=False)
                    self.controller.code = new_code
                    self.last_code = new_code
                    
        else:
            try:
                if Path(event.src_path).resolve() == RASPI_FUNCTIONS_MODULE_FILE:
                    importlib.reload(raspi_functions)
                    logger.info("Hot reloaded raspi_functions module.")
                    rgbLED.blink(on_time=0.2, off_time=0.2, n=3, on_color=(0,1,1), off_color=(0,0,0), background=False)
            except OSError:
                logger.debug("Skipping unresolved modified path: %s", event.src_path)

class Controller:
    def __init__(self, robot_code_path=ROBOT_CODE):
        self.devices = {}
        self.code = ""
        self.robot_code_path = robot_code_path if robot_code_path else ROBOT_CODE
        self.vision_camera = None
        self.vision_model = None
        self.vision_contour = None
        self.vision_cache = {
            "latest_image": None,
            "latest_detections": None,
            "latest_center_points": None,
            "latest_contours": None,
        }

        self.observer = Observer()
        self.event_handler = HotReloadHandler(self)
        self.observer.schedule(self.event_handler, ".", recursive=False)
        self.observer.start()

        self.init_mp_device()

        self.work_event = threading.Event()
        self.worker_thread = None

    
    def init_mp_device(self):
        self.state = State()

        try:
            commands.do_connect(self.state)
            logger.info("Connected to device successfully.")
        except (transport.TransportError, commands.CommandError) as e:
            # Blink red 5 times
            rgbLED.blink(on_time=0.3, off_time=0.3, n=5, on_color=(1,0,0), off_color=(0,0,0), background=False)
            logger.critical(f"Error connecting to the device: {e}")
            sys.exit(1)

    def stop(self, state:State):
        logger.info("Stopping and resetting device connection.")
        commands.do_disconnect(state)
        commands.do_connect(state)
        sleep(0.1)
        commands.do_soft_reset(state)
        del self.devices
        self.devices = {}

    def handle_device_function_call(self, func_call:str=None, parsed=None):
        parsed_or_error = self._resolve_and_validate_call(
            func_call,
            parsed,
            namespace="devices",
            error_code="error-invalid_device_function_format",
            warn_label="device",
        )
        if isinstance(parsed_or_error, str):
            return parsed_or_error
        path, args_list, kwargs = parsed_or_error

        # devices.register(device_type, device_name, ...)
        if len(path) == 2 and path[1] == "register":
            if len(args_list) < 2:
                return self._result_payload("error", code="error-invalid_args", message="register requires device_type and device_name")

            device_type = str(args_list[0])
            device_name = str(args_list[1])
            params = args_list[2:]

            if device_type not in DEVICE_CONSTRUCTORS:
                return self._result_payload("error", code="error-unsupported_device", device_type=device_type)

            required_min, constructor = DEVICE_CONSTRUCTORS[device_type]
            
            # Handle special parameter requirements
            if device_type == "distance_sensor" and len(params) < required_min:
                return self._result_payload("error", code="error-invalid_args", message="distance_sensor requires echo, trigger, max_distance")
            if device_type == "servo" and len(params) not in (1, 6):
                return self._result_payload("error", code="error-invalid_args", message="servo requires pin or full config")

            try:
                self.devices[device_name] = constructor(params)
            except Exception as e:
                logger.error("Device registration failed for %s: %s", device_name, e)
                return self._result_payload("error", code="error-device_register_failed", message=str(e))

            return self._result_payload("ok", action="devices.register", device_type=device_type, device_name=device_name)

        # devices.<device_name>.<method>(...)
        if len(path) == 3:
            device_name = path[1]
            method = path[2]

            if device_name not in self.devices:
                return self._result_payload("error", code="error-unknown_device", device_name=device_name)

            device = self.devices[device_name]
            if method == "get_distance":
                value = float(device.distance * 100)
                return self._result_payload("ok", action="devices.get_distance", device_name=device_name, value=value)
            if method == "get_angle":
                value = device.angle
                return self._result_payload("ok", action="devices.get_angle", device_name=device_name, value=value)
            if method == "set_angle":
                angle = kwargs.get("angle", args_list[0] if args_list else None)
                if angle is None:
                    return self._result_payload("error", code="error-invalid_args", message="set_angle requires angle")
                device.angle = int(angle)
                return self._result_payload("ok", action="devices.set_angle", device_name=device_name, value=int(angle))

            return self._result_payload("error", code="error-unknown_device_method", target=f"{device_name}.{method}")

        return self._result_payload("error", code="error-invalid_device_function_format")

    def read_function_call(self, state:State):
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
                if not self.work_event.is_set():
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

    def _parse_ast_value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp):
            # Allow signed numeric literals like -30 or +5 in call args.
            return ast.literal_eval(node)
        if isinstance(node, ast.Name):
            # Keep compatibility with existing protocol where bare tokens are sent.
            return node.id
        if isinstance(node, (ast.List, ast.Tuple, ast.Dict)):
            return ast.literal_eval(node)
        raise ValueError("Unsupported argument type")

    def _parse_structured_call(self, func_call: str):
        parsed = ast.parse(func_call, mode="eval")
        if not isinstance(parsed.body, ast.Call):
            raise ValueError("Function call expected")

        call_node = parsed.body
        func_node = call_node.func
        path = []
        while isinstance(func_node, ast.Attribute):
            path.insert(0, func_node.attr)
            func_node = func_node.value
        if isinstance(func_node, ast.Name):
            path.insert(0, func_node.id)
        else:
            raise ValueError("Invalid function path")

        args = [self._parse_ast_value(a) for a in call_node.args]
        kwargs = {}
        for kw in call_node.keywords:
            if kw.arg is None:
                raise ValueError("Star-args are not supported")
            kwargs[kw.arg] = self._parse_ast_value(kw.value)
        return path, args, kwargs

    def _resolve_and_validate_call(self, func_call, parsed, namespace, error_code, warn_label):
        if parsed is None:
            try:
                parsed = self._parse_structured_call(func_call)
            except Exception as e:
                logger.warning("Invalid %s function call format '%s': %s", warn_label, func_call, e)
                return self._result_payload("error", code=error_code)

        path, args_list, kwargs = parsed
        if len(path) < 2 or path[0] != namespace:
            return self._result_payload("error", code=error_code)
        return path, args_list, kwargs

    @staticmethod
    def _arg(args_list, kwargs, key, idx, default=None):
        if key in kwargs:
            return kwargs[key]
        if idx is not None and len(args_list) > idx:
            return args_list[idx]
        return default

    def _require_cached_image(self):
        image = self.vision_cache["latest_image"]
        if image is None:
            return None, self._result_payload("error", code="error-missing_cached_image")
        return image, None

    @staticmethod
    def _result_payload(status: str = "ok", **data):
        payload = {"status": status}
        payload.update(data)
        return json.dumps(payload)

    @staticmethod
    def _json_safe(value):
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, (list, tuple)):
            return [Controller._json_safe(v) for v in value]
        if isinstance(value, dict):
            return {str(k): Controller._json_safe(v) for k, v in value.items()}
        return str(value)

    def _dispatch_raspi_function_call(self, path, args_list, kwargs):
        if len(path) < 2 or path[0] != "raspi_functions":
            return self._result_payload("error", code="error-invalid_raspi_function_format")

        target = raspi_functions
        for attr in path[1:]:
            if not hasattr(target, attr):
                return self._result_payload("error", code="error-unknown_raspi_function", target=".".join(path[1:]))
            target = getattr(target, attr)

        if not callable(target):
            return self._result_payload("error", code="error-rpi_target_not_callable", target=".".join(path[1:]))

        try:
            result = target(*args_list, **kwargs)
        except Exception as e:
            logger.error("Exception in raspi function call '%s': %s", ".".join(path), e)
            return self._result_payload("error", code="error-raspi_function_exception", message=str(e))

        return self._result_payload(
            "ok",
            action=f"raspi_functions.{'.'.join(path[1:])}",
            result=self._json_safe(result),
        )

    def _initialize_vision_runtime(self, args_list, kwargs):
        if not config.getboolean("Vision", "enabled"):
            return self._result_payload("error", code="error-vision_module_disabled")

        # Positional compatibility:
        # vision.initialize(take_picture_method, camera_config, model_path)
        take_picture_method = kwargs.get("take_picture_method", "picamera2")
        camera_config = kwargs.get("camera_config", None)
        model_path = kwargs.get("model_path", "yolo26n.pt")

        if len(args_list) > 0:
            take_picture_method = args_list[0]
        if len(args_list) > 1:
            camera_config = args_list[1]
        if len(args_list) > 2:
            model_path = args_list[2]

        try:
            camera = vision.Camera(take_picture_method=take_picture_method, camera_config=camera_config)
            vision_model = vision.Vision(model_path=model_path, camera=camera)
            contour = vision.ContourDetector(config_path=config.get("Vision", "vision_config_path", fallback=None), camera=camera)
        except Exception as e:
            logger.error("Vision initialization failed: %s", e)
            return self._result_payload("error", code="error-vision_initialize_failed", message=str(e))

        self.vision_camera = camera
        self.vision_model = vision_model
        self.vision_contour = contour
        self.vision_cache = {
            "latest_image": None,
            "latest_detections": None,
            "latest_center_points": None,
            "latest_contours": None,
        }

        return self._result_payload(
            "ok",
            action="initialize",
            take_picture_method=take_picture_method,
            model_path=model_path,
        )

    def _dispatch_camera_call(self, method: str, args_list, kwargs):
        if self.vision_camera is None:
            return self._result_payload("error", code="error-vision_not_initialized")

        if method == "start":
            self.vision_camera.start()
            return self._result_payload("ok", action="Camera.start")
        if method == "stop":
            self.vision_camera.stop()
            return self._result_payload("ok", action="Camera.stop")
        if method == "take_picture":
            image = self.vision_camera.take_picture()
            if image is None:
                return self._result_payload("error", code="error-camera_capture_failed")
            self.vision_cache["latest_image"] = image
            return self._result_payload(
                "ok",
                action="Camera.take_picture",
                shape=list(image.shape),
            )
        return self._result_payload("error", code="error-unknown_vision_method", target=f"Camera.{method}")

    def _dispatch_vision_call(self, method: str, args_list, kwargs):
        if self.vision_model is None:
            return self._result_payload("error", code="error-vision_not_initialized")

        if method == "load_model":
            model_name = self._arg(args_list, kwargs, "model", 0)
            if not isinstance(model_name, str) or model_name == "":
                return self._result_payload("error", code="error-invalid_args", message="load_model requires model path")
            self.vision_model.load_model(model_name)
            return self._result_payload("ok", action="Vision.load_model", model=model_name)

        if method == "find_objects":
            model_name = self._arg(args_list, kwargs, "model_name", 0)
            if not isinstance(model_name, str) or model_name == "":
                return self._result_payload("error", code="error-invalid_args", message="find_objects requires model_name")
            detections, center_points = self.vision_model.find_objects(model_name)
            self.vision_cache["latest_detections"] = detections
            self.vision_cache["latest_center_points"] = center_points
            return self._result_payload(
                "ok",
                action="Vision.find_objects",
                detections_count=len(detections),
                center_points_count=len(center_points),
            )

        if method == "detect_objects_from_image":
            model_name = self._arg(args_list, kwargs, "model_name", 0)
            image, error_payload = self._require_cached_image()
            if error_payload:
                return error_payload
            if not isinstance(model_name, str) or model_name == "":
                return self._result_payload("error", code="error-invalid_args", message="detect_objects_from_image requires model_name")
            detections = self.vision_model.detect_objects_from_image(image, model_name)
            self.vision_cache["latest_detections"] = detections
            return self._result_payload(
                "ok",
                action="Vision.detect_objects_from_image",
                detections_count=len(detections),
            )

        return self._result_payload("error", code="error-unknown_vision_method", target=f"Vision.{method}")

    def _dispatch_contour_call(self, method: str, args_list, kwargs):
        if self.vision_contour is None:
            return self._result_payload("error", code="error-vision_not_initialized")

        if method == "detect_contours":
            image, error_payload = self._require_cached_image()
            if error_payload:
                return error_payload

            filters = kwargs.get("filters")
            if filters is None and args_list:
                filters = args_list[0] if isinstance(args_list[0], dict) else None
            if filters is None:
                filter_keys = ("min_area", "max_area", "color", "n", "vertices")
                if any(k in kwargs for k in filter_keys):
                    filters = {k: kwargs[k] for k in filter_keys if k in kwargs}

            contours = self.vision_contour.detect_contours(image, filters=filters)
            self.vision_cache["latest_contours"] = contours
            return self._result_payload(
                "ok",
                action="ContourDetector.detect_contours",
                detections_count=0 if contours is None else len(contours),
            )

        if method == "crop_image":
            image, error_payload = self._require_cached_image()
            if error_payload:
                return error_payload

            x = self._arg(args_list, kwargs, "x", 0)
            y = self._arg(args_list, kwargs, "y", 1)
            w = self._arg(args_list, kwargs, "w", 2)
            h = self._arg(args_list, kwargs, "h", 3)

            if None in (x, y, w, h):
                return self._result_payload("error", code="error-invalid_args", message="crop_image requires x, y, w, h")

            cropped = self.vision_contour.crop_image(image, int(x), int(y), int(w), int(h))
            self.vision_cache["latest_image"] = cropped
            return self._result_payload("ok", action="ContourDetector.crop_image", shape=list(cropped.shape))

        if method == "extend_color_range":
            color_range = self._arg(args_list, kwargs, "color_range", 0)
            offset = self._arg(args_list, kwargs, "offset", 1)
            if color_range is None:
                return self._result_payload("error", code="error-invalid_args", message="extend_color_range requires color_range")
            extended = self.vision_contour.extend_color_range(color_range, offset=offset)
            return self._result_payload("ok", action="ContourDetector.extend_color_range", ranges=extended)

        if method == "extend_all_color_ranges":
            color_ranges = self._arg(args_list, kwargs, "color_ranges", 0)
            offset = self._arg(args_list, kwargs, "offset", 1)
            if color_ranges is None:
                return self._result_payload("error", code="error-invalid_args", message="extend_all_color_ranges requires color_ranges")
            extended = self.vision_contour.extend_all_color_ranges(color_ranges, offset=offset)
            return self._result_payload("ok", action="ContourDetector.extend_all_color_ranges", color_ranges=extended)

        if method == "load_config":
            vis_config = self.vision_contour.load_config(config_path=config.get("Vision", "vision_config_path", fallback=None))
            self.vision_contour.config = vis_config
            return self._result_payload("ok", action="ContourDetector.load_config")

        return self._result_payload("error", code="error-unknown_vision_method", target=f"ContourDetector.{method}")

    def handle_vision_function_call(self, func_call:str=None, parsed=None):
        parsed_or_error = self._resolve_and_validate_call(
            func_call,
            parsed,
            namespace="vision",
            error_code="error-invalid_vision_function_format",
            warn_label="vision",
        )
        if isinstance(parsed_or_error, str):
            return parsed_or_error
        path, args_list, kwargs = parsed_or_error

        if len(path) == 2 and path[1] == "initialize":
            return self._initialize_vision_runtime(args_list, kwargs)

        if len(path) != 3:
            return self._result_payload("error", code="error-invalid_vision_function_format")

        class_name, method_name = path[1], path[2]
        if class_name == "Camera":
            return self._dispatch_camera_call(method_name, args_list, kwargs)
        if class_name == "Vision":
            return self._dispatch_vision_call(method_name, args_list, kwargs)
        if class_name == "ContourDetector":
            return self._dispatch_contour_call(method_name, args_list, kwargs)

        return self._result_payload("error", code="error-unknown_vision_class", target=class_name)

    def run_function(self, func_call:str):
        result_string = ""
        if func_call == "" or not func_call.isprintable():
            return result_string

        try:
            path, args_list, kwargs = self._parse_structured_call(func_call)
        except Exception as e:
            logger.warning("Invalid function call '%s': %s", func_call, e)
            return self._result_payload("error", code="error-invalid_function_call_format")

        root = path[0] if path else None

        if root == "devices":
            try:
                return self.handle_device_function_call(parsed=(path, args_list, kwargs))
            except Exception as e:
                logger.error("Error processing device function call '%s': %s", func_call, e)
                return self._result_payload("error", code="error-device_dispatch_failure", message=str(e))

        if root == "vision":
            if not config.getboolean("Vision", "enabled"):
                return self._result_payload("error", code="error-vision_module_disabled")
            try:
                return self.handle_vision_function_call(parsed=(path, args_list, kwargs))
            except Exception as e:
                logger.error("Error processing vision function call '%s': %s", func_call, e)
                return self._result_payload("error", code="error-vision_dispatch_failure", message=str(e))

        if root == "raspi_functions":
            try:            
                return self._dispatch_raspi_function_call(path, args_list, kwargs)
            except Exception as e:
                logger.error("Error processing raspi function call '%s': %s", func_call, e)
                return self._result_payload("error", code="error-raspi_dispatch_failure", message=str(e))

        return self._result_payload("error", code="error-unknown_call_namespace", target=str(root))

    def run_code(self):
        with open(self.robot_code_path, "r") as f:
            self.code = f.read()
            logger.info("Loaded robot code.")
        try:
            logger.info("Entering raw REPL.")
            self.state.transport.enter_raw_repl()
        except transport.TransportError as e:
            # Blink blue 2 times
            rgbLED.blink(on_time=0.1, off_time=0.1, n=2, on_color=(0,0,1), off_color=(0,0,0), background=False)
            logger.critical(f"Error entering raw REPL: {e}")
            sys.exit(1)
        try:
            logger.info("Executing robot code on device.")
            self.state.transport.exec_raw_no_follow(self.code)
        except transport.TransportError as e:
            # Blink blue 5 times
            rgbLED.blink(on_time=0.1, off_time=0.1, n=5, on_color=(0,0,1), off_color=(0,0,0), background=False)
            logger.critical(f"Error executing code: {e}")
            sys.exit(1)

        # Blink green 2 times (background)
        rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,0), off_color=(0,0,0), background=True)
        logger.info("Code execution started. Awaiting function calls.")

    def worker(self):
        if config.get("Code", "trigger_mode", fallback="external") == "external":
            self.run_code()
        
        while self.work_event.is_set():
            sleep(0.05)
            
            func_call = self.read_function_call(self.state)
            
            if func_call is None:
                continue
            
            if func_call == "exit":
                logger.info("Exit command received, stopping worker thread.")
                break
            
            # Run the function call and send the result
            result_string = self.run_function(func_call)
            print(f"Result: {result_string}")
            try:
                self.state.transport.serial.write(f"{result_string}\n".encode())
                # ack = self.state.transport.read_until(1,result_string.encode()) # clean up the acknowledgment
                # print(f"Ack: {ack}")
            except (serial.serialutil.SerialException, OSError) as e:
                logger.error(f"Error writing result to serial: {e}")
                
        logger.info("Code stopped/finished.")
        self.work_event.clear()
        # Blink green 2 times
        rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,0), off_color=(0,0,0), background=False)

    def main(self):
        try:
            rgbLED.color = (0,1,0)  # green
            logger.info("System ready. Waiting for button press.")
            
            if config.get("Code", "trigger_mode", fallback="external") != "external":
                self.work_event.set()
                worker_thread = threading.Thread(target=self.worker)
                worker_thread.start()
                logger.info("Built-in button is used. Starting worker thread in internal mode.")
            else:
                while True:
                    if button.is_pressed:
                        if self.work_event.is_set():
                            logger.info("Button pressed, stopping work...")
                            # Stop the robot
                            self.work_event.clear()
                            self.stop(self.state)
                            # Blink red 3 times
                            rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(1,0,0), off_color=(0,0,0), background=False)
                            sleep(0.2)
                            rgbLED.color = (0,1,0)  # green
                        else:
                            # Reload the code and raspi_functions module
                            with open(ROBOT_CODE,"r") as f:
                                new_code = f.read()
                                if new_code != self.code:
                                    logger.info("Reloaded robot_code.py")
                                    # Blink cyan 3 times (background)
                                    rgbLED.blink(on_time=0.2, off_time=0.2, n=2, on_color=(0,1,1), off_color=(0,0,0), background=True)
                                self.code = new_code
                            old_raspi_funcs = len(raspi_functions.__dict__.keys())
                            importlib.reload(raspi_functions)
                            if len(raspi_functions.__dict__.keys()) != old_raspi_funcs:
                                rgbLED.blink(on_time=0.2, off_time=0.2, n=3, on_color=(0,1,1), off_color=(0,0,0), background=True)
                                logger.info("Reloaded raspi_functions module.")
                            
                            # Check the serial connection
                            if not self.state.transport.serial.is_open:
                                logger.error("Serial port is not open, reconnecting...")
                                commands.do_disconnect(self.state)
                                commands.do_connect(self.state)
                            else:
                                self.state.transport.serial.flushInput()
                                self.state.transport.serial.flushOutput()

                            # Start the worker thread
                            self.work_event.set()
                            worker_thread = threading.Thread(target=self.worker)
                            worker_thread.start()
                            logger.info("Button pressed, starting work...")
                            rgbLED.color = (1,1,0)  # yellow

                        sleep(0.2)  # Debounce delay
        except Exception as e:
            logger.exception(f"Error occurred: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, stopping...")
            if self.work_event.is_set():
                self.work_event.clear()
                self.stop(self.state)
            else:
                logger.info("No work to stop.")
            rgbLED.off()
        finally:
            self.observer.stop()
            self.observer.join()

if __name__ == "__main__":
    controller = Controller()
    controller.main()