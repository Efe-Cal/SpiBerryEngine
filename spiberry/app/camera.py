import ast
import configparser
import json
from pathlib import Path
import subprocess
from typing import Literal

import cv2

import importlib.util
if importlib.util.find_spec("picamera2") is not None:
    from picamera2 import Picamera2


class Camera:
    def __init__(self, take_picture_method:Literal["picamera2", "rpicam-still"]="picamera2", camera_config=None):
        """
        Initialize camera with specified method and configuration.
        
        Args:
            take_picture_method: Either "picamera2" or "rpicam-still"
            camera_config: Configuration dict with camera settings
                          For picamera2: Can be a full config dict or controls dict
                          For rpicam-still: Dict of command-line options (e.g., {"width": 1920, "height": 1080, "shutter": 10000})
        """
        if camera_config is None:
            camera_config = self._load_engine_camera_config()

        self.camera_config = self._normalize_camera_config(camera_config)
        config_method = self.camera_config.pop("take_picture_method", None)
        if config_method and take_picture_method == "picamera2":
            take_picture_method = config_method
        self.take_picture_method = take_picture_method
        self._is_started = False
        
        if self.take_picture_method == "picamera2":
            self.picam2 = Picamera2()
            self._configure_picamera2()
        elif self.take_picture_method == "rpicam-still":
            pass
        else:
            raise ValueError(f"Unsupported take_picture_method: {self.take_picture_method}")

    @staticmethod
    def _coerce_scalar_value(value):
        if isinstance(value, str):
            text = value.strip()
            lowered = text.lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
            try:
                return int(text)
            except ValueError:
                pass
            try:
                return float(text)
            except ValueError:
                return text
        return value

    @classmethod
    def _load_engine_camera_config(cls):
        config = configparser.ConfigParser()
        config.read(Path.home() / "spiberry_config.ini")

        merged = {}

        # Backward compatible: [Vision] camera = {...}
        if config.has_option("Vision", "camera"):
            raw_camera = config.get("Vision", "camera")
            try:
                merged.update(cls._normalize_camera_config(raw_camera))
            except ValueError:
                pass

        # Support explicit camera sections for larger/clearer configurations.
        for section in ("Camera", "Vision.Camera"):
            if config.has_section(section):
                for key, value in config.items(section):
                    merged[key] = value

        # Also allow [Vision] camera_* keys (e.g. camera_timeout = 1000)
        if config.has_section("Vision"):
            for key, value in config.items("Vision"):
                if key.startswith("camera_"):
                    merged[key.removeprefix("camera_")] = value

        return merged

    @classmethod
    def _normalize_camera_config(cls, camera_config):
        if camera_config is None:
            return {}

        parsed_config = camera_config
        if isinstance(camera_config, str):
            text = camera_config.strip()
            if text == "":
                return {}

            parse_error = None
            for parser in (json.loads, ast.literal_eval):
                try:
                    parsed_config = parser(text)
                    break
                except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                    parse_error = e
            else:
                raise ValueError(f"camera_config string is not a valid dict: {parse_error}")

        if not isinstance(parsed_config, dict):
            raise ValueError("camera_config must be a dictionary or a dictionary-like string")

        normalized = {}
        for key, value in parsed_config.items():
            key = str(key)
            if isinstance(value, dict):
                normalized[key] = {
                    str(sub_key): cls._coerce_scalar_value(sub_value)
                    for sub_key, sub_value in value.items()
                }
            elif isinstance(value, (list, tuple)):
                normalized[key] = [cls._coerce_scalar_value(item) for item in value]
            else:
                normalized[key] = cls._coerce_scalar_value(value)

        return normalized
    
    def _configure_picamera2(self):
        """Configure picamera2 with the provided configuration."""
        if not self.camera_config:
            # Use default still configuration if no config provided
            config = self.picam2.create_still_configuration()
            self.picam2.configure(config)
        elif "main" in self.camera_config or "raw" in self.camera_config:
            # Full configuration dict provided (with streams)
            self.picam2.configure(self.camera_config)
        else:
            # Allow width/height as top-level keys in simplified config.
            width = self.camera_config.get("width")
            height = self.camera_config.get("height")
            if isinstance(width, int) and isinstance(height, int):
                config = self.picam2.create_still_configuration(main={"size": (width, height)})
            else:
                config = self.picam2.create_still_configuration()
            self.picam2.configure(config)

            controls = {
                key: value
                for key, value in self.camera_config.items()
                if key not in {"width", "height", "timeout"}
            }
            if controls:
                self.picam2.set_controls(controls)
    
    def _build_rpicam_command(self):
        """Build rpicam-still command with configuration options."""
        timeout = self.camera_config.get("timeout", 1)
        cmd = ["rpicam-still", "-o", "captured_image.jpg", "--timeout", str(timeout)]
        
        # Map common configuration options to rpicam-still arguments
        config_mapping = {
            "width": "--width",
            "height": "--height",
            "shutter": "--shutter",
            "gain": "--gain",
            "analoggain": "--analoggain",
            "brightness": "--brightness",
            "contrast": "--contrast",
            "saturation": "--saturation",
            "sharpness": "--sharpness",
            "awb": "--awb",
            "awbgains": "--awbgains",
            "denoise": "--denoise",
            "exposure": "--exposure",
            "ev": "--ev",
            "metering": "--metering",
            "hflip": "--hflip",
            "vflip": "--vflip",
            "rotation": "--rotation",
            "quality": "--quality",
            "encoding": "--encoding",
            "timeout": "--timeout",
        }

        flag_options = {"hflip", "vflip"}
        
        for key, value in self.camera_config.items():
            if key == "timeout":
                continue

            option = config_mapping.get(key, f"--{str(key).replace('_', '-')}")

            if key in flag_options:
                if bool(value):
                    cmd.append(option)
            elif isinstance(value, (list, tuple)):
                # For options like awbgains that take comma-separated values
                cmd.extend([option, ",".join(map(str, value))])
            elif value is not None:
                # Regular options with values
                cmd.extend([option, str(value)])
        
        return cmd
        
    def start(self):
        """Start the camera (for picamera2)."""
        if self.take_picture_method == "picamera2" and not self._is_started:
            self.picam2.start()
            self._is_started = True
    
    def stop(self):
        """Stop the camera (for picamera2)."""
        if self.take_picture_method == "picamera2" and self._is_started:
            self.picam2.stop()
            self._is_started = False
    
    def take_picture(self):
        """Capture an image using the configured method."""
        if self.take_picture_method == "rpicam-still":
            cmd = self._build_rpicam_command()
            subprocess.run(cmd)
            image = cv2.imread("captured_image.jpg")

        elif self.take_picture_method == "picamera2":
            # Start camera if not already started
            was_started = self._is_started
            if not was_started:
                self.start()
            
            # Capture the image
            image = self.picam2.capture_array()
            
            # Stop camera if we started it (maintain previous state)
            if not was_started:
                self.stop()
        
        else:
            raise ValueError(f"Unsupported take_picture_method: {self.take_picture_method}")
        
        return image
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
