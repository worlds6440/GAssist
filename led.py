# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Signal states on a LED'''

import itertools
import logging
import os
import threading
import time

import RPi.GPIO as GPIO

# Import blinkstick module
from blinkstick import blinkstick


logger = logging.getLogger('led')

CONFIG_DIR = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
CONFIG_FILES = [
    '/etc/status-led.ini',
    os.path.join(CONFIG_DIR, 'status-led.ini')
]


class LED:

    """Starts a background thread to show patterns with the LED."""

    def __init__(self, channel):
        self.animator = threading.Thread(target=self._animate)
        self.channel = channel
        self.iterator = None
        self.running = False
        self.state = None
        self.last_known_state = None
        self.sleep = 0

        self.max_pwm = 100
        GPIO.setup(channel, GPIO.OUT)  # GPIO pin 25 by default
        self.pwm = GPIO.PWM(channel, self.max_pwm)

        # Find the first BlinkStick
        self.max_brightness = 255
        self.bstick = blinkstick.find_first()
        # Set the color red on the 1st LED of G channel to OFF
        self.led_index = 0
        self.led_channel = 1
        # Ensure the LED is OFF after boot
        self.bstick.set_color(
            channel=self.led_channel,
            index=self.led_index,
            name="black")

        # Default LED colour
        self.base_red = 255
        self.base_green = 0
        self.base_blue = 0

    def start(self):
        self.pwm.start(0)  # off by default
        self.running = True
        self.animator.start()

    def stop(self):
        self.running = False
        self.animator.join()
        self.pwm.stop()
        GPIO.output(self.channel, GPIO.LOW)

    def set_state(self, state):
        self.state = state
        self.last_known_state = state
        # Everytime state is changed, reset colour
        self.base_red = 255
        self.base_green = 0
        self.base_blue = 0

    def _animate(self):
        # TODO(ensonic): refactor or add justification
        # pylint: disable=too-many-branches

        # base colour used to flash/pulse/light the led.
        while self.running:
            if self.state:
                if self.state == 'on-green':
                    # Used when RECORDING VOICE
                    self.iterator = None
                    self.sleep = 0.0
                    self.pwm.ChangeDutyCycle(self.max_pwm)
                    # Choose a colour (green works well for "Listening")
                    self.base_red = 0
                    self.base_green = 190
                    self.base_blue = 0
                    # Turn ON the led
                    self.bstick.set_color(
                        channel=self.led_channel,
                        index=self.led_index,
                        red=self.base_red,
                        green=self.base_green,
                        blue=self.base_blue)
                elif self.state == 'on-red':
                    # Used when waiting for trigger
                    self.iterator = None
                    self.sleep = 0.0
                    self.pwm.ChangeDutyCycle(self.max_pwm)
                    # Turn ON the led
                    self.bstick.set_color(
                        channel=self.led_channel,
                        index=self.led_index,
                        red=self.base_red,
                        green=self.base_green,
                        blue=self.base_blue)
                elif self.state == 'off':
                    self.iterator = None
                    self.sleep = 0.0
                    self.pwm.ChangeDutyCycle(0)
                    self.bstick.set_color(
                        channel=self.led_channel,
                        index=self.led_index,
                        red=0,
                        green=0,
                        blue=0)
                elif self.state == 'blink':
                    self.iterator = itertools.cycle([0, self.max_pwm])
                    self.sleep = 0.5
                elif self.state == 'blink-3':
                    self.iterator = itertools.cycle(
                        [0, self.max_pwm] * 3 + [0, 0])
                    self.sleep = 0.25
                elif self.state == 'beacon':
                    self.iterator = itertools.cycle(
                        itertools.chain(
                            [30] * 100, [self.max_pwm] * 8,
                            range(self.max_pwm, 30, -5)))
                    self.sleep = 0.05
                elif self.state == 'beacon-dark':
                    self.iterator = itertools.cycle(
                        itertools.chain(
                            [0] * 10,  # Delay between pulses: 10 values of [0] with 0.05 seconds sleep between
                            range(0, 30, 3),
                            range(30, 0, -3)))
                    self.sleep = 0.05
                elif self.state == 'decay':
                    self.iterator = itertools.cycle(range(self.max_pwm, 0, -2))
                    self.sleep = 0.05
                elif self.state == 'pulse-slow':
                    self.iterator = itertools.cycle(
                        itertools.chain(
                            range(0, self.max_pwm, 2),
                            range(self.max_pwm, 0, -2)))
                    self.sleep = 0.1
                elif self.state == 'pulse-slow-dark':
                    self.iterator = itertools.cycle(
                        itertools.chain(
                            range(10, 80, 2),
                            range(80, 10, -2)))
                    self.sleep = 0.1
                elif self.state == 'pulse-quick':
                    self.iterator = itertools.cycle(
                        itertools.chain(
                            range(0, self.max_pwm, 5),
                            range(self.max_pwm, 0, -5)))
                    self.sleep = 0.05
                else:
                    logger.warning("unsupported state: %s", self.state)
                self.state = None
            if self.iterator:
                new_value = next(self.iterator)
                self.pwm.ChangeDutyCycle(new_value)

                # Vary LED brightness but keep colour
                brightness = (min(self.max_pwm, new_value) / self.max_brightness)

                self.bstick.set_color(
                    channel=self.led_channel,
                    index=self.led_index,
                    red=self.base_red * brightness,
                    green=self.base_green * brightness,
                    blue=self.base_blue * brightness)
                time.sleep(self.sleep)
            else:
                time.sleep(0.25)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    )

    import configargparse
    parser = configargparse.ArgParser(
        default_config_files=CONFIG_FILES,
        description="Status LED daemon")
    parser.add_argument('-G', '--gpio-pin', default=25, type=int,
                        help='GPIO pin for the LED (default: 25)')
    args = parser.parse_args()

    led = None
    state_map = {
        "starting": "pulse-quick",
        # "ready": "beacon-dark",
        # "ready": "on-red",
        "ready": "pulse-slow-dark",
        "listening": "on-green",
        "thinking": "pulse-quick",
        "stopping": "pulse-quick",
        "power-off": "off",
        "error": "blink-3",
    }
    try:
        GPIO.setmode(GPIO.BCM)

        led = LED(args.gpio_pin)
        led.start()
        while True:
            try:
                state = input()
                if not state:
                    continue
                if state not in state_map:
                    logger.warning("unsupported state: %s, must be one of: %s",
                                   state, ",".join(state_map.keys()))
                    continue

                led.set_state(state_map[state])
            except EOFError:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    except:
        logger.warning("ERROR: Probably Blinkstick")
    finally:
        led.stop()
        GPIO.cleanup()

if __name__ == '__main__':
    main()
