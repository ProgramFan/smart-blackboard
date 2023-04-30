#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO

def soft_pwm(pin, freq, dc, duration):
    """Generate a soft PWM on specified pin. This is blocking so only one PWM
    can be generated at the same time. If you want to output multiple PWMs,
    use GPIO.PWM instead.
    """
    GPIO.output(pin, GPIO.LOW)
    period = 1 / freq
    req_on = period * dc
    req_off = period - req_on
    nsteps = duration * freq
    for _ in range(nsteps):
        if req_on > 0:
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(req_on)
        if req_off > 0:
            GPIO.output(pin, GPIO.LOW)
            time.sleep(req_off)
    GPIO.output(pin, GPIO.LOW)


class StepperMotor(object):
    def __init__(self, pin_en, pin_dir, pin_stp):
        self.pins = [pin_en, pin_dir, pin_stp]
        for p in self.pins:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

    def _drive(self, freq, dc, duration, clockwise):
        GPIO.output(self.pins[0], GPIO.HIGH)
        GPIO.output(self.pins[1], GPIO.HIGH if clockwise else GPIO.LOW)
        p = GPIO.PWM(self.pins[2], freq)
        p.start(dc * 100) # GPIO.PWM use dc from 0 to 100
        time.sleep(duration)
        p.stop()

    def forward(self, duration, freq=100, dc=0.5):
        self._drive(freq, dc, duration, True)

    def backward(self, duration, freq=100, dc=0.5):
        self._drive(freq, dc, duration, False)

def main():
    GPIO.setmode(GPIO.BCM)
    conf = {
     "motor0": {
         "EN": 19,
         "DIR": 6,
         "STP": 13,
     }
    }
    motor0 = StepperMotor(conf["motor0"]["EN"], conf["motor0"]["DIR"], conf["motor0"]["STP"])
    motor0.forward(5)
    motor0.backward(5)
    GPIO.cleanup()

if __name__ == "__main__":
    main()
