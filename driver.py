#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO

class StepperMotor(object):
    def __init__(self, pin_en, pin_dir, pin_stp):
        self.pins = [pin_en, pin_dir, pin_stp]
        for p in self.pins:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    def drive(self, duration, freq, dc, clockwise):
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH if clockwise else GPIO.LOW)
        p = GPIO.PWM(self.pins[2], freq)
        p.start(dc * 100) # GPIO.PWM use dc from 0 to 100
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
        p.start(0.5 * 100) # GPIO.PWM use dc from 0 to 100
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
