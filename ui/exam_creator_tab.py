from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QHBoxLayout, QSpinBox, QGridLayout, QDoubleSpinBox,
    QCheckBox, QSlider
)
from aqt import mw
from aqt.qt import Qt, QScreen, QApplication
from .matching_ui import MatchingExam
import random
import anki.errors


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
        self.audio_field_selector = QComboBox()
        self.screen_x = QSpinBox()
        self.screen_x.setRange(600, 3840)
        self.screen_x.setSingleStep(20)
        self.screen_x.setValue(1600)
        self.screen_y = QSpinBox()
        self.screen_y.setRange(500, 2160)
        self.screen_y.setSingleStep(20)
        self.screen_y.setValue(900)
        self.disappearing_type = QComboBox()
        self.disappearing_time = QDoubleSpinBox()
        self.disappearing_time.setDecimals(1)
        self.disappearing_time.setRange(0.1, 5.0)
        self.disappearing_time.setSingleStep(0.1)
        self.disappearing_time.setValue(0.5)
        self.word_count_box = QSpinBox()
        self.word_count_box.setRange(3, 50)
        self.word_count_box.setValue(10)
        self.word_columns = QSpinBox()
        self.word_columns.setRange(2, 50)
        self.word_columns.setValue(4)

        self.deck_selector.currentIndexChanged.connect(self.update_note_types)
        self.note_type_selector.currentIndexChanged.connect(self.update_fields)
        layout.addWidget(QLabel("Select Deck (including subdecks):"))
        layout.addWidget(self.deck_selector)
        layout.addWidget(QLabel("Select Note Type:"))
        layout.addWidget(self.note_type_selector)
        layout.addWidget(QLabel("Select the field containing the Word (Vocabulary):"))
        layout.addWidget(self.vocab_field_selector)
        layout.addWidget(QLabel("Select the field containing the Meaning:"))
        layout.addWidget(self.meaning_field_selector)
        layout.addWidget(QLabel("Select the field containing the Audio:"))
        layout.addWidget(self.audio_field_selector)


        # Font Size  |  Screen Size
        self.font_size_slider = QSlider()
        self.font_size_slider.setOrientation(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(10, 30)  # Range in 10pt to 30pt
        default_font_size = 13
        self.font_size_slider.setValue(default_font_size)

        self.font_size_value_label = QLabel(f"{default_font_size}pt")
        self.font_size_value_label.setFixedWidth(40)

        gridConfigFontScreen = QGridLayout()
        layout.addLayout(gridConfigFontScreen)

        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value_label)

        self.font_size_slider.valueChanged.connect(self._update_font_size_label)

        gridConfigFontScreen.addWidget(QLabel("Font Size:"), 0, 0)
        gridConfigFontScreen.addLayout(font_size_layout, 1, 0)

        screen_layout = QHBoxLayout()
        screen_layout.addWidget(self.screen_x)
        screen_layout.addWidget(self.screen_y)

        gridConfigFontScreen.addWidget(QLabel("Screen Size:"), 0, 1)
        gridConfigFontScreen.addLayout(screen_layout, 1, 1)


        # Update Anki progress  |  Card Selection mode
        self.update_stats_checkbox = QCheckBox("")
        self.update_stats_checkbox.setChecked(False)

        self.card_selection_mode = QComboBox()
        self.card_selection_mode.addItem("Use all cards (ignores status)", "all")
        self.card_selection_mode.addItem("Use all 'Ready' cards (is:due)", "ready_all")
        self.card_selection_mode.addItem("Use cards within Daily Limit (scheduled pool)", "daily_limit")

        gridConfigDeck = QGridLayout()
        layout.addLayout(gridConfigDeck)

        gridConfigDeck.addWidget(QLabel("Update Anki progress for matched cards:"), 0, 0)
        gridConfigDeck.addWidget(self.update_stats_checkbox, 1, 0)

        gridConfigDeck.addWidget(QLabel("Card Selection Mode:"), 0, 1)
        gridConfigDeck.addWidget(self.card_selection_mode, 1, 1)


        # Disappering Animation Type  |  Animation Time
        gridConfigAnimation = QGridLayout()
        layout.addLayout(gridConfigAnimation)

        gridConfigAnimation.addWidget(QLabel("Disappearing Animation Type"), 0, 0)
        gridConfigAnimation.addWidget(self.disappearing_type, 1, 0)

        gridConfigAnimation.addWidget(QLabel("Animation Time"), 0, 1)
        gridConfigAnimation.addWidget(self.disappearing_time, 1, 1)

        self.disappearing_type.addItem("fade")
        self.disappearing_type.addItem("shrink")


        gridConfig = QGridLayout()
        layout.addLayout(gridConfig)
        gridConfig.addWidget(QLabel("Number of words per page:"), 0, 0)
        gridConfig.addWidget(self.word_count_box, 1, 0)
        gridConfig.addWidget(QLabel("Number of columns:"), 0, 1)
        gridConfig.addWidget(self.word_columns, 1, 1)

        btn_layout = QHBoxLayout()
        self.start_button = QPushButton("Start test")
        self.start_button.clicked.connect(self.start_exam)
        btn_layout.addWidget(self.start_button)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(lambda: (mw.matching_config_win.close(), setattr(mw, "matching_config_win", None)))
        btn_layout.addWidget(self.exit_button)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_decks()

    def config_deduction(self):
        # Set of probable audio field names (in lowercase for fast lookup)
        PROBABLE_AUDIO_FIELDS = {"audio", "sound", "pronunciation", "music"}

        # --- Audio Field Deduction (Case-Insensitive) ---
        # Iterate over all items currently in the QComboBox to find probably audio field
        for index in range(self.audio_field_selector.count()):
            field_name = self.audio_field_selector.itemText(index)

            # Check if the lowercase version of the field name matches any probable name
            if field_name.lower() in PROBABLE_AUDIO_FIELDS:
                # Found a match! Set the index using the current safe index and return
                self.audio_field_selector.setCurrentIndex(index)
                break  # Break the loop after setting the first match

        # --- Vocab and Meaning Field Deduction (Positional) ---
        # Get the number of available fields (all selectors have the same count at this point)
        field_count = self.vocab_field_selector.count()

        # Set Vocab field to the first available field (Index 0)
        if field_count > 0:     # Check if at least one field exists
            self.vocab_field_selector.setCurrentIndex(0)

        # Set Meaning field to the second available field (Index 1)
        if field_count > 1:     # Check if at least two fields exist
            self.meaning_field_selector.setCurrentIndex(1)

    def _update_font_size_label(self, value: int):
        self.font_size_value_label.setText(f"{value}pt")

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
        self.audio_field_selector.clear()
        ntid = self.note_type_selector.currentData()
        model = mw.col.models.get(ntid)
        if model:
            fields = [f["name"] for f in model["flds"]]
            self.vocab_field_selector.addItems(fields)
            self.meaning_field_selector.addItems(fields)
            self.audio_field_selector.addItems(fields)
            self.config_deduction()

    def start_exam(self):
        deck_name = self.deck_selector.currentText()
        note_type_id = self.note_type_selector.currentData()
        vocab_field = self.vocab_field_selector.currentText()
        meaning_field = self.meaning_field_selector.currentText()
        audio_field = self.audio_field_selector.currentText()

        # default validation
        if not deck_name or not note_type_id or not vocab_field or not meaning_field:
            QMessageBox.warning(self, "Missing information", "Please select all fields.")
            return

        # getting settings from user interface
        update_stats = self.update_stats_checkbox.isChecked()
        selection_mode = self.card_selection_mode.currentData() # 'all', 'ready_all', lub 'daily_limit'

        deck_id = mw.col.decks.id(deck_name)
        cids_pool = []
        cids = []

        if selection_mode == 'daily_limit':
            cids_pool_all_decks = mw.col.sched.get_queued_cards(fetch_limit=1000000)

            cids_final_daily = []

            for queued_card_object in cids_pool_all_decks.cards:
                # KEY: in object QueuedCard, ID card is accessible as attribute .id
                cid = queued_card_object.card.id

                card = mw.col.get_card(cid)

                # Check whether card is inside chosen deck
                if card and card.did == deck_id:
                    cids_final_daily.append(cid)

            cids = cids_final_daily

        elif selection_mode == 'ready_all':
            # Mode "is:due" (return all is:due - ignore the limit)
            query = f'deck:"{deck_name}" is:due'
            cids = mw.col.find_cards(query)

        else:  # 'all'
            # Mode "Use all cards" (return all, ignoring status)
            query = f'deck:"{deck_name}"'
            cids = mw.col.find_cards(query)


        notes = []
        for cid in cids:
            # Getting Note ID
            nid = mw.col.db.scalar("select nid from cards where id = ?", cid)

            # If there is any problem with Note ID, ignore this card
            if not nid:
                continue

            try:
                note = mw.col.get_note(nid)
            except anki.errors.DBError as e:
                print(f"DB Error (Note ignored): Note ID {nid} is corrupted (DBError: {e}).")
                continue    # go to next card

            # Checking if note has correct Note Type
            if note.mid == note_type_id:
                vocab = note[vocab_field]
                meaning = note[meaning_field]
                audio = note[audio_field]

                # Be sure vocab i meaning are not empty
                if vocab and meaning:
                    notes.append((vocab, meaning, audio, cid))

        # Validation if all cards has their pair
        if len(notes) < 1:
            QMessageBox.information(self, "Not enough data", "No valid word-meaning pair found.")
            return

        # Running Exam
        random.shuffle(notes)
        win = MatchingExam(
            notes,
            page_size=self.word_count_box.value(),
            columns=self.word_columns.value(),
            anim=self.disappearing_type.currentText(),
            animtime=self.disappearing_time.value(),
            update_stats=update_stats,
            font_size=self.font_size_slider.value())

        win.setMinimumSize(600, 500)

        DEFAULT_SCREEN_WIDTH = self.screen_x.value()
        DEFAULT_SCREEN_HEIGHT = self.screen_y.value()

        app = mw.app
        screen = app.primaryScreen()
        available_rect = screen.availableGeometry()
        max_screen_width = available_rect.width()
        max_screen_height = available_rect.height()
        final_width = min(DEFAULT_SCREEN_WIDTH, max_screen_width)
        final_height = min(DEFAULT_SCREEN_HEIGHT, max_screen_height)
        win.resize(final_width, final_height)

        win.show()
