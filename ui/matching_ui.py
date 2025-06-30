
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSizePolicy, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import random

class MatchingExam(QWidget):
    def __init__(self, all_data, page_size=5):
        super().__init__()
        self.setWindowTitle("Matching Game")
        self.all_data = all_data
        self.page_size = page_size
        self.current_page = 0
        self.correct_total = 0
        self.wrong_total = 0
        self.matched_pairs = set()
        self.selected_vocab = None
        self.selected_meaning = None
        self.vocab_buttons = {}
        self.meaning_buttons = {}
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        title = QLabel("Match the words with their meanings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.layout.addWidget(title)

        # Hiển thị thông tin số trang
        self.page_info = QLabel()
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_info.setFont(QFont("Arial", 11))
        self.layout.addWidget(self.page_info)

        self.timer_label = QLabel("⏳ Thời gian: 02:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.timer_label)

        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        self.status_label = QLabel("Select a word and a meaning to match.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.next_button = QPushButton("Next Page")
        self.next_button.clicked.connect(self.next_page)
        button_layout.addWidget(self.next_button)

        self.result_button = QPushButton("Tổng hợp kết quả")
        self.result_button.clicked.connect(self.show_summary)
        button_layout.addWidget(self.result_button)

        self.exit_button = QPushButton("Thoát")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)

        self.layout.addLayout(button_layout)
        self.load_page()

    def start_timer(self):
        self.time_remaining = 120  # 2 phút
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        self.update_timer()

    def update_timer(self):
        if self.time_remaining <= 0:
            self.timer.stop()
            self.status_label.setText("⏰ Hết giờ! Không thể ghép tiếp.")
            for btn in self.vocab_buttons.values():
                btn.setEnabled(False)
            for btn in self.meaning_buttons.values():
                btn.setEnabled(False)
        else:
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_label.setText(f"⏳ Thời gian: {minutes:02}:{seconds:02}")
            self.time_remaining -= 1
    def load_page(self):
        total_pages = (len(self.all_data) + self.page_size - 1) // self.page_size
        self.page_info.setText(f"Page {self.current_page + 1} of {total_pages}")
        if hasattr(self, "timer"):
            self.timer.stop()
        self.start_timer()
        self.clear_grid()
        self.selected_vocab = None
        self.selected_meaning = None
        self.vocab_buttons = {}
        self.meaning_buttons = {}
        start = self.current_page * self.page_size
        end = start + self.page_size
        self.page_data = self.all_data[start:end]
        if not self.page_data:
            QMessageBox.information(self, "Hết dữ liệu", "Không còn cặp nào để hiển thị.")
            return

        self.correct_pairs = {v: m for v, m in self.page_data}
        vocabs = list(self.correct_pairs.keys())
        meanings = list(self.correct_pairs.values())
        random.shuffle(vocabs)
        random.shuffle(meanings)

        for i, vocab in enumerate(vocabs):
            btn = QPushButton(vocab)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _, v=vocab: self.select_vocab(v))
            self.vocab_buttons[vocab] = btn
            self.grid.addWidget(btn, i, 0)

        for i, meaning in enumerate(meanings):
            btn = QPushButton(meaning)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _, m=meaning: self.select_meaning(m))
            self.meaning_buttons[meaning] = btn
            self.grid.addWidget(btn, i, 1)

    def clear_grid(self):
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def select_vocab(self, vocab):
        self.selected_vocab = vocab
        self.status_label.setText(f"Selected word: {vocab}")
        self.check_match()

    def select_meaning(self, meaning):
        self.selected_meaning = meaning
        self.status_label.setText(f"Selected meaning: {meaning}")
        self.check_match()

    def check_match(self):
        if self.selected_vocab and self.selected_meaning:
            correct_meaning = self.correct_pairs.get(self.selected_vocab)
            if correct_meaning == self.selected_meaning:
                self.vocab_buttons[self.selected_vocab].setStyleSheet("background-color: lightgreen;")
                self.meaning_buttons[self.selected_meaning].setStyleSheet("background-color: lightgreen;")
                self.vocab_buttons[self.selected_vocab].setEnabled(False)
                self.meaning_buttons[self.selected_meaning].setEnabled(False)
                self.correct_total += 1
                self.status_label.setText("✅ Đúng!")
            else:
                self.vocab_buttons[self.selected_vocab].setStyleSheet("background-color: lightcoral;")
                self.meaning_buttons[self.selected_meaning].setStyleSheet("background-color: lightcoral;")
                self.wrong_total += 1
                self.status_label.setText("❌ Sai rồi, thử lại nhé!")

            self.selected_vocab = None
            self.selected_meaning = None

    def next_page(self):
        self.current_page += 1
        self.load_page()

    def show_summary(self):
        total = self.correct_total + self.wrong_total
        accuracy = round((self.correct_total / total) * 100, 2) if total > 0 else 0
        QMessageBox.information(self, "Kết quả",
            f"Tổng số cặp đã làm: {total}\n"
            f"Số đúng: {self.correct_total}\n"
            f"Số sai: {self.wrong_total}\n"
            f"Tỷ lệ chính xác: {accuracy}%")
