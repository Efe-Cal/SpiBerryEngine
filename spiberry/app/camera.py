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
        self.take_picture_method = take_picture_method
        self.camera_config = camera_config or {}
        self._is_started = False
        
        if self.take_picture_method == "picamera2":
            self.picam2 = Picamera2()
            self._configure_picamera2()
        elif self.take_picture_method == "rpicam-still":
            # Validate rpicam-still config is dict-based
            if camera_config and not isinstance(camera_config, dict):
                raise ValueError("camera_config for rpicam-still must be a dictionary of command-line options")
    
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
            # Assume it's a controls dict or partial config
            # Create a still configuration and apply controls
            config = self.picam2.create_still_configuration()
            self.picam2.configure(config)
            # Set controls if they were provided
            if self.camera_config:
                self.picam2.set_controls(self.camera_config)
    
    def _build_rpicam_command(self):
        """Build rpicam-still command with configuration options."""
        cmd = ["rpicam-still", "-o", "captured_image.jpg", "--timeout", "1"]
        
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
        
        for key, value in self.camera_config.items():
            if key in config_mapping:
                option = config_mapping[key]
                if isinstance(value, bool) and value:
                    # Boolean flags (like hflip, vflip)
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
        
        return image
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
