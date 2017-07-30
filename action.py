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

"""Carry out voice commands by recognising keywords."""

import datetime
from datetime import timedelta
import logging
import subprocess
import actionbase
import time
from mode import Mode

# =============================================================================
#
# Hey, Makers!
#
# This file contains some examples of voice commands that are handled locally,
# right on your Raspberry Pi.
#
# Do you want to add a new voice command? Check out the instructions at:
# https://aiyprojects.withgoogle.com/voice/#makers-guide-3-3--create-a-new-voice-command-or-action
# (MagPi readers - watch out! You should switch to the instructions in the link
#  above, since there's a mistake in the MagPi instructions.)
#
# In order to make a new voice command, you need to do two things. First, make a
# new action where it says:
#   "Implement your own actions here"
# Secondly, add your new voice command to the actor near the bottom of the file,
# where it says:
#   "Add your own voice commands here"
#
# =============================================================================

# Actions might not use the user's command. pylint: disable=unused-argument


# Example: Say a simple response
# ================================
#
# This example will respond to the user by saying something. You choose what it
# says when you add the command below - look for SpeakAction at the bottom of
# the file.
#
# There are two functions:
# __init__ is called when the voice commands are configured, and stores
# information about how the action should work:
#   - self.say is a function that says some text aloud.
#   - self.words are the words to use as the response.
# run is called when the voice command is used. It gets the user's exact voice
# command as a parameter.


class SpeakAction(object):

    """Says the given text via TTS."""

    def __init__(self, say, words):
        self.say = say
        self.words = words

    def run(self, voice_command):
        self.say(self.words)


# Example: Tell the current time
# ==============================
#
# This example will tell the time aloud. The to_str function will turn the time
# into helpful text (for example, "It is twenty past four."). The run function
# uses to_str say it aloud.

