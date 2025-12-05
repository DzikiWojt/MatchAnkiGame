
from PyQt6.QtWidgets import QMainWindow
from aqt import mw
from .ui.exam_creator_tab import ExamCreatorTab

from .translation import tr


def launch_matching_config():
    mw.matching_config_win = QMainWindow()
    mw.matching_config_win.setWindowTitle(tr("window_title_config"))
    mw.matching_config_win.setCentralWidget(ExamCreatorTab())
    mw.matching_config_win.resize(600, 450)
    mw.matching_config_win.show()
