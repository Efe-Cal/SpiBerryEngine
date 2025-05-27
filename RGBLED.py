import RPi.GPIO as GPIO # type: ignore

class RGBLED:
    """
    A class to control an RGB LED connected to Raspberry Pi GPIO pins.
    """
    def __init__(self, red_pin: int, green_pin: int, blue_pin: int, active_high: bool = True):
        """
        Initializes the RGB LED.

        Args:
            red_pin (int): The GPIO pin number for the red component.
            green_pin (int): The GPIO pin number for the green component.
            blue_pin (int): The GPIO pin number for the blue component.
            active_high (bool): True if the LED turns on with a HIGH signal, 
                                False if it turns on with a LOW signal. Defaults to True.
        """
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.active_high = active_high
        self.on_level = GPIO.HIGH if active_high else GPIO.LOW
        self.off_level = GPIO.LOW if active_high else GPIO.HIGH

        # Consider setting GPIO mode here if not done globally, e.g.,
        # GPIO.setmode(GPIO.BCM) 
        # Or ensure it's documented that the user must set it.

        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        self.turn_off() # Initialize with LED off
        
    def set_color(self, red_state, green_state, blue_state):
        """
        Sets the color of the LED by controlling the state of each component.

        Args:
            red_state: The state for the red component (e.g., self.on_level or self.off_level).
            green_state: The state for the green component.
            blue_state: The state for the blue component.
        """
        GPIO.output(self.red_pin, red_state)
        GPIO.output(self.green_pin, green_state)
        GPIO.output(self.blue_pin, blue_state)

    def turn_off(self):
        """Turns the LED off."""
        self.set_color(self.off_level, self.off_level, self.off_level)

    def red(self):
        """Sets the LED to red."""
        self.set_color(self.on_level, self.off_level, self.off_level)

    def green(self):
        """Sets the LED to green."""
        self.set_color(self.off_level, self.on_level, self.off_level)

    def blue(self):
        """Sets the LED to blue."""
        self.set_color(self.off_level, self.off_level, self.on_level)

    def yellow(self):
        """Sets the LED to yellow (red + green)."""
        self.set_color(self.on_level, self.on_level, self.off_level)

    def cyan(self):
        """Sets the LED to cyan (green + blue)."""
        self.set_color(self.off_level, self.on_level, self.on_level)

    def magenta(self):
        """Sets the LED to magenta (red + blue)."""
        self.set_color(self.on_level, self.off_level, self.on_level)

    def white(self):
        """Sets the LED to white (red + green + blue)."""
        self.set_color(self.on_level, self.on_level, self.on_level)

    def cleanup(self):
        """Cleans up the GPIO pins used by this LED."""
        self.turn_off()
        GPIO.cleanup([self.red_pin, self.green_pin, self.blue_pin])

# Example Usage (ensure GPIO mode is set before this):
if __name__ == "__main__":
    import time
    # Ensure GPIO mode is set before using the RGBLED class
    GPIO.setmode(GPIO.BCM) # Or GPIO.BOARD
    led = RGBLED(red_pin=22, green_pin=10, blue_pin=9, active_high=False)
    try:
        led.red()
        time.sleep(1)
        led.green()
        time.sleep(1)
        led.blue()
        time.sleep(1)
        led.turn_off()
    finally:
        led.cleanup() # Clean up specific pins
        # Or GPIO.cleanup() # Clean up all pins if this is the end of the script
