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
        motor_x = driver.BoundedStepperMotor(*devices["motor_x"]["pins"])
        motor_y = driver.BoundedStepperMotor(*devices["motor_y"]["pins"])
        motor_z = driver.StepperMotor(*devices["motor_z"]["pins"])
        x_data = motor_x.calibrate(1000, devices["motor_x"]["length"])
        y_data = motor_y.calibrate(1000, devices["motor_y"]["length"])
        z_data = motor_z.calibrate(4000, devices["motor_y"]["length"])
        if x_data["swap_bounds"]:
            pins = devices["motor_x"]["pins"]
            pins[-2], pins[-1] = pins[-1], pins[-2]
        del x_data["swap_bounds"]
        if y_data["swap_bounds"]:
            pins = devices["motor_y"]["pins"]
            pins[-2], pins[-1] = pins[-1], pins[-2]
        del y_data["swap_bounds"]
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
