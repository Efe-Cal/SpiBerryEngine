"""
Examples of how to configure the Camera class for both picamera2 and rpicam-still methods.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spiberry.app.vision import Camera

# Example 1: picamera2 with default configuration
print("Example 1: picamera2 with default configuration")
camera1 = Camera(take_picture_method="picamera2")
image1 = camera1.take_picture()
print(f"Captured image shape: {image1.shape if image1 is not None else 'None'}")


# Example 2: picamera2 with camera controls
print("\nExample 2: picamera2 with camera controls")
camera_config_controls = {
    "ExposureTime": 20000,  # 20ms exposure
    "AnalogueGain": 2.0,    # 2x analogue gain
    "Brightness": 0.1,      # Slightly brighter
    "Contrast": 1.2,        # Increased contrast
}
camera2 = Camera(take_picture_method="picamera2", camera_config=camera_config_controls)
image2 = camera2.take_picture()
print(f"Captured image shape: {image2.shape if image2 is not None else 'None'}")



# Example 3: picamera2 with full configuration (streams)
print("\nExample 3: picamera2 with full stream configuration")
# This requires importing Picamera2 to create the config
try:
    from picamera2 import Picamera2
    
    temp_picam = Picamera2()
    full_config = temp_picam.create_still_configuration(
        main={"size": (1920, 1080), "format": "RGB888"},
        lores={"size": (640, 480)},
    )
    temp_picam.close()
    
    camera3 = Camera(take_picture_method="picamera2", camera_config=full_config)
    image3 = camera3.take_picture()
    print(f"Captured image shape: {image3.shape if image3 is not None else 'None'}")
except ImportError:
    print("Picamera2 not available, skipping full config example")




# Example 4: rpicam-still with basic configuration
print("\nExample 4: rpicam-still with basic configuration")
rpicam_config_basic = {
    "width": 1920,
    "height": 1080,
    "quality": 95,
}
camera4 = Camera(take_picture_method="rpicam-still", camera_config=rpicam_config_basic)
image4 = camera4.take_picture()
print(f"Captured image shape: {image4.shape if image4 is not None else 'None'}")




# Example 5: rpicam-still with advanced controls
print("\nExample 5: rpicam-still with advanced controls")
rpicam_config_advanced = {
    "width": 2560,
    "height": 1440,
    "shutter": 10000,       # 10ms shutter speed (in microseconds)
    "gain": 2.0,            # Analogue gain
    "brightness": 0.1,      # Brightness adjustment (-1.0 to 1.0)
    "contrast": 1.2,        # Contrast (0.0 to 2.0, 1.0 is default)
    "saturation": 1.1,      # Saturation
    "sharpness": 1.5,       # Sharpness
    "awb": "daylight",      # Auto white balance mode
    "denoise": "auto",      # Denoise mode
    "quality": 100,         # JPEG quality
    "encoding": "jpg",      # Output encoding
}
camera5 = Camera(take_picture_method="rpicam-still", camera_config=rpicam_config_advanced)
image5 = camera5.take_picture()
print(f"Captured image shape: {image5.shape if image5 is not None else 'None'}")




# Example 6: rpicam-still with flips and rotation
print("\nExample 6: rpicam-still with flips")
rpicam_config_flips = {
    "width": 1280,
    "height": 720,
    "hflip": True,          # Horizontal flip
    "vflip": True,          # Vertical flip
    "rotation": 0,          # Rotation (0 or 180)
}
camera6 = Camera(take_picture_method="rpicam-still", camera_config=rpicam_config_flips)
image6 = camera6.take_picture()
print(f"Captured image shape: {image6.shape if image6 is not None else 'None'}")




# Example 7: Using Camera with context manager (for picamera2)
print("\nExample 7: Using context manager (efficient for multiple captures)")
with Camera(take_picture_method="picamera2") as camera:
    # Camera is started once
    for i in range(3):
        image = camera.take_picture()
        print(f"Capture {i+1} shape: {image.shape if image is not None else 'None'}")
    # Camera is automatically stopped when exiting context




# Example 8: Manual start/stop for efficient multiple captures
print("\nExample 8: Manual start/stop for efficient operation")
camera8 = Camera(take_picture_method="picamera2")
camera8.start()  # Start once
for i in range(3):
    image = camera8.take_picture()
    print(f"Capture {i+1} shape: {image.shape if image is not None else 'None'}")
camera8.stop()  # Stop once



print("\n" + "="*50)
print("Configuration Reference:")
print("="*50)

print("""
picamera2 Configuration Options:
--------------------------------
1. Full Configuration (with streams):
   - Use Picamera2.create_still_configuration(), create_video_configuration(), etc.
   - Specify stream sizes and formats (main, lores, raw)
   
2. Camera Controls (as dict):
   - ExposureTime: Exposure time in microseconds
   - AnalogueGain: Analogue gain value
   - Brightness: Brightness level (-1.0 to 1.0)
   - Contrast: Contrast level (0.0 to 2.0)
   - Saturation: Saturation level
   - Sharpness: Sharpness level
   - AwbMode: Auto white balance mode (0-7)
   - ColourGains: Tuple of (red_gain, blue_gain)
   - And many more... (see picamera2 documentation)

rpicam-still Configuration Options:
-----------------------------------
All options should be specified as dictionary keys:
   - width, height: Image dimensions
   - shutter: Shutter speed in microseconds
   - gain/analoggain: Gain value
   - brightness: -1.0 to 1.0
   - contrast: 0.0 to 2.0
   - saturation: Saturation level
   - sharpness: Sharpness level
   - awb: 'auto', 'incandescent', 'tungsten', 'fluorescent', 'indoor', 'daylight', 'cloudy'
   - awbgains: Tuple or list of (red_gain, blue_gain)
   - denoise: 'auto', 'off', 'cdn_off', 'cdn_fast', 'cdn_hq'
   - quality: JPEG quality 1-100
   - encoding: 'jpg', 'png', 'bmp', 'rgb', 'yuv420'
   - hflip, vflip: Boolean for image flips
   - rotation: 0 or 180
   - exposure: 'sport', 'normal', 'long'
   - ev: Exposure compensation (-10 to 10)
   - metering: 'centre', 'spot', 'average', 'custom'
   - timeout: Timeout in milliseconds (default 1)

See rpicam-still documentation for complete list of options:
https://www.raspberrypi.com/documentation/computers/camera_software.html
""")
