import sys
import time
import select

try:
    import ujson  # type: ignore[import-not-found]
except ImportError:
    import json as ujson


def input_with_timeout(prompt, timeout):
    def _now_ms():
        if hasattr(time, "ticks_ms"):
            return time.ticks_ms()
        return int(time.time() * 1000)

    def _diff_ms(now, start):
        if hasattr(time, "ticks_diff"):
            return time.ticks_diff(now, start)
        return now - start

    sys.stdout.write(prompt)
    sys.stdout.flush()

    timeout_ms = int(timeout * 1000)
    start = _now_ms()
    
    if select is not None:
        try:
            while True:
                elapsed = _diff_ms(_now_ms(), start)
                remaining = (timeout_ms - elapsed) // 1000
                if remaining <= 0:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    sys.stdout.flush()
                    return None

                rlist, _, _ = select.select([sys.stdin], [], [], remaining)
                if rlist:
                    data = sys.stdin.readline()
                    if not data:
                        sys.stdout.write("\n")
                        return None
                    return data.rstrip('\n').rstrip('\r')
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            return None

    try:
        start_block = _now_ms()
        s = input()
        elapsed = _diff_ms(_now_ms(), start_block)
        if elapsed >= timeout_ms:
            sys.stdout.write("\n")
            return None
        return s
    except Exception:
        return None


class Device:
    def __init__(self, device_type, device_name, *args):
        self.device_type = device_type
        self.device_name = device_name
        self.args = args

class Servo(Device):
    def get_angle(self, timeout=1):
        print(f";devices.{self.device_name}.get_angle();")
        return _extract_value(sys.stdin.readline().strip())

    def set_angle(self, angle, timeout=2):
        print(f";devices.{self.device_name}.set_angle({angle});")
        return _read_payload(sys.stdin.readline().strip())


class DistanceSensor(Device):
    def get_distance(self, timeout=1):
        print(f";devices.{self.device_name}.get_distance();")
        return _extract_value(sys.stdin.readline().strip())


def _read_payload(raw_line):
    raw_line = raw_line.strip()
    try:
        return ujson.loads(raw_line)
    except Exception:
        return {"status": "error", "code": "error-invalid_json_response", "raw": raw_line}


def _extract_value(raw_line):
    payload = _read_payload(raw_line)
    if payload.get("status") == "ok" and "value" in payload:
        return payload["value"]
    return payload


def _lit(value):
    if isinstance(value, str):
        return ujson.dumps(value)
    if isinstance(value, (dict, list, tuple, bool)) or value is None:
        return ujson.dumps(value)
    return str(value)


def _call(expr):
    print(f";{expr};")
    return _read_payload(sys.stdin.readline().strip())


class Raspi:
    def register_device(self, device_type, device_name, *args, timeout=1):
        parts = [_lit(arg) for arg in args]
        call_args = ", ".join(parts)
        print(f";devices.register({device_type}, {device_name}, {call_args});")
        payload = _read_payload(sys.stdin.readline().strip())

        if payload.get("status") != "ok":
            raise RuntimeError(f"Device registration failed: {payload}")

        if device_type == "servo":
            return Servo(device_type, device_name, *args)
        elif device_type == "distance_sensor":
            return DistanceSensor(device_type, device_name, *args)
        else:
            raise ValueError(f"Unsupported device type: {device_type}")

    def _invoke_raspi_function(self, func_name, *args, **kwargs):
        parts = [_lit(arg) for arg in args]
        parts.extend([f"{key}={_lit(value)}" for key, value in kwargs.items()])
        call_args = ", ".join(parts)
        payload = _call(f"raspi_functions.{func_name}({call_args})")
        if payload.get("status") == "ok":
            return payload.get("result")
        return payload

    def __getattr__(self, name):
        def _dynamic_func(*args, **kwargs):
            return self._invoke_raspi_function(name, *args, **kwargs)

        return _dynamic_func

    def func(self, func_string):
        payload = _call(f"raspi_functions.{func_string}")
        if payload.get("status") == "ok":
            return payload.get("result")
        return payload


class Vision:
    def initialize(self, take_picture_method="picamera2", camera_config=None, model_path="yolo26n.pt"):
        return _call(
            f"vision.initialize(take_picture_method={_lit(take_picture_method)},"
            f"camera_config={_lit(camera_config)},model_path={_lit(model_path)})"
        )

    def camera_start(self): return _call("vision.Camera.start()")
    def camera_stop(self): return _call("vision.Camera.stop()")
    def take_picture(self): return _call("vision.Camera.take_picture()")

    def load_model(self, model):
        return _call(f"vision.Vision.load_model(model={_lit(model)})")

    def find_objects(self, model_name):
        return _call(f"vision.Vision.find_objects(model_name={_lit(model_name)})")

    def detect_objects_from_image(self, model_name):
        return _call(f"vision.Vision.detect_objects_from_image(model_name={_lit(model_name)})")

    def detect_contours(self, filters=None, **kwargs):
        if filters is not None:
            return _call(f"vision.ContourDetector.detect_contours(filters={_lit(filters)})")
        if kwargs:
            args = ",".join([f"{k}={_lit(v)}" for k, v in kwargs.items()])
            return _call(f"vision.ContourDetector.detect_contours({args})")
        return _call("vision.ContourDetector.detect_contours()")

    def crop_image(self, x, y, w, h):
        return _call(f"vision.ContourDetector.crop_image(x={x},y={y},w={w},h={h})")

    def extend_color_range(self, color_range, offset=None):
        return _call(
            f"vision.ContourDetector.extend_color_range(color_range={_lit(color_range)},offset={_lit(offset)})"
        )

    def extend_all_color_ranges(self, color_ranges, offset=None):
        return _call(
            f"vision.ContourDetector.extend_all_color_ranges(color_ranges={_lit(color_ranges)},offset={_lit(offset)})"
        )

    def load_config(self):
        return _call("vision.ContourDetector.load_config()")


# Example usage
if __name__ == "__main__":
    raspi = Raspi()
    servo = raspi.register_device("servo", "my_servo", "17")
    servo.set_angle(90)
