
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QSizePolicy, QHBoxLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import random
import time
from .animated_button import AnimatedButton
from collections.abc import Sequence
from aqt import mw, AnkiQt
from aqt.utils import showWarning
from aqt.operations import CollectionOp
from anki.collection import OpChanges
from anki.consts import QUEUE_TYPE_REV  # 2 == Review
from anki.cards import CardId
from anki.scheduler.v3 import CardAnswer

from . import anki_media


class MatchingExam(QWidget):
    def __init__(self, all_data, page_size=5, columns=3, anim="fade", animtime=0.5, update_stats=False, font_size=18):
        super().__init__()
        self.setWindowTitle("Match Anki Game")
        self.all_data = all_data
        self.page_size = page_size
        self.columns = columns
        self.anim = anim
        self.animtime = animtime
        self.update_stats = update_stats
        self.font_size = font_size
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

        # Display page number
        self.page_info = QLabel()
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_info.setFont(QFont("Arial", 11))
        self.layout.addWidget(self.page_info)

        # Display Time
        self.timer_label = QLabel("⏳ Time: 02:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.timer_label)

        # Grid start
        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        # Display Current Status Text
        self.status_label = QLabel("Select a word and a meaning to match.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Display Summary Bar
        result_frame = QFrame()     # create contener for visual frame of summary bar
        result_frame.setStyleSheet("QFrame { border: 2px solid #555; border-radius: 5px; margin: 1px; }")   # border of summary bar

        result_layout = QHBoxLayout(result_frame)

        self.summary_pairs = QLabel("Tries: 0")
        self.summary_pairs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_pairs.setStyleSheet("QLabel { border: none; }")  # Remove border. Or do like this:    border: 0px solid transparent;
        result_layout.addWidget(self.summary_pairs)

        result_layout.addWidget(self.create_v_separator())

        self.summary_correct = QLabel("Correct: 0")
        self.summary_correct.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_correct.setStyleSheet("QLabel { border: none; }")  # Remove border. Or do like this:    border: 0px solid transparent;
        result_layout.addWidget(self.summary_correct)

        result_layout.addWidget(self.create_v_separator())

        self.summary_wrong = QLabel("Wrong: 0")
        self.summary_wrong.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_wrong.setStyleSheet("QLabel { border: none; }")  # Remove border. Or do like this:    border: 0px solid transparent;
        result_layout.addWidget(self.summary_wrong)

        result_layout.addWidget(self.create_v_separator())

        self.summary_accuracy = QLabel("Accuracy: 0%")
        self.summary_accuracy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_accuracy.setStyleSheet("QLabel { border: none; }")  # Remove border. Or do like this:    border: 0px solid transparent;
        result_layout.addWidget(self.summary_accuracy)

        self.layout.addWidget(result_frame)
        self.update_summary()

        # Button: Next Page
        button_layout = QHBoxLayout()
        self.next_button = QPushButton("Next Page")
        self.next_button.clicked.connect(self.next_page)
        button_layout.addWidget(self.next_button)
        self.next_button.setStyleSheet("""
            QPushButton {
                font-size: 16pt; 
                padding: 10px 20px 10px 20px; 
            }
        """)

        # Button: Exit
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)
        self.exit_button.setStyleSheet("""
            QPushButton {
                font-size: 16pt; 
                padding: 10px 20px 10px 20px; 
            }
        """)

        self.layout.addLayout(button_layout)
        self.load_page()

    # Create Vertical Separator
    def create_v_separator(self):
        separator = QFrame()
        separator.setFixedWidth(2)
        # Opcjonalnie: ustaw kolor linii za pomocą CSS (lub QPalette)
        separator.setStyleSheet("QFrame { background-color: #aaa; }")
        return separator

    def start_timer(self):
        self.time_remaining = 120  # 2 phút
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        self.update_timer()

    def update_timer(self):
        if self.time_remaining <= 0:
            self.timer.stop()
            self.status_label.setText("⏰ Time's up! You can't continue matching.")
            for btn in self.vocab_buttons.values():
                btn.setEnabled(False)
            for btn in self.meaning_buttons.values():
                btn.setEnabled(False)
        else:
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_label.setText(f"⏳ Time: {minutes:02}:{seconds:02}")
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
            QMessageBox.information(self, "No data left", "No more pairs to display.")
            return

        tiles_number = self.page_size * 2
        tiles = random.sample(range(0, tiles_number), tiles_number)

        self.correct_pairs = {v: (m, audio, cid) for v, m, audio, cid in self.page_data}
        vocabs = [v for v, m, audio, cid in self.page_data]
        meanings = [m for v, m, audio, cid in self.page_data]
        random.shuffle(vocabs)
        random.shuffle(meanings)

        tile_pos = 0
        tile_rand = 0

        for i, vocab in enumerate(vocabs):
            btn = AnimatedButton(vocab, self.anim, self.animtime, self.font_size)
            btn.clicked.connect(lambda _, v=vocab: self.select_vocab(v))
            self.vocab_buttons[vocab] = btn
            tile_rand = tiles[tile_pos]
            col = tile_rand % self.columns
            row = tile_rand // self.columns
            tile_pos += 1
            self.grid.addWidget(btn, row, col)

        for i, meaning in enumerate(meanings):
            btn = AnimatedButton(meaning, self.anim, self.animtime, self.font_size)
            btn.clicked.connect(lambda _, m=meaning: self.select_meaning(m))
            self.meaning_buttons[meaning] = btn
            tile_rand = tiles[tile_pos]
            col = tile_rand % self.columns
            row = tile_rand // self.columns
            tile_pos += 1
            self.grid.addWidget(btn, row, col)

        max_tile_width = self.find_max_button_width(self.grid)
        self.set_uniform_column_width(self.grid, max_tile_width, self.columns)


    def find_max_button_width(self, grid_layout):
        max_width = 0

        # All grid elements
        for i in range(grid_layout.count()):
            item = grid_layout.itemAt(i)

            # If the grid element is widget (button)...
            if item and item.widget():
                widget = item.widget()

                # Enforce size based on text
                width = widget.sizeHint().width()

                if width > max_width:
                    max_width = width

        return max_width

    def set_uniform_column_width(self, grid_layout, max_width, num_columns):
        # Add a little padding to text
        target_width = max_width + 10

        # Setup minimum width for every column
        for col in range(num_columns):
            grid_layout.setColumnMinimumWidth(col, target_width)

            # setting Stretch to 0, keep column no extending, keeping them on minimum width
            grid_layout.setColumnStretch(col, 0)

    def clear_grid(self):
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def next_page(self):
        self.current_page += 1
        self.load_page()

    def update_summary(self):
        total = self.correct_total + self.wrong_total
        accuracy = round((self.correct_total / total) * 100, 2) if total > 0 else 0

        self.summary_pairs.setText(f"⏰ Tries: {total}")
        self.summary_correct.setText(f"✅ Correct: {self.correct_total}")
        self.summary_wrong.setText(f"❌ Wrong: {self.wrong_total}")
        self.summary_accuracy.setText(f"🎯 Accuracy: {accuracy}%")

    def select_vocab(self, vocab):
        #if self.selected_vocab == vocab:
        if self.selected_vocab != None and self.vocab_buttons[vocab].isChecked():
            self.vocab_buttons[self.selected_vocab].setChecked(False)  # Unselect Button
            self.selected_vocab = None
            return

        if self.selected_vocab != None:
            self.selection_wrong(self.vocab_buttons[self.selected_vocab], self.vocab_buttons[vocab])
            return

        self.selected_vocab = vocab
        self.status_label.setText(f"Selected word: {vocab}")

        self.vocab_buttons[self.selected_vocab].setChecked(True)    # Select Button

        self.check_match()

    def select_meaning(self, meaning):
        #if self.selected_meaning == meaning:
        if self.selected_meaning != None and self.meaning_buttons[meaning].isChecked():
            self.meaning_buttons[self.selected_meaning].setChecked(False)  # Unselect Button
            self.selected_meaning = None
            return

        if self.selected_meaning != None:
            self.selection_wrong(self.meaning_buttons[self.selected_meaning], self.meaning_buttons[meaning])
            return


        self.selected_meaning = meaning
        self.status_label.setText(f"Selected meaning: {meaning}")

        self.meaning_buttons[self.selected_meaning].setChecked(True)   # Select Button

        self.check_match()

    def check_match(self):
        if self.selected_vocab and self.selected_meaning:
            # correct_meaning has meaning and cid
            correct_meaning, audio_content, card_id = self.correct_pairs.get(self.selected_vocab)
            #correct_meaning = self.correct_pairs.get(self.selected_vocab)
            if correct_meaning == self.selected_meaning:
                self.vocab_buttons[self.selected_vocab].setStyleSheet("background-color: lightgreen;")
                self.meaning_buttons[self.selected_meaning].setStyleSheet("background-color: lightgreen;")
                self.vocab_buttons[self.selected_vocab].setEnabled(False)
                self.meaning_buttons[self.selected_meaning].setEnabled(False)
                self.correct_total += 1
                self.status_label.setText("✅ Correct!")
                self.vocab_buttons[self.selected_vocab].start_disappearing()
                self.meaning_buttons[self.selected_meaning].start_disappearing()

                self._update_card_progress(card_id)

                self.vocab_buttons[self.selected_vocab].setChecked(False)       # Unselect Button
                self.meaning_buttons[self.selected_meaning].setChecked(False)   # Unselect Button

                self.update_summary()

                # play audio file if exist
                anki_media.play_audio_from_card_field(audio_content)

            else:
                self.selection_wrong(self.vocab_buttons[self.selected_vocab], self.meaning_buttons[self.selected_meaning])

            self.selected_vocab = None
            self.selected_meaning = None

    def selection_wrong(self, btn1, btn2):
        self.wrong_total += 1
        self.status_label.setText("❌ Wrong, try again!")

        btn1.setChecked(False)  # Unselect Button
        btn2.setChecked(False)  # Unselect Button

        btn1.flash_color_overlay_two("lightcoral")
        btn2.flash_color_overlay_two("lightcoral")

        self.selected_vocab = None
        self.selected_meaning = None

        self.update_summary()


    # Update card progress (method should be upgraded !!)
    def _update_card_progress(self, card_id):
        if not self.update_stats:
            return

        CollectionOp(
            parent=self,
            op=lambda col: self._perform_card_update(card_id),
        ).success(
            lambda result: self._handle_update_success(result)
        ).failure(
            lambda error: self._handle_update_failure(error)
        ).run_in_background()

    def _handle_update_success(self, result):
        mw.reset()

    def _handle_update_failure(self, error):
        from aqt.utils import showWarning
        showWarning(f"Failed to update card status: {error}")

    def _perform_card_update(self, card_id):
        card = mw.col.get_card(card_id)
        if not card:
            return OpChanges()

        TIME_ELAPSED_SECONDS = 5
        REVLOG_GOOD_CODE = 2

        try:
            # Manually setup card as Review (queue=2)
            card.queue = QUEUE_TYPE_REV
            mw.col.update_card(card)

            # Refresh card object and setup time
            card = mw.col.get_card(card_id)
            card.timer_started = time.time() - TIME_ELAPSED_SECONDS

            # Review card
            mw.col.sched.answerCard(card, REVLOG_GOOD_CODE)

        except Exception as e:
            # In case of error (ex. when answerCard don't accept)
            raise e

        return OpChanges()
        
