import datetime

from PIL import Image, ImageDraw, ImageFont
from board import SCL, SDA
import busio
import adafruit_ssd1306

from pisces.base import PiscesBase

class Display(PiscesBase):
    """Class to control the Adafruit PiOLED status display."""
    def __init__(self, pisces_core, **kwargs):
        super().__init__(**kwargs)  # Load config and configure logging.
        self._core = pisces_core

        self._width = int(self.config['display']['width'])
        self._height = int(self.config['display']['height'])
        self._top_padding = int(self.config['display']['top_padding'])
        self._left_padding = int(self.config['display']['left_padding'])
        self._spacing = int(self.config['display']['spacing'])

        self._image_buffer = Image.new('1', (self._width, self._height))
        self._image_draw = ImageDraw.Draw(self._image_buffer)
        self._font = ImageFont.load_default()
        
        self._initialise()
        self.clear()

    def _initialise(self):
        try:
            # Create the I2C interface.
            i2c = busio.I2C(SCL, SDA)
            # Create the SSD1306 OLED display object.
            self._display = adafruit_ssd1306.SSD1306_I2C(self._width, self._height, i2c)
        except Exception as err:
            self.logger.error("Error initialising PiOLED display: {}".format(err))
            self._initialised = False
        else:
            self.logger.info("PiOLED display initialised.")
            self._initialised = True

    @property
    def is_initialised(self):
        """Returns True if the status has been successfully initialised, otherwise False."""
        return self._initialised

    def clear(self, white=False):
        """Clears the display."""
        if self.is_initialised:
            if white:
                self._display.fill(255)
            else:
                self._display.fill(0)
            self._display.show()
        else:
            self.logger.warning("Attempt to clear display but display not initialised.")

    def update(self):
        """Updates the status display with the Pisces core status info."""
        if self.is_initialised:
            # Format current time
            now = datetime.datetime.now()
            time_string = now.strftime("%H:%M")

            # Clear image buffer
            self._image_draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)

            # Add text
            self._image_draw.text((self._left_padding, self._top_padding),
                                  "Pisces v{}  {}".format(self.__version__,
                                                          time_string),
                                  font=self._font, fill=255)

            if self._core.status['water_temp_status'] == 'OK':
                rectangle_colour = 0
                text_colour = 255
            else:
                # Water temperature is outside target range, highlight it.
                rectangle_colour = 255
                text_colour = 0
                
            self._image_draw.rectangle((self._left_padding - 1,
                                        1 * spacing,
                                        self._left_padding + 47,
                                        2 * spacing - 1), outline=rectangle_colour, fill=rectangle_colour)
            self._image_draw.text((self._left_padding, self._top_padding + self._spacing),
                                  "WT:{:2.1f}".format(self._core.status['water_temp']),
                                  font=self._font, fill=text_colour)
                
            self._image_draw.text((self._left_padding, self._top_padding + self._spacing),
                                  "            AT:{:2.1f}C".format(self._core.status['air_temp']),
                                  font=self._font, fill=255)
            
            if self._core.status['water_level_status'] == 'OK':
                rectangle_colour = 0
                text_colour = 255
            else:
                # Water level is outside target range, highlight it.
                rectangle_colour = 255
                text_colour = 0

        
            self._image_draw.rectangle((self._left_padding - 1,
                                        2 * spacing,
                                        self._left_padding + 53,
                                        3 * spacing - 1), outline=rectangle_colour, fill=rectangle_colour)
            self._image_draw.text((self._left_padding, self._top_padding + 2 * self._spacing),
                                  "WL:{:2.1f}cm".format(self._core.status['water_level']),
                                  font=self._font, fill=text_colour)        

            if self._core.status['overflow']:
                # Water overflow sensor triggered.
                self._image_draw.rectangle((self._left_padding + 70,
                                            self._top_padding + 2 * self._spacing + 2,
                                            self._left_padding + 119,
                                            self._top_padding + 3 * self._spacing + 1),
                                           outline=255, fill=255)
                self._image_draw.text((self._left_padding + 71,
                                       self._top_padding + 2 * self._spacing),
                                      "OVERFLOW", font=self._font, fill=0)

            if self._core.status['lights_auto']:
                lights = 'Auto'
            else:
                if self._core.status['lights_enabled']:
                    lights = 'On'
                else:
                    lights = 'Off'

            if self._core.status['fan_auto']:
                fan = 'Auto'
            else:
                if self._core.status['fan_enabled']:
                    fan = 'On'
                else:
                    fan = 'Off'

            if self._core.status['pump_auto']:
                pump = 'Auto'
            else:
                if self._core.status['pump_enabled']:
                    pump = 'On'
                else:
                    pump = 'Off'
            
            self._image_draw.text((self._left_padding, self._top_padding + 3 * self._spacing),
                                  "L:{:<4} F:{:<4} P:{:<4}".format(lights, fan, pump),
                                  font=self._font, fill=255)
            
            # Display updated image
            self._display.image(self._image_buffer)
            self._display.show()
        else:
            self.logger.warning("Attempt to update display but display not initialised.")
