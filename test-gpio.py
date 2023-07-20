#!/usr/bin/env python3
# coding: utf-8

import RPi.GPIO as GPIO
import time

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    def collision_detected(channel):
        print("碰撞检测到!")
    try:
        GPIO.add_event_detect(4, GPIO.RISING, callback=collision_detected, bouncetime=200)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