class SpeakTime(object):

    """Says the current local time with TTS."""

    def __init__(self, say):
        self.say = say

    def run(self, voice_command):
        time_str = self.to_str(datetime.datetime.now())
        self.say(time_str)

    def to_str(self, dt):
        """Convert a datetime to a human-readable string."""
        HRS_TEXT = ['midnight', 'one', 'two', 'three', 'four', 'five', 'six',
                    'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
        MINS_TEXT = ["five", "ten", "quarter", "twenty", "twenty-five", "half"]
        hour = dt.hour
        minute = dt.minute

        # convert to units of five minutes to the nearest hour
        minute_rounded = (minute + 2) // 5
        minute_is_inverted = minute_rounded > 6
        if minute_is_inverted:
            minute_rounded = 12 - minute_rounded
            hour = (hour + 1) % 24

        # convert time from 24-hour to 12-hour
        if hour > 12:
            hour -= 12

        if minute_rounded == 0:
            if hour == 0:
                return 'It is midnight.'
            return "It is %s o'clock." % HRS_TEXT[hour]

        if minute_is_inverted:
            return 'It is %s to %s.' % (MINS_TEXT[minute_rounded - 1], HRS_TEXT[hour])
        return 'It is %s past %s.' % (MINS_TEXT[minute_rounded - 1], HRS_TEXT[hour])


# Example: Run a shell command and say its output
# ===============================================
#
# This example will use a shell command to work out what to say. You choose the
# shell command when you add the voice command below - look for the example
# below where it says the IP address of the Raspberry Pi.

class SpeakShellCommandOutput(object):

    """Speaks out the output of a shell command."""

    def __init__(self, say, shell_command, failure_text):
        self.say = say
        self.shell_command = shell_command
        self.failure_text = failure_text

    def run(self, voice_command):
        output = subprocess.check_output(self.shell_command, shell=True).strip()
        if output:
            self.say(output)
        elif self.failure_text:
            self.say(self.failure_text)


# Example: Change the volume
# ==========================
#
# This example will can change the speaker volume of the Raspberry Pi. It uses
# the shell command SET_VOLUME to change the volume, and then GET_VOLUME gets
# the new volume. The example says the new volume aloud after changing the
# volume.

class VolumeControl(object):

    """Changes the volume and says the new level."""

    GET_VOLUME = r'amixer get Master | grep "Front Left:" | sed "s/.*\[\([0-9]\+\)%\].*/\1/"'
    SET_VOLUME = 'amixer -q set Master %d%%'

    def __init__(self, say, change):
        self.say = say
        self.change = change

    def run(self, voice_command):
        res = subprocess.check_output(VolumeControl.GET_VOLUME, shell=True).strip()
        try:
            logging.info("volume: %s", res)
            vol = int(res) + self.change
            vol = max(0, min(100, vol))
            subprocess.call(VolumeControl.SET_VOLUME % vol, shell=True)
            self.say(_('Volume at %d %%.') % vol)
        except (ValueError, subprocess.CalledProcessError):
            logging.exception("Error using amixer to adjust volume.")


# Example: Repeat after me
# ========================
#
# This example will repeat what the user said. It shows how you can access what
# the user said, and change what you do or how you respond.

class RepeatAfterMe(object):

    """Repeats the user's command."""

    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword

    def run(self, voice_command):
        # The command still has the 'repeat after me' keyword, so we need to
        # remove it before saying whatever is left.
        to_repeat = voice_command.replace(self.keyword, '', 1)
        self.say(to_repeat)


# =========================================
# Makers! Implement your own actions here.
# =========================================


# Power: Shutdown or reboot the pi
# ================================
# Shuts down the pi or reboots with a response
#

class PowerCommand(object):
    """Shutdown or reboot the pi"""

    def __init__(self, say, command):
        self.say = say
        self.command = command

    def run(self, voice_command):
        if (self.command == "shutdown"):
            self.say("Shutting down, goodbye")
            subprocess.call("sudo shutdown now", shell=True)
        elif (self.command == "reboot"):
            self.say("Rebooting")
            subprocess.call("sudo shutdown -r now", shell=True)
        else:
            logging.error("Error identifying power command.")
            self.say("Sorry I didn't identify that command")


# Photo: Capture a photo using the onboard rpi camera board.
# ================================
# Capture a photo using the onboard rpi camera board.
#

class PhotoCapture(object):
    """Shutdown or reboot the pi"""

    def __init__(self, say, command, camera_core):
        self.say = say
        self.command = command
        self.camera_core = camera_core

    def run(self, voice_command):
        if (self.command == "photo"):
            time_obj = datetime.datetime.now()
            time_str = time_obj.strftime("%Y-%m-%d_%H-%M-%S")
            path_str = '/home/pi/Documents'
            self.say("I'm taking a photo. Say cheese")

            # use pre-initialised camera to take photo (faster).
            self.camera_core.take_photo(
                "{}/photo_{}.jpg".format(path_str, time_str)
            )

            self.say("Done.")
            # self.say(words="",
            #     wav_file="/home/pi/voice-recognizer-raspi/src/camera-shutter-click-03.wav")
        else:
            logging.error("Error identifying photo command.")
            self.say("Sorry I didn't identify that command")


# Uptime: Respond with length of time the Pi has been up.
# ================================
# Run "uptime" on shell and speak the result.
#

class Uptime(object):
    """Shutdown or reboot the pi"""

    def __init__(self, say, command):
        self.say = say
        self.command = command

    def run(self, voice_command):
        if (self.command == "uptime"):
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])

                dt = timedelta(seconds=uptime_seconds)
                days = dt.days
                hours = dt.seconds // 3600
                minutes = (dt.seconds // 60) % 60

                time_str = ("{} days, {} hours and {} minutes"
                            ).format(days, hours, minutes)
                self.say(time_str)
        else:
            logging.error("Error identifying power command.")
            self.say("Sorry I didn't identify that command")


# Pass: Give no response if triggered accidently.
# ================================

class Pass(object):
    """ Give no response if triggered accidently """

    def __init__(self, say):
        self.say = say

    def run(self, voice_command):
        self.say("")


# Timelapse
# ========================
#
# Start a new thread that will take several photos at set intervals.

class TimeLapse(object):

    """ Take several photos a set intervals. """

    def __init__(self, say, camera_core):
        self.say = say
        self.camera_core = camera_core

    def run(self, voice_command):
        # The command still has the 'repeat after me' keyword, so we need to
        # remove it before saying whatever is left.

        interval_str = ''
        interval = 10
        interval_unit = 'seconds'
        length_str = ''
        length = 2
        length_unit = 'minutes'

        time_units = [
            'second',
            'seconds',
            'minute',
            'minutes',
            'hour',
            'hours',
            'day',
            'days',
            'week',
            'weeks',
            'month',
            'months',
            'year',
            'years'
        ]

        word_list = voice_command.split()
        for i, x in enumerate(word_list):
            if x == 'at' or x == 'every':
                # append all text numbers together and find the time unit.
                index = 1
                while index < (len(word_list) - i):
                    word = word_list[i + index]
                    if word in time_units:
                        # Store interval time unit
                        # and stop processing interval.
                        interval_unit = word
                        index = len(word_list)
                    else:
                        if interval_str != '':
                            interval_str = interval_str + ' '
                        interval_str = interval_str + word
                    index = index + 1
                if interval_str == "":
                    interval = 1  # No number, e.g."Every minute"
                else:
                    interval = self.camera_core.text2int(interval_str)

            if x == 'for':
                # append all text numbers together and find the time unit.
                index = 1
                while index < (len(word_list) - i):
                    word = word_list[i + index]
                    if word in time_units:
                        # Store length time unit
                        # and stop processing length.
                        length_unit = word
                        index = len(word_list)
                    else:
                        if length_str != '':
                            length_str = length_str + ' '
                        length_str = length_str + word
                    index = index + 1
                length = self.camera_core.text2int(length_str)

        # Convert interval and length into seconds.
        interval_seconds = interval * self.camera_core.seconds_in_units(
            interval_unit)
        length_seconds = length * self.camera_core.seconds_in_units(
            length_unit)

        # DEBUG
        # self.say("{} seconds in interval and {}"
        # " seconds in length".format(interval_seconds, length_seconds))
        # _DEBUG

        if interval_seconds > 0 and length_seconds > 0:
            self.say(
                "Confirmed, I'll take a photo every "
                "{} {} for {} {}.".format(
                    interval, interval_unit, length, length_unit))

            # Take the photos using threaded core module
            self.camera_core.length_seconds = length_seconds
            self.camera_core.interval_seconds = interval_seconds
            self.camera_core.mode = Mode.TIME_LAPSE
            self.camera_core.take_timelapse(
               interval_seconds,
               length_seconds,
               filename_prepend="img_",
               filename_append="")
        else:
            # Failed to take photos due to invalid interval or length.
            if interval_seconds <= 0:
                self.say("Sorry, invalid interval.")
            elif length_seconds <= 0:
                self.say("Sorry, invalid length.")


def make_actor(say, camera):
    """Create an actor to carry out the user's commands."""

    actor = actionbase.Actor()

    actor.add_keyword(
        _('ip address'), SpeakShellCommandOutput(
            say, "ip -4 route get 1 | head -1 | cut -d' ' -f8",
            _('I do not have an ip address assigned to me.')))

    actor.add_keyword(_('volume up'), VolumeControl(say, 10))
    actor.add_keyword(_('volume down'), VolumeControl(say, -10))
    actor.add_keyword(_('max volume'), VolumeControl(say, 100))

    actor.add_keyword(_('repeat after me'),
                      RepeatAfterMe(say, _('repeat after me')))

    # =========================================
    # Makers! Add your own voice commands here.
    # =========================================

    actor.add_keyword(_('power off'), PowerCommand(say, 'shutdown'))
    actor.add_keyword(_('reboot'), PowerCommand(say, 'reboot'))

    actor.add_keyword(_('take a photo'), PhotoCapture(say, 'photo', camera))
    actor.add_keyword(_('uptime'), Uptime(say, 'uptime'))

    actor.add_keyword(_('time lapse'), TimeLapse(say, camera))

    # If triggered accidently, either say "pass" or detect no words said.
    actor.add_keyword(_('pass'), Pass(say))
    # actor.add_keyword(_(''), Pass(say))
    return actor


def add_commands_just_for_cloud_speech_api(actor, say):
    """Add simple commands that are only used with the Cloud Speech API."""
    def simple_command(keyword, response):
        actor.add_keyword(keyword, SpeakAction(say, response))

    simple_command('alexa', _("We've been friends since we were both starter projects"))
    simple_command(
        'beatbox',
        'pv zk pv pv zk pv zk kz zk pv pv pv zk pv zk zk pzk pzk pvzkpkzvpvzk kkkkkk bsch')
    simple_command(_('clap'), _('clap clap'))
    simple_command('google home', _('She taught me everything I know.'))
    simple_command(_('hello'), _('hello to you too'))
    simple_command(_('tell me a joke'),
                   _('What do you call an alligator in a vest? An investigator.'))
    simple_command(_('three laws of robotics'),
                   _("""The laws of robotics are
0: A robot may not injure a human being or, through inaction, allow a human
being to come to harm.
1: A robot must obey orders given it by human beings except where such orders
would conflict with the First Law.
2: A robot must protect its own existence as long as such protection does not
conflict with the First or Second Law."""))
    simple_command(_('where are you from'), _("A galaxy far, far, just kidding. I'm from Seattle."))
    simple_command(_('your name'), _('A machine has no name'))

    actor.add_keyword(_('time'), SpeakTime(say))
