#!/usr/bin/env python3
# coding: utf8

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtWidgets import QGridLayout, QWidget, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize
import RPi.GPIO as GPIO
from driver import StepperMotor

import sys
import os
import json

class MainWindow(QMainWindow):

    def __init__(self, motor_spec):
        super(MainWindow, self).__init__()

        self.setWindowTitle("智能黑板擦控制程序")
        self.showFullScreen()

        widget = QWidget()
        layout = QGridLayout()

        buttons = [
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
                QIcon(QApplication.style().standardIcon(
                    QStyle.SP_DriveDVDIcon)), "快速"),
        ]

        font = QFont()
        font.setPixelSize(48)
        for button in buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setIconSize(QSize(48, 48))
            button.setFont(font)

        positions = [(i, j) for i in range(3) for j in range(3)]

        for position, button in zip(positions, buttons):                             
            if button is not None:
                layout.addWidget(button, *position)

        buttons[0].clicked.connect(self.reset)
        buttons[1].clicked.connect(self.close)
        buttons[2].clicked.connect(self.manual)
        buttons[3].clicked.connect(self.mode1)
        buttons[4].clicked.connect(self.mode2)
        buttons[5].clicked.connect(self.mode3)
        buttons[6].clicked.connect(self.mode4)
        buttons[7].clicked.connect(self.mode5)
        buttons[8].clicked.connect(self.mode6)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        with open(motor_spec, encoding="utf8") as f:
            self.motor_spec = json.load(f)

        self.motor_x = StepperMotor(5, 3, 4);
        self.motor_x_spec = self.motor_spec["motor_x"]
        self.motor_y = StepperMotor(8, 6, 7);
        self.motor_y_spec = self.motor_spec["motor_y"]
        self.nx = 12;
        self.ny = 5;
        self.reset()

    def go(self, direction, nsteps, reverse=False, speed=1):
        motor = self.motor_x if direction == "x" else self.motor_y
        motor_spec = self.motor_x_spec if direction == "x" else self.motor_y_spec
        nn = self.nx if direction == "x" else self.ny
        freq = 1000 * speed
        dc = 0.5
        clockwise = motor_spec["direction"]
        if reverse:
            clockwise = not clockwise
        duration = motor_spec["time"] * nsteps / nn * motor_spec["freq"] / freq
        motor.drive(duration, freq=freq, dc=dc, clockwise=clockwise)

    def reset(self):
        self.motor_x.hold()
        self.motor_y.hold()

    def manual(self):
        self.motor_x.release()
        self.motor_y.release()

    def mode1(self):
        self.go("x", 1, False)

    def mode2(self):
        self.go("x", 1, True)

    def mode3(self):
        self.go("y", 1, False)

    def mode4(self):
        self.go("y", 1, True)

    def mode5(self):
        for _ in range(self.ny):
            self.go("x", self.nx, False)
            self.go("x", self.nx, True)
            self.go("y", 1, False)
        self.go("x", self.nx, False)
        self.go("x", self.nx, True)
        self.go("y", self.ny, True)

    def mode6(self):
        pass


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    GPIO.setmode(GPIO.BCM)
    app = QApplication(sys.argv)
    window = MainWindow(os.path.join(SCRIPT_DIR, "motor_spec.json"))
    window.show()
    ret_code = app.exec_();
    GPIO.cleanup()
    sys.exit(ret_code)
