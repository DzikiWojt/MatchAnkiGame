
from PyQt6.QtWidgets import QMainWindow
from aqt import mw
from .ui.exam_creator_tab import ExamCreatorTab

def launch_matching_config():
    mw.matching_config_win = QMainWindow()
    mw.matching_config_win.setWindowTitle("Matching Question Config")
    mw.matching_config_win.setCentralWidget(ExamCreatorTab())
    mw.matching_config_win.resize(400, 300)
    mw.matching_config_win.show()
