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

    def __init__(self, pin_en, pin_dir, pin_stp, freq=1000, dc=0.5):
        self.pins = [pin_en, pin_dir, pin_stp]
        self.default_freq = freq
        self.default_dc = dc
        self.reset()

    def reset(self):
        for p in self.pins:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    def calibrate(self, freq, length):
        print(f">> Calibrating with PWM freq {freq}Hz for length {length}m <<")
        print(">>> Check direction:")
        self.release()
        input(">>> Place the object to the center and press enter")
        self.hold()
        self.forward(2, freq=freq)
        ans = input(">>> Is the object going forward (1) or backward (0)? ")
        clockwise = int(ans) == 1
        self.release()
        input(">>> Place the object to the forward start and press enter.")
        self.hold()
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH if clockwise else GPIO.LOW)
        p = GPIO.PWM(self.pins[2], freq)
        p.start(0.5 * 100)  # GPIO.PWM use dc from 0 to 100
        t0 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        input(">>> Press enter when the object reaches the other end")
        t1 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        p.stop()
        return {
            "clockwise": clockwise,
            "freq": freq,
            "speed": length / (t1 - t0)
        }

    def drive(self, duration, freq, dc, clockwise):
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH if clockwise else GPIO.LOW)
        p = GPIO.PWM(self.pins[2], freq)
        p.start(dc * 100)  # GPIO.PWM use dc from 0 to 100
        time.sleep(duration)
        p.stop()

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

    def calibrate(self, freq, length):
        print(f">> Calibrating with PWM freq {freq}Hz for length {length}m <<")
        print(">>> Check direction:")
        self.release()
        input(">>> Place the object to the center and press enter")
        self.hold()
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH)
        p = GPIO.PWM(self.pins[2], freq)
        k0, k1 = self.bounds
        GPIO.add_event_detect(k0, GPIO.RISING)
        GPIO.add_event_detect(k1, GPIO.RISING)
        p.start(0.5 * 100)  # GPIO.PWM use dc from 0 to 100
        print(">>> Press the correct collision detector within 5 secs")
        k0_pressed, k1_pressed = False, False
        for _ in range(5 * 100):
            time.sleep(0.01)
            k0_pressed = GPIO.event_detected(k0)
            k1_pressed = GPIO.event_detected(k1)
            if k0_pressed or k1_pressed:
                break
        p.stop()
        GPIO.remove_event_detect(k0)
        GPIO.remove_event_detect(k1)
        ans = input(">>> Is the object going forward (1) or backward (0)? ")
        clockwise = int(ans) == 1  # shall motor go clockwise if move forward
        # self.drive expect that if go clockwise, k1 shall be pressed, swap if
        # we detect something different.
        shall_swap = k0_pressed
        if shall_swap:
            self.bounds[0], self.bounds[1] = self.bounds[1], self.bounds[0]
            print(f">>> swapped bounds as {self.bounds}")
        # a very large duration to ensure reach the boundary.
        print(">>> The motor will go backward to the forward start.")
        trial_duration = 120  # an hour
        self.drive(trial_duration, freq, 0.5, not clockwise)
        print(">>> The motor will perform a full move forward.")
        t0 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        self.drive(trial_duration, freq, 0.5, clockwise)
        t1 = time.clock_gettime_ns(time.CLOCK_MONOTONIC) * 1e-9
        return {
            "clockwise": clockwise,
            "freq": freq,
            "speed": length / (t1 - t0),
            "swap_bounds": shall_swap
        }

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
        GPIO.add_event_detect(d, GPIO.RISING)
        p.start(real_dc * 1000)  # GPIO.PWM use dc from 0 to 100
        collision_detected = False
        for _ in range(int(duration * 100)):
            time.sleep(0.001)
            if GPIO.event_detected(d):
                collision_detected = True
                break
        p.stop()
        GPIO.remove_event_detect(d)
        if collision_detected:
            # go backward a little bit to release collision detector
            time.sleep(0.1)  # wait some time to avoid sudden acceleration.
            GPIO.output(self.pins[0], GPIO.HIGH)
            GPIO.output(self.pins[1], GPIO.LOW if clockwise else GPIO.HIGH)
            p = GPIO.PWM(self.pins[2], real_freq)
            p.start(real_dc * 100)
            # In our exp, run 0.1s with 1000hz goes 1cm. we want to move 0.05cm,
            # so the sleep time will be 0.1/2 * 1000/freq = 50 / freq
            time.sleep(50 / freq)
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
        motor_x = BoundedStepperMotor(3, 4, 5, 6, 7, freq=1000)
        print(motor_x.calibrate(1000, 0.5))
        motor_x.release()
        input("Put the motor to left")
        motor_x.hold()
        input("Press enter to start")
        for _ in range(4):
            print("Goes forward")
            motor_x.forward(10)
            print("Stopped")
            print("Goes backward")
            motor_x.backward(10)
            print("Stopped")


def test2():
    with GpioManager() as _:
        motor_x = StepperMotor(14, 15, 16, freq=4000)
        print(motor_x.calibrate(4000, 0.15))
        motor_x.release()
        input("Put the motor to left")
        motor_x.hold()
        input("Press enter to start")
        for _ in range(4):
            print("Goes forward")
            motor_x.forward(5)
            print("Stopped")
            print("Goes backward")
            motor_x.backward(5)
            print("Stopped")


if __name__ == "__main__":
    test()
