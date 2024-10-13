from PyQt6.QtWidgets import QApplication
from src.main_window import *
import os

'''os.close(os.sys.stderr.fileno())'''
app = QApplication([])
window = MainWindow()
window.show()

app.exec()