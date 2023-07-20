
from driver import StepperMotor

x_motor = StepperMotor(5, 3, 4)
y_motor = StepperMotor(8, 6, 7)

def reset():
    x_motor.hold()
    y_motor.hold()

def manual_mode():
    x_motor.release()
    y_motor.release()

def x_forward():
    x_motor.go(1)

def x_backward():
    x_motor.go(-1)

def y_forward():
    y_motor.go(1)

def y_backward():
    y_motor.go(-1)

def clean_all():
    for _ in range(5):
        x_motor.go(12)
        x_motor.go(-12)
        y_motor.go(1)
    x_motor.go(12)
    x_motor.go(-12)
    y_motor.go(-5)
