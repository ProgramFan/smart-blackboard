from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QGridLayout, QWidget, QSizePolicy
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("QT Program")
        self.showFullScreen()

        widget = QWidget()
        layout = QGridLayout()

        buttons = [
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_BrowserReload)), "复位"),
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_DialogCloseButton)), "退出"),
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)), "手动"),
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_DriveHDIcon)), "模式1"),
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_DriveFDIcon)), "模式2"),
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_DriveCDIcon)), "模式3"),
            QPushButton(QIcon(QApplication.style().standardIcon(QStyle.SP_DriveDVDIcon)), "模式4")
        ]
        for button in buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        positions = [(i,j) for i in range(3) for j in range(3)]

        for position, button in zip(positions, buttons):
            if button is not None:
                layout.addWidget(button, *position)

        buttons[1].clicked.connect(self.close)  # Add this line to connect the "退出" button's clicked signal to the close slot

        widget.setLayout(layout)
        self.setCentralWidget(widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
