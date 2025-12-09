
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QHBoxLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont, QColor
import random
from .animated_button import AnimatedButton
from aqt import gui_hooks
from aqt.utils import showWarning
from aqt.qt import QTimer
from aqt.sound import av_player

from . import anki_media
from ..grade_now import grade_now
from ..translation import tr
from ..clockdown_manager import ClockdownManager
from ..timer_manager import TimerManager
from ..enums import TimekeepingMode


class MatchingExam(QWidget):
    def __init__(self, all_data, page_size=5, columns=3, anim="fade", animtime=0.5, update_stats=False, font_size=18, timekeeping_mode=TimekeepingMode.TIME_INFORMATIONAL, timekeeping_time=QTime()):
        super().__init__()
        self.setWindowTitle(tr("window_title_game"))
        self.all_data = all_data
        self.page_size = page_size
        self.columns = columns
        self.anim = anim
        self.animtime = animtime
        self.update_stats = update_stats
        self.font_size = font_size
        self.timekeeping_mode = timekeeping_mode
        self.timekeeping_time = timekeeping_time
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

        # Header layout: Title & Sound Icon
        BUTTON_SOUND_SIZE_DEFAULT = "30"
        BUTTON_SOUND_SIZE_HOVER = "34"

        header_layout = QGridLayout()

        title = QLabel(tr("game_title_on_top"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        self.corner_button_sound = QPushButton("🔈")
        self.corner_button_sound.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
                text-align: left;
                font-size: {BUTTON_SOUND_SIZE_DEFAULT}px;
            }}
            QPushButton:hover {{
                font-size: {BUTTON_SOUND_SIZE_HOVER}px;
            }}
        """)

        self.corner_button_sound.setFixedWidth(50)
        self.corner_button_sound.clicked.connect(self.corner_button_sound_clicked)

        # add title to span on 3 columns (from 0 to 2)
        # so it's center will be center of whole window
        # addWidget(widget, row, col, rowSpan, colSpan, alignment)
        header_layout.addWidget(title, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.corner_button_sound, 0, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.layout.addLayout(header_layout)

        # Display page number
        self.page_info = QLabel()
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_info.setFont(QFont("Arial", 11))
        self.layout.addWidget(self.page_info)

        # Display Time
        self.font_size_clock_small : int = 12
        self.font_size_clock_big : int = 15

        self.timer_bar = QHBoxLayout()
        # Clock Small (per page)
        self.timer_per_page_icon = QLabel("⏳")
        self.change_label_font_size(self.timer_per_page_icon, self.font_size_clock_small)
        self.timer_per_page_label = QLabel(tr("game_timer_per_page"))
        self.change_label_font_size(self.timer_per_page_label, self.font_size_clock_small)
        # Clock Big (for all cards)
        self.timer_for_all_cards_icon = QLabel("⏳")
        self.change_label_font_size(self.timer_for_all_cards_icon, self.font_size_clock_big)
        self.timer_for_all_cards_label = QLabel(tr("game_timer_for_all_cards"))
        self.change_label_font_size(self.timer_for_all_cards_label, self.font_size_clock_big)

        self.timer_bar.addStretch(1)
        self.timer_bar.addWidget(self.timer_per_page_icon)
        self.timer_bar.addWidget(self.timer_per_page_label)
        self.timer_bar.addSpacing(120)
        self.timer_bar.addWidget(self.timer_for_all_cards_icon)
        self.timer_bar.addWidget(self.timer_for_all_cards_label)
        self.timer_bar.addStretch(1)
        self.layout.addLayout(self.timer_bar)

        ICON_RED_DOWN_ARROW_HTML_BIG = f'<span style="color: red; font-size: {self.font_size_clock_big}px;">▼</span>'
        ICON_RED_DOWN_ARROW_HTML_SMALL = f'<span style="color: red; font-size: {self.font_size_clock_small}px;">▼</span>'
        icons_clock_red_down_arrow_html_text_big = f"⏳ {ICON_RED_DOWN_ARROW_HTML_BIG}"
        icons_clock_red_down_arrow_html_text_small = f"⏳ {ICON_RED_DOWN_ARROW_HTML_SMALL}"
        ICON_GREEN_UP_ARROW_HTML_BIG = f'<span style="color: green; font-size: {self.font_size_clock_big}px;">▲</span>'
        ICON_GREEN_UP_ARROW_HTML_SMALL = f'<span style="color: green; font-size: {self.font_size_clock_small}px;">▲</span>'
        icons_clock_green_up_arrow_html_text_big = f"⏳ {ICON_GREEN_UP_ARROW_HTML_BIG}"
        icons_clock_green_up_arrow_html_text_small = f"⏳ {ICON_GREEN_UP_ARROW_HTML_SMALL}"

        match self.timekeeping_mode:
            case TimekeepingMode.COUNTDOWN_FOR_ALL_CARDS:
                # Timer per page
                self.timer_manager_per_page = TimerManager(self.timer_per_page_label)
                self.timer_per_page_icon.setText(icons_clock_green_up_arrow_html_text_small)
                self.timer_per_page_icon.setToolTip(tr("game_timer_per_page_tooltip"))
                self.timer_per_page_label.setToolTip(tr("game_timer_per_page_tooltip"))
                # Countdown for all cards
                self.clockdown_manager_for_all_cards = ClockdownManager(self.timekeeping_time, self.timer_for_all_cards_label)
                self.clockdown_manager_for_all_cards.timeout_finished.connect(self.clockdown_finish_for_all_cards)
                self.clockdown_manager_for_all_cards.start_clockdown()
                self.timer_for_all_cards_icon.setText(icons_clock_red_down_arrow_html_text_big)
                self.timer_for_all_cards_icon.setToolTip(tr("game_countdown_for_all_cards_tooltip"))
                self.timer_for_all_cards_label.setToolTip(tr("game_countdown_for_all_cards_tooltip"))
            case TimekeepingMode.COUNTDOWN_PER_PAGE:
                # Countdown per page
                self.clockdown_manager_per_page = ClockdownManager(self.timekeeping_time, self.timer_per_page_label)
                self.clockdown_manager_per_page.timeout_finished.connect(self.clockdown_finish_per_page)
                self.timer_per_page_icon.setText(icons_clock_red_down_arrow_html_text_small)
                self.timer_per_page_icon.setToolTip(tr("game_countdown_per_page_tooltip"))
                self.timer_per_page_label.setToolTip(tr("game_countdown_per_page_tooltip"))
                # Timer for all cards
                self.timer_manager_for_all_cards = TimerManager(self.timer_for_all_cards_label)
                self.timer_manager_for_all_cards.start_timer()
                self.timer_for_all_cards_icon.setText(icons_clock_green_up_arrow_html_text_big)
                self.timer_for_all_cards_icon.setToolTip(tr("game_timer_for_all_cards_tooltip"))
                self.timer_for_all_cards_label.setToolTip(tr("game_timer_for_all_cards_tooltip"))
            case TimekeepingMode.TIME_INFORMATIONAL:
                # Timer per page
                self.timer_manager_per_page = TimerManager(self.timer_per_page_label)
                self.timer_per_page_icon.setText(icons_clock_green_up_arrow_html_text_small)
                self.timer_per_page_icon.setToolTip(tr("game_timer_per_page_tooltip"))
                self.timer_per_page_label.setToolTip(tr("game_timer_per_page_tooltip"))
                # Timer for all cards
                self.timer_manager_for_all_cards = TimerManager(self.timer_for_all_cards_label)
                self.timer_manager_for_all_cards.start_timer()
                self.timer_for_all_cards_icon.setText(icons_clock_green_up_arrow_html_text_big)
                self.timer_for_all_cards_icon.setToolTip(tr("game_timer_for_all_cards_tooltip"))
                self.timer_for_all_cards_label.setToolTip(tr("game_timer_for_all_cards_tooltip"))


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

        self.audio_currently_playing = False
        gui_hooks.av_player_did_end_playing.append(self._handle_audio_finished)
        self.last_sound: str | None = None

        self.total_pages : int = (len(self.all_data) + self.page_size - 1) // self.page_size

        self.layout.addLayout(button_layout)
        self.load_page()

    def change_label_font_size(self, label, size):
        current_font = label.font()
        current_font.setPointSize(size)
        label.setFont(current_font)

    # Create Vertical Separator
    def create_v_separator(self):
        separator = QFrame()
        separator.setFixedWidth(2)
        # Opcjonalnie: ustaw kolor linii za pomocą CSS (lub QPalette)
        separator.setStyleSheet("QFrame { background-color: #aaa; }")
        return separator

    def clockdown_finish_per_page(self):
        # Disable this page buttons
        for btn in self.vocab_buttons.values():
            btn.force_disable_instant("lightcoral")
        for btn in self.meaning_buttons.values():
            btn.force_disable_instant("lightcoral")
        # Disable Timer for all cards, only if this is last page
        if self.is_last_page():
            self.timer_manager_for_all_cards.stop_timer()

    def clockdown_finish_for_all_cards(self):
        # Disable this page buttons
        for btn in self.vocab_buttons.values():
            btn.force_disable_instant("lightcoral")
        for btn in self.meaning_buttons.values():
            btn.force_disable_instant("lightcoral")
        # Disable "Next Page" button
        self.next_button.setStyleSheet("""
            QPushButton {
                font-size: 16pt; 
                padding: 10px 20px 10px 20px;
                background: lightcoral; 
            }
        """)
        self.next_button.setEnabled(False)
        # Disable Timer per page
        self.timer_manager_per_page.stop_timer()

    def load_page(self):
        #total_pages = (len(self.all_data) + self.page_size - 1) // self.page_size
        self.page_info.setText(tr("game_page", page=self.current_page+1, total_pages=self.total_pages))

        self.can_auto_next_page = False
        self.last_animation_finished = False

        # Timers and Countdowners
        match self.timekeeping_mode:
            case TimekeepingMode.COUNTDOWN_FOR_ALL_CARDS:
                # Timer per page
                self.timer_manager_per_page.start_timer()
            case TimekeepingMode.COUNTDOWN_PER_PAGE:
                # Countdown per page
                self.clockdown_manager_per_page.start_clockdown()
            case TimekeepingMode.TIME_INFORMATIONAL:
                # Timer per page
                self.timer_manager_per_page.start_timer()

        if self.is_last_page():
            self.next_button.setVisible(False)

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

        # Get number of current page cards (tiles = cards * 2)
        self.current_page_cards = len(self.page_data)


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

                self.can_auto_next_page = True

                # play audio file if exist
                self.last_sound : str = audio_content
                played_files = anki_media.play_audio_from_card_field(audio_content)
                if len(played_files) > 0:
                    self.audio_currently_playing = True
                    self.corner_button_sound.setText("🔊")

                # count number of cards in current page
                self.current_page_cards -= 1
                if self.current_page_cards <= 0:
                    self.matched_last_card_on_page()

            else:
                self.selection_wrong(self.vocab_buttons[self.selected_vocab], self.meaning_buttons[self.selected_meaning])

            self.selected_vocab = None
            self.selected_meaning = None

    def selection_wrong(self, btn1, btn2):
        self.wrong_total += 1
        self.status_label.setText("❌ Wrong, try again!")

        btn1.setChecked(False)  # Unselect Button
        btn2.setChecked(False)  # Unselect Button

        btn1.flash_color_overlay("lightcoral")
        btn2.flash_color_overlay("lightcoral")

        self.selected_vocab = None
        self.selected_meaning = None

        self.update_summary()

    def _update_card_progress(self, card_id):
        if not self.update_stats:
            return

        grade_now(parent=self, card_ids=[card_id], ease=2).failure(self._handle_update_failure).run_in_background()

    def _handle_update_failure(self, error):
        showWarning(f"Failed to update card status: {error}")

    # execute when last card on the page is matched
    def matched_last_card_on_page(self):
        QTimer.singleShot(int(self.animtime*1000), self._handle_last_animation_finished)

        # Timers and Countdowners
        if self.is_last_page():
            match self.timekeeping_mode:
                case TimekeepingMode.COUNTDOWN_FOR_ALL_CARDS:
                    # Timer per page
                    self.timer_manager_per_page.stop_timer()
                    # Countdown for all cards
                    self.clockdown_manager_for_all_cards.stop_clockdown()
                case TimekeepingMode.COUNTDOWN_PER_PAGE:
                    # Countdown per page
                    self.clockdown_manager_per_page.stop_clockdown()
                    # Timer for all cards
                    self.timer_manager_for_all_cards.stop_timer()
                case TimekeepingMode.TIME_INFORMATIONAL:
                    # Timer per page
                    self.timer_manager_per_page.stop_timer()
                    # Timer for all cards
                    self.timer_manager_for_all_cards.stop_timer()


    # execute when match animation finished on last card on the page
    def _handle_last_animation_finished(self):
        self.last_animation_finished = True
        if self.audio_currently_playing == False and self.can_auto_next_page and not self.is_last_page():
            self.next_page()

    # execute when single audio file finished
    def _handle_audio_finished(self, audio_finished_filename: str) -> None:
        files_remaining = len(av_player._enqueued)

        if files_remaining <= 0:
            self.audio_currently_playing = False
            self.corner_button_sound.setText("🔈")
            if self.last_animation_finished == True and self.can_auto_next_page and not self.is_last_page():
                self.next_page()

    def corner_button_sound_clicked(self):
        if self.last_sound:
            played_files = anki_media.play_audio_from_card_field(self.last_sound)
            if len(played_files) > 0:
                self.audio_currently_playing = True
                self.corner_button_sound.setText("🔊")

    def is_last_page(self):
        return self.current_page+1 >= self.total_pages