#!/usr/bin/env python3
"""Driver for stepper motors"""

import time
from RPi import GPIO
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] -- %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")


class GpioManager(object):

    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        GPIO.cleanup()
        return False


class StepperMotor(object):
    """A simple stepper motor with 3 control signals."""

    def __init__(self, pin_en, pin_dir, pin_stp):
        self.pins = [pin_en, pin_dir, pin_stp]
        for p in self.pins:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    def drive(self, duration, freq, dc, clockwise):
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH if clockwise else GPIO.LOW)
        p = GPIO.PWM(self.pins[2], freq)
        p.start(dc * 100)  # GPIO.PWM use dc from 0 to 100
        time.sleep(duration)
        p.stop()

    def calibrate(self, freq):
        print("Check direction:")
        input("Please set the object to the middle and press enter")
        self.forward(1, freq=500)
        ans = input("Is the object going forward (1) or backward (0)?")
        direction = int(ans) == 1
        self.release()
        input("Place the object to one end and press enter to start.")
        self.hold()
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH)
        p = GPIO.PWM(self.pins[2], freq)
        p.start(0.5 * 100)  # GPIO.PWM use dc from 0 to 100
        t0 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        input("Press enter when the object reaches the other end")
        t1 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        p.stop()
        return {"direction": direction, "freq": freq, "time": t1 - t0}

    def forward(self, duration, freq=500, dc=0.50):
        self.drive(duration, freq, dc, True)

    def backward(self, duration, freq=500, dc=0.50):
        self.drive(duration, freq, dc, False)

    def release(self):
        GPIO.output(self.pins[0], GPIO.LOW)

    def hold(self):
        GPIO.output(self.pins[0], GPIO.HIGH)


class BoundedStepperMotor(object):
    """A stepper motor with two keys to stop when collide onto."""

    def __init__(self,
                 pin_en,
                 pin_dir,
                 pin_stp,
                 pin_b0,
                 pin_b1,
                 freq=1000,
                 dc=0.5):
        self.pins = [pin_en, pin_dir, pin_stp]
        self.bounds = [pin_b0, pin_b1]
        self.default_freq = freq
        self.default_dc = dc
        self.reset()

    def calibrate(self, freq=1000):
        # a very large duration to ensure reach the boundary.
        trial_duration = 3600  # an hour
        self.backward(trial_duration, freq)
        t0 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        self.forward(trial_duration, freq)
        t1 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        ans = input("Does the full move goes forward (Y) or backward (N)?")
        direction = bool(ans.lower().startswith("y"))
        return {"clockwise": direction, "freq": freq, "time": t1 - t0}

    def reset(self):
        for p in self.pins:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
        for p in self.bounds:
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def drive(self, duration, freq=None, dc=None, clockwise=True):
        real_freq = self.default_freq if freq is None else freq
        real_dc = dc if dc is not None else self.default_dc
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH if clockwise else GPIO.LOW)
        p = GPIO.PWM(self.pins[2], real_freq)
        d = self.bounds[1] if clockwise else self.bounds[0]
        p.start(real_dc * 100)  # GPIO.PWM use dc from 0 to 100
        GPIO.wait_for_edge(d, GPIO.RISING, timeout=duration * 1000)
        p.stop()

    def forward(self, duration=3600, freq=None, dc=None):
        self.drive(duration, freq, dc, True)

    def backward(self, duration=3600, freq=None, dc=None):
        self.drive(duration, freq, dc, False)

    def release(self):
        GPIO.output(self.pins[0], GPIO.LOW)

    def hold(self):
        GPIO.output(self.pins[0], GPIO.HIGH)


def test():
    with GpioManager() as _:
        motor_x = BoundedStepperMotor(5, 3, 4, 6, 7, freq=1000)
        print(motor_x.calibrate())
        for _ in range(4):
            print("Goes forward")
            motor_x.forward(5)
            print("Stopped")
            print("Goes backward")
            motor_x.backward(5)
            print("Stopped")


if __name__ == "__main__":
    test()
