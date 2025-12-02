
from .main import launch_matching_config
from aqt import mw
from aqt.qt import QAction

def on_load():
    action = QAction("Match Anki Game", mw)
    action.triggered.connect(launch_matching_config)
    mw.form.menuTools.addAction(action)

on_load()
