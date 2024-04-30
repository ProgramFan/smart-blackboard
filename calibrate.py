#!/usr/bin/env python3
# coding: utf8

import driver
import json


def calibrate(output_fn):
    with driver.GpioManager() as _:
        motor_x = driver.BoundedStepperMotor(5, 3, 4, 6, 7)
        motor_y = driver.BoundedStepperMotor(12, 10, 11, 8, 9)
        freq = 1000
        x_data = motor_x.calibrate(freq)
        y_data = motor_y.calibrate(freq)
        with open(output_fn, "w", encoding="utf8") as f:
            json.dump({"motor_x": x_data, "motor_y": y_data}, f, indent=2)


if __name__ == "__main__":
    calibrate()
