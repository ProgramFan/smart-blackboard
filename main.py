#!/usr/bin/env python3
# coding: utf8
"""Main Application for smart blackboard"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtWidgets import QGridLayout, QWidget, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize
from RPi import GPIO

from driver import BoundedStepperMotor, StepperMotor, Pump
from voice_model import VoiceCmdModel
import audio_utils

import sys
import os
import json
import argparse
import time


class MainWindow(QMainWindow):
    """The main window"""

    def __init__(self, motor_spec, model_spec, fullscreen=True):
        super().__init__()

        self.setWindowTitle("智能黑板擦控制程序")
        if fullscreen:
            self.showFullScreen()

        widget = QWidget()
        layout = QGridLayout()

        self.buttons = [
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_BrowserReload)), "复位"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DialogCloseButton)), "退出"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_FileDialogDetailedView)), "手动"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DriveDVDIcon)), "X前进"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DriveDVDIcon)), "X后退"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DriveDVDIcon)), "Y前进"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DriveDVDIcon)), "Y后退"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DriveDVDIcon)), "洁净"),
            QPushButton(
                QIcon(QApplication.style().standardIcon(QStyle.SP_MediaPlay)),
                "语音"),
        ]

        font = QFont()
        font.setPixelSize(60)
        for button in self.buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setIconSize(QSize(60, 60))
            button.setFont(font)

        positions = [(i, j) for i in range(3) for j in range(3)]

        for position, button in zip(positions, self.buttons):
            if button is not None:
                layout.addWidget(button, *position)

        self.buttons[0].clicked.connect(self.reset)
        self.buttons[1].clicked.connect(self.close)
        self.buttons[2].clicked.connect(self.manual)
        self.buttons[3].clicked.connect(self.go_right)
        self.buttons[4].clicked.connect(self.go_left)
        self.buttons[5].clicked.connect(self.go_up)
        self.buttons[6].clicked.connect(self.go_down)
        self.buttons[7].clicked.connect(self.full_clean)
        self.buttons[8].clicked.connect(self.voice_control)

        self.cmd_cn = {
            "__noise__": "噪音",
            "up": "向上",
            "down": "向下",
            "left": "向左",
            "right": "向右",
            "go": "全擦",
            "stop": "停止",
        }

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # initialize voice command model
        with open(model_spec, encoding="utf8") as f:
            model_conf = json.load(f)
        self.model = VoiceCmdModel(model_conf["fn"], model_conf["sr"],
                                   model_conf["duration"],
                                   model_conf["feature"], **model_conf["args"])
        self.voice_device = audio_utils.select_input_device()[0]
        self.voice_duration = model_conf["duration"]

        # initialize motors
        with open(motor_spec, encoding="utf8") as f:
            motor_conf = json.load(f)
        devices = motor_conf["devices"]
        self.pump = Pump(devices["pump"]["pin"])
        self.motors = {}
        self.specs = {}
        self.motors["x"] = BoundedStepperMotor(*devices["motor_x"]["pins"])
        self.motors["y"] = BoundedStepperMotor(*devices["motor_y"]["pins"])
        self.motors["z"] = StepperMotor(*devices["motor_z"]["pins"])
        self.specs["x"] = motor_conf["motor_x"]
        self.specs["y"] = motor_conf["motor_y"]
        self.specs["z"] = motor_conf["motor_z"]
        self.dx = 0.1  # 0.1m per step on x
        self.dy = 0.1  # 0.1m per step on y
        self.dz = 0.01  # 0.01m per step on z
        self.ny = int(devices["motor_x"]["length"] / self.dy)
        self.manual()

    def drive_motor(self, motor, length, forward=True, speed_mul=1.0):
        speed = self.specs[motor]["speed"] * speed_mul  # increase speed
        freq = self.specs[motor]["freq"] * speed_mul  # by increase freq
        clockwise = self.specs[motor]["clockwise"]
        if not forward:
            clockwise = not clockwise
        duration = length / speed
        self.motors[motor].drive(duration,
                                 freq=freq,
                                 dc=0.5,
                                 clockwise=clockwise)

    def go(self, direction, nsteps, reverse=False, speed_mul=1.0):
        if direction == "x":
            self.drive_motor("x", self.dx * nsteps, not reverse, speed_mul)
        elif direction == "y":
            self.drive_motor("y", self.dy * nsteps, not reverse, speed_mul)
        else:
            self.drive_motor("z", self.dz * nsteps, not reverse, speed_mul)

    def reset(self):
        self.motors["x"].hold()
        self.motors["y"].hold()
        self.motors["z"].hold()
        # Go to left bottom corner and ready cleaner
        self.go("x", 100, reverse=True)
        self.go("y", 100, reverse=True)
        self.go("z", 2)

    def manual(self):
        self.go("z", 2, reverse=True)
        self.motors["x"].release()
        self.motors["y"].release()
        self.motors["z"].release()

    def go_right(self):
        self.go("x", 1)

    def go_left(self):
        self.go("x", 1, reverse=True)

    def go_up(self):
        self.go("y", 1)

    def go_down(self):
        self.go("y", 1, reverse=True)

    def full_clean(self):
        self.reset()
        for _ in range(self.ny):
            self.pump.on()
            time.sleep(0.5)
            self.pump.off()
            self.go("x", 100)
            self.go("x", 100, reverse=True)
            self.go("y", 1)
        self.pump.on()
        time.sleep(0.5)
        self.pump.off()
        self.go("x", 100)
        self.go("x", 100, reverse=True)
        self.go("y", 100, reverse=True)

    def voice_control(self):
        try:
            while True:
                self.buttons[8].setIcon(
                    QIcon(QApplication.style().standardIcon(
                        QStyle.SP_MediaPause)))
                self.buttons[8].setText("请发令")
                self.buttons[8].repaint()
                time.sleep(0.2)
                data = audio_utils.record_voice(self.voice_device[0],
                                                self.voice_duration,
                                                self.voice_device[2],
                                                downsample=False)
                self.buttons[8].setIcon(
                    QIcon(QApplication.style().standardIcon(
                        QStyle.SP_MediaPlay)))
                self.buttons[8].setText("解析中")
                self.buttons[8].repaint()
                result = self.model.predict(data, self.voice_device[2])
                print("Probability:")
                for k, v in result["details"].items():
                    print(f"  {k}: {v*100:.3f}%")
                print(f"Voice command: {result['command']}")
                cmd = result["command"]
                self.buttons[8].setText(self.cmd_cn[cmd])
                self.buttons[8].repaint()
                if result["details"][cmd] <= 0.8:
                    continue
                if cmd == "__noise__":
                    continue
                elif cmd == "go":
                    self.full_clean()
                elif cmd == "stop":
                    self.buttons[8].setText("语音")
                    self.buttons[8].repaint()
                    break
                elif cmd == "up":
                    self.go_up()
                elif cmd == "down":
                    self.go_down()
                elif cmd == "left":
                    self.go_left()
                elif cmd == "right":
                    self.go_right()
        except KeyboardInterrupt:
            return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullscreen",
                        action="store_true",
                        help="start app in fullscreen mode")
    args = parser.parse_args()

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    GPIO.setmode(GPIO.BCM)
    app = QApplication(sys.argv)
    window = MainWindow(os.path.join(SCRIPT_DIR, "motor_spec.json"),
                        os.path.join(SCRIPT_DIR, "model_spec.json"),
                        args.fullscreen)
    window.show()
    ret_code = app.exec_()
    GPIO.cleanup()
    sys.exit(ret_code)


if __name__ == "__main__":
    main()
