#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO

class GpioManager(object):
    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        return self
    def __exit__(exc_type, exc_val, exc_tb):
        GPIO.cleanup()
        return False

class BoundedStepperMotor(object):
    def __init__(self, pin_en, pin_dir, pin_stp, pin_b0, pin_b1, freq=100, dc=0.5):
        self.pins = [pin_en, pin_dir, pin_stp]
        self.bounds = [pin_b0, pin_b1]
        self.default_freq = freq
        self.default_dc = dc
        self.reset()

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
        def stop_pwm(chan):
            p.stop()
        GPIO.add_event_detect(self.bounds[0], GPIO.RISING, callback=stop_pwm,
                              bouncetime=200)
        GPIO.add_event_detect(self.bounds[1], GPIO.RISING, callback=stop_pwm,
                              bouncetime=200)
        p.start(real_dc * 100) # GPIO.PWM use dc from 0 to 100
        time.sleep(duration)
        p.stop()
        GPIO.remove_event_detect(self.bounds[0])
        GPIO.remove_event_detect(self.bounds[1])

    def forward(self, duration, freq=None, dc=None):
        self.drive(duration, freq, dc, True)

    def backward(self, duration, freq=None, dc=None):
        self.drive(duration, freq, dc, False)

def main():
    conf = {
     "motorx": {
         "EN": 4,
         "DIR": 2,
         "STP": 3,
     },
     "motory": {
         "EN": 11,
         "DIR": 10,
         "STP": 9,
     }
    }
    #motorx = StepperMotor(conf["motorx"]["EN"], conf["motorx"]["DIR"], conf["motorx"]["STP"])
    motor_x = StepperMotor(4, 2, 3)
    motor_y = StepperMotor(11, 10, 9)
    for _ in range(3):
        motor_x.forward(1)
        motor_y.backward(1)
        motor_x.backward(1)
        motor_y.forward(1)
    #motor_y.forward(1)
    #motor_x.forward(1)
    #motor_x.backward(1)
    #motor_y = StepperMotor(conf["motory"]["EN"], conf["motory"]["DIR"], conf["motory"]["STP"])
    GPIO.cleanup()

if __name__ == "__main__":
    main()
