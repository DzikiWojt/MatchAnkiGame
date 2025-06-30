from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QHBoxLayout, QSpinBox
)
from aqt import mw
from .matching_ui import MatchingExam
import random
class ExamCreatorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.deck_selector = QComboBox()
        self.note_type_selector = QComboBox()
        self.vocab_field_selector = QComboBox()
        self.meaning_field_selector = QComboBox()
        self.word_count_box = QSpinBox()
        self.word_count_box.setRange(3, 50)
        self.word_count_box.setValue(5)
        self.deck_selector.currentIndexChanged.connect(self.update_note_types)
        self.note_type_selector.currentIndexChanged.connect(self.update_fields)
        layout.addWidget(QLabel("Chọn Deck (bao gồm cả subdeck):"))
        layout.addWidget(self.deck_selector)
        layout.addWidget(QLabel("Chọn Note Type:"))
        layout.addWidget(self.note_type_selector)
        layout.addWidget(QLabel("Chọn trường chứa Từ (Vocabulary):"))
        layout.addWidget(self.vocab_field_selector)
        layout.addWidget(QLabel("Chọn trường chứa Nghĩa (Meaning):"))
        layout.addWidget(self.meaning_field_selector)
        layout.addWidget(QLabel("Số lượng từ mỗi trang:"))
        layout.addWidget(self.word_count_box)
        btn_layout = QHBoxLayout()
        self.start_button = QPushButton("Bắt đầu kiểm tra")
        self.start_button.clicked.connect(self.start_exam)
        btn_layout.addWidget(self.start_button)
        self.exit_button = QPushButton("Thoát")
        self.exit_button.clicked.connect(lambda: (mw.matching_config_win.close(), setattr(mw, "matching_config_win", None)))
        btn_layout.addWidget(self.exit_button)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_decks()
    def load_decks(self):
        self.deck_selector.clear()
        decks = mw.col.decks.all_names_and_ids()
        for deck in decks:
            self.deck_selector.addItem(deck.name, deck.id)
    def update_note_types(self):
        self.note_type_selector.clear()
        deck_name = self.deck_selector.currentText()
        cids = mw.col.find_cards(f'deck:"{deck_name}"')
        nids = list(set(mw.col.db.list("select nid from cards where id in %s" % str(tuple(cids))))) if cids else []
        nt_ids = set()
        if nids:
            q = "select mid from notes where id in " + str(tuple(nids)) if len(nids) > 1 else f"select mid from notes where id = ({nids[0]})"
            nt_ids = set(mw.col.db.list(q))
        for ntid in nt_ids:
            nt = mw.col.models.get(ntid)
            if nt:
                self.note_type_selector.addItem(nt["name"], ntid)
    def update_fields(self):
        self.vocab_field_selector.clear()
        self.meaning_field_selector.clear()
        ntid = self.note_type_selector.currentData()
        model = mw.col.models.get(ntid)
        if model:
            fields = [f["name"] for f in model["flds"]]
            self.vocab_field_selector.addItems(fields)
            self.meaning_field_selector.addItems(fields)
    def start_exam(self):
        deck_name = self.deck_selector.currentText()
        note_type_id = self.note_type_selector.currentData()
        vocab_field = self.vocab_field_selector.currentText()
        meaning_field = self.meaning_field_selector.currentText()
        if not deck_name or not note_type_id or not vocab_field or not meaning_field:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn đầy đủ tất cả các trường.")
            return
        query = f'deck:"{deck_name}"'
        cids = mw.col.find_cards(query)
        notes = []
        for cid in cids:
            nid = mw.col.db.scalar("select nid from cards where id = ?", cid)
            note = mw.col.get_note(nid)
            if note.mid == note_type_id:
                vocab = note[vocab_field]
                meaning = note[meaning_field]
                if vocab and meaning:
                    notes.append((vocab, meaning))
        if len(notes) < 1:
            QMessageBox.information(self, "Không đủ dữ liệu", "Không tìm thấy cặp từ-nghĩa hợp lệ.")
            return
        random.shuffle(notes)
        win = MatchingExam(notes, page_size=self.word_count_box.value())
        win.setMinimumSize(600, 400)
        win.show()
