import sys
import time
import select


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

    def __repr__(self):
        return f"Device(type={self.device_type}, name={self.device_name}, args={self.args})"

class Servo(Device):
    def get_angle(self, timeout=1):
        return input_with_timeout(f";devices.{self.device_name}.get_angle();", timeout=timeout)
    def set_angle(self, angle, timeout=2):
        return input_with_timeout(f";devices.{self.device_name}.set_angle({angle});", timeout=timeout)

class DistanceSensor(Device):
    def get_distance(self, timeout=1):
        return input_with_timeout(f";devices.{self.device_name}.get_distance();", timeout=timeout)

class Raspi:
    def register_device(self, device_type, device_name, *args, timeout=1):
        input_with_timeout(f";devices.register({device_type}, {device_name}, {', '.join(args)});", timeout=timeout)
        if device_type == "servo":
            return Servo(device_type, device_name, *args)
        elif device_type == "distance_sensor":
            return DistanceSensor(device_type, device_name, *args)
        else:
            raise ValueError(f"Unsupported device type: {device_type}")

# Example usage
if __name__ == "__main__":
    raspi = Raspi()
    servo = raspi.register_device("servo", "my_servo", "17")
    servo.set_angle(90)
