from picamera import PiCamera
import time
import threading
from mode import Mode


class Core():
    """ Give no response if triggered accidently """

    def __init__(self, say):
        """ Initialise member variables. """
        self.say = say
        self.camera = None
        # Set default high resolution
        self.camera_hires = (3280, 2464)
        # Set default low resolution
        self.camera_lowres = (1024, 768)

        self.running = False
        self.main_thread = None
        self.path_str = '/home/pi/Documents'

    def initialise_camera(self):
        """ Initialise camera module. """
        self.camera = PiCamera()
        # Default to HIGH resolution
        self.camera.resolution = (self.camera_hires[0], self.camera_hires[1])
        self.camera.start_preview()

        # Camera warm-up time
        time.sleep(2)

    def set_high_res(self):
        """ Set camera into High Resolution mode. """
        self.camera.resolution = (self.camera_hires[0], self.camera_hires[1])

    def set_low_res(self):
        """ Set camera into Low Resolution mode. """
        self.camera.resolution = (self.camera_lowres[0], self.camera_lowres[1])

    def seconds_in_units(self, unit):
        # Convert interval and units into interval in seconds.
        multiplyer = 1
        if unit == 'second' or unit == 'seconds':
            multiplyer = 1
        elif unit == 'minute' or unit == 'minutes':
            multiplyer = 60
        elif unit == 'hour' or unit == 'hours':
            multiplyer = 3600
        elif unit == 'day' or unit == 'days':
            multiplyer = 86400
        elif unit == 'week' or unit == 'weeks':
            multiplyer = 604800
        elif unit == 'month' or unit == 'months':
            multiplyer = 18144000
        elif unit == 'year' or unit == 'years':
            multiplyer = 31536000
        return multiplyer

    def text2int(self, textnum, numwords={}):
        # Prepare "NumWords" dictionary
        if not numwords:
            units = [
                "zero",
                "one",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
                "ten",
                "eleven",
                "twelve",
                "thirteen",
                "fourteen",
                "fifteen",
                "sixteen",
                "seventeen",
                "eighteen",
                "nineteen"
            ]
            tens = [
                "",
                "",
                "twenty",
                "thirty",
                "forty",
                "fifty",
                "sixty",
                "seventy",
                "eighty",
                "ninety"
            ]
            scales = [
                "hundred",
                "thousand",
                "million",
                "billion",
                "trillion"
            ]

            # Special words
            numwords["and"] = (1, 0)
            numwords["a"] = (1, 1)  # AKA 1
            numwords["an"] = (1, 1)  # AKA 1
            # enumerate lists above into new dictionary.
            for idx, word in enumerate(units):
                numwords[word] = (1, idx)
            for idx, word in enumerate(tens):
                numwords[word] = (1, idx * 10)
            for idx, word in enumerate(scales):
                numwords[word] = (10 ** (idx * 3 or 2), 0)

        # Loop every word in "textnum".
        current = result = 0
        for word in textnum.split():
            if word in numwords:
                scale, increment = numwords[word]
                current = current * scale + increment
                if scale > 100:
                    result += current
                    current = 0
            else:
                # Not a valid written number, check
                # to see if its actually a number.
                valid_number = True
                numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                for c in word:
                    if c not in numbers:
                        valid_number = False
                # It was a valid number, just in text.
                if valid_number:
                    result += int(word)
                    current = 0

            # else:
            #     raise Exception("Illegal word: " + word)

        return result + current

    def take_photo(self, filename):
        if self.camera is not None:
            self.camera.capture(filename)
        else:
            self.say("Camera not initialised.")

    def take_timelapse(self,
                       interval_seconds,
                       length_seconds,
                       filename_prepend="img_",
                       filename_append=""):
        if self.camera is not None:
            for filename in self.camera.capture_continuous(
                 self.path_str +
                 "/" + filename_prepend +
                 "{timestamp:%Y-%m-%d_%H-%M-%S}.jpg" +
                 filename_append):

                time.sleep(interval_seconds)
                # Subtract interval from length.
                length_seconds = length_seconds - interval_seconds
                if length_seconds <= 0:
                    # Stop taking photos
                    break
            self.say("Time lapse is complete.")
        else:
            self.say("Camera not initialised.")

    def run_loop(self):
        """ Main method to run as it's own thread. """
        self.initialise_camera()
        while self.running:
            # Not doing anything, sleep for
            # a bit to allow things to happen
            time.sleep(0.5)

    def start_thread(self):
        """ Call this method to ensure thread is started. """
        if not self.running:
            self.running = True
            self.main_thread = threading.Thread(target=self.run_loop).start()

    def stop_thread(self):
        """ Call this method to stop thread. """
        self.running = False
        self.main_thread.join()
        self.main_thread = None
