#!/usr/bin/env python3
# coding: utf8

import driver
import json
import argparse


def calibrate(output_fn):
    with open(output_fn, "w", encoding="utf8") as f:
        data = json.load(f)
    with driver.GpioManager() as _:
        devices = data["devices"]
        motor_x = driver.BoundedStepperMotor(*devices["motor_x"])
        motor_y = driver.BoundedStepperMotor(*devices["motor_y"])
        motor_z = driver.BoundedStepperMotor(*devices["motor_z"])
        freq = 1000
        x_data = motor_x.calibrate(freq)
        y_data = motor_y.calibrate(freq)
        z_data = motor_z.calibrate(freq)
        with open(output_fn, "w", encoding="utf8") as f:
            data["motor_x"] = x_data
            data["motor_y"] = y_data
            data["motor_z"] = z_data
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("CONFIG_FILE", help="Config file name")
    args = parser.parse_args()

    calibrate(args.CONFIG_FILE)
