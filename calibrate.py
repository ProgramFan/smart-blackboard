#!/usr/bin/env python3
# coding: utf8

from driver import StepperMotor
import RPi.GPIO as GPIO
import json
import time


def calibrate(output_fn):
    motor_x = StepperMotor(5, 3, 4)
    motor_y = StepperMotor(8, 6, 7)
    x_data = motor_x.calibrate(500)
    y_data = motor_y.calibrate(500)
    with open(output_fn, "w", encoding="utf8") as f:
        json.dump({"motor_x": x_data, "motor_y": y_data}, f, indent=2)


def main():
    GPIO.setmode(GPIO.BCM)
    calibrate("motor_spec.json")
    GPIO.cleanup()

if __name__ == "__main__":
    main()
