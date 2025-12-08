from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QHBoxLayout, QSpinBox, QGridLayout, QDoubleSpinBox,
    QCheckBox, QSlider, QStackedWidget, QSpacerItem, QTimeEdit
)
from PyQt6.QtCore import QTime
from aqt import mw
from aqt.qt import Qt, QScreen, QApplication
from .matching_ui import MatchingExam
import random
import anki.errors

from ..enums import TimekeepingMode
from ..translation import tr


config_default_clockdown_per_page = QTime(0, 2, 0)          # 0h, 2m, 0s
config_default_clockdown_for_all_cards = QTime(0, 10, 0)    # 0h, 10m, 0s



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
        layout.addWidget(QLabel(tr("config_select_deck")))
        layout.addWidget(self.deck_selector)
        layout.addWidget(QLabel(tr("config_select_note_type")))
        layout.addWidget(self.note_type_selector)
        layout.addWidget(QLabel(tr("config_select_field_vocabulary")))
        layout.addWidget(self.vocab_field_selector)
        layout.addWidget(QLabel(tr("config_select_field_meaning")))
        layout.addWidget(self.meaning_field_selector)
        layout.addWidget(QLabel(tr("config_select_field_audio")))
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

        gridConfigFontScreen.addWidget(QLabel(tr("config_font_size")), 0, 0)
        gridConfigFontScreen.addLayout(font_size_layout, 1, 0)

        screen_layout = QHBoxLayout()
        screen_layout.addWidget(self.screen_x)
        screen_layout.addWidget(self.screen_y)

        gridConfigFontScreen.addWidget(QLabel(tr("config_screen_size")), 0, 1)
        gridConfigFontScreen.addLayout(screen_layout, 1, 1)


        # Timekeeping
        self.timekeeping = QComboBox()
        self.timekeeping.addItem(tr("config_timekeeping_1"))
        self.timekeeping.addItem(tr("config_timekeeping_2"))
        self.timekeeping.addItem(tr("config_timekeeping_3"))

        self.timekeeping_mode: TimekeepingMode = TimekeepingMode(self.timekeeping.currentIndex())

        self.timekeeping_stacked = QStackedWidget()
        self.timekeeping.currentIndexChanged.connect(self.timekeeping_config_changed)

        self.timekeeping_time_per_page = QTimeEdit()
        self.timekeeping_time_per_page.setDisplayFormat("hh:mm:ss")
        self.timekeeping_time_per_page.setTime(config_default_clockdown_per_page)
        self.timekeeping_time_for_all_cards = QTimeEdit()
        self.timekeeping_time_for_all_cards.setDisplayFormat("hh:mm:ss")
        self.timekeeping_time_for_all_cards.setTime(config_default_clockdown_for_all_cards)


        space_container_widget = QWidget()
        space_container_widget.setFixedSize(100, 30)
        space_container_widget.setAutoFillBackground(False)

        self.timekeeping_stacked.addWidget(space_container_widget)
        self.timekeeping_stacked.addWidget(self.timekeeping_time_per_page)
        self.timekeeping_stacked.addWidget(self.timekeeping_time_for_all_cards)

        gridConfigTimekeeping = QGridLayout()
        layout.addLayout(gridConfigTimekeeping)

        gridConfigTimekeeping.addWidget(QLabel(tr("config_timekeeping")), 0, 0)
        gridConfigTimekeeping.addWidget(self.timekeeping, 1, 0)
        gridConfigTimekeeping.addWidget(self.timekeeping_stacked, 1,1)


        # Update Anki progress  |  Card Selection mode
        self.update_stats_checkbox = QCheckBox("")
        self.update_stats_checkbox.setChecked(False)

        self.update_stats = QComboBox()
        self.update_stats.addItem("Do not update", "no")
        self.update_stats.addItem("Static grade", "static")
        #self.update_stats.addItem()

        self.card_selection_mode = QComboBox()
        self.card_selection_mode.addItem(tr("config_card_selection_mode_1"), "all")
        self.card_selection_mode.addItem(tr("config_card_selection_mode_2"), "ready_all")
        self.card_selection_mode.addItem(tr("config_card_selection_mode_3"), "daily_limit")

        gridConfigDeck = QGridLayout()
        layout.addLayout(gridConfigDeck)

        gridConfigDeck.addWidget(QLabel("Update Anki progress for matched cards:"), 0, 0)
        gridConfigDeck.addWidget(self.update_stats_checkbox, 1, 0)

        gridConfigDeck.addWidget(QLabel(tr("config_card_selection_mode")), 0, 1)
        gridConfigDeck.addWidget(self.card_selection_mode, 1, 1)


        # Disappering Animation Type  |  Animation Time
        gridConfigAnimation = QGridLayout()
        layout.addLayout(gridConfigAnimation)

        gridConfigAnimation.addWidget(QLabel(tr("config_disappearing_animation_type")), 0, 0)
        gridConfigAnimation.addWidget(self.disappearing_type, 1, 0)

        gridConfigAnimation.addWidget(QLabel(tr("config_animation_time")), 0, 1)
        gridConfigAnimation.addWidget(self.disappearing_time, 1, 1)

        self.disappearing_type.addItem("fade")
        self.disappearing_type.addItem("shrink")


        gridConfig = QGridLayout()
        layout.addLayout(gridConfig)
        gridConfig.addWidget(QLabel(tr("config_number_of_cards_per_page")), 0, 0)
        gridConfig.addWidget(self.word_count_box, 1, 0)
        gridConfig.addWidget(QLabel(tr("config_number_of_columns")), 0, 1)
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

    def timekeeping_config_changed(self, index: int) -> None:
        self.timekeeping_stacked.setCurrentIndex(index)
        self.timekeeping_mode = TimekeepingMode(index)


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

    def get_cards_for_mode(self, deck_name: str, mode_index: int) -> list[int]:
        # Base query limiting to the selected deck
        # We use quotes around deck name to handle spaces safely
        base_query = f'deck:"{deck_name}"'

        status_query = ""

        if mode_index == 0:
            # Mode: All cards
            # No status filter needed, fetches entire deck (including suspended).
            pass

        elif mode_index == 1:
            # Mode: All ready cards (No limits)
            # FIX: Previously 'is:due' missed 'is:new' cards.
            # Now we explicitly ask for New, Due (Review), and Learn queues.
            status_query = "(is:new OR is:due OR is:learn)"

        elif mode_index == 2:
            # Mode: Scheduled pool (Daily limits)
            # Delegates logic to the new helper function to apply per-deck limits
            # based on card type priority (Learn > Due > New).
            return self._get_limited_scheduled_cards(deck_name)

        # Combine deck query with status query
        full_query = f"{base_query} {status_query}".strip()

        # Execute search in Anki collection
        return mw.col.find_cards(full_query)

    def _get_limited_scheduled_cards(self, deck_name: str) -> list[int]:
        base_query = f'deck:"{deck_name}"'
        did = mw.col.decks.id_for_name(deck_name)

        # 1. Get Daily Limits
        conf = mw.col.decks.config_dict_for_deck_id(did)
        new_limit = conf['new']['perDay']
        review_limit = conf['rev']['perDay']

        # 2. Fetch Cards for all three queues (Learn, Due, New)
        # We need card objects to get their 'queue' status and 'due' date for sorting.
        # Fetching all ready cards first.
        all_ready_ids = mw.col.find_cards(f'{base_query} (is:new OR is:due OR is:learn)')

        # Map card ID to the actual Card object
        all_cards = [mw.col.get_card(cid) for cid in all_ready_ids]

        # 3. Separate cards into priority groups
        learn_cards = []
        due_cards = []
        new_cards = []

        for card in all_cards:
            if card.queue == 1:  # Learn queue (Anki consts: 1)
                learn_cards.append(card)
            elif card.queue == 2:  # Review/Due queue (Anki consts: 2)
                due_cards.append(card)
            elif card.queue == 0:  # New queue (Anki consts: 0)
                new_cards.append(card)

        # 4. Sort within groups (Priority: Oldest first)
        # - Learn: Sort by oldest step (card.due)
        learn_cards.sort(key=lambda c: c.due)
        # - Due: Sort by oldest due date (card.due)
        due_cards.sort(key=lambda c: c.due)
        # - New: Sort by date added or card.id (to ensure a consistent order)
        new_cards.sort(key=lambda c: c.id)

        # 5. Apply Limits (New and Due)
        # Learn cards are typically NOT limited by daily review limits.

        # New cards limit
        limited_new = [c.id for c in new_cards[:new_limit]]

        # Due cards limit
        limited_due = [c.id for c in due_cards[:review_limit]]

        # 6. Combine and prioritize (Learn first, then Due, then New)
        final_ids = (
                [c.id for c in learn_cards] +
                limited_due +
                limited_new
        )

        # This list may still contain duplicates if a card technically meets
        # multiple criteria (e.g., a card in learning that is also marked as 'due'
        # by some internal logic). We use a set for final deduplication.
        return list(set(final_ids))

    def start_exam(self):
        deck_name = self.deck_selector.currentText()
        note_type_id_check = self.note_type_selector.currentText()
        vocab_field = self.vocab_field_selector.currentText()
        meaning_field = self.meaning_field_selector.currentText()
        audio_field = self.audio_field_selector.currentText()

        # default validation
        if not deck_name or not note_type_id_check or not vocab_field or not meaning_field:
            QMessageBox.warning(self, "Missing information", "Please select all fields.")
            return

        note_type_id = mw.col.models.by_name(note_type_id_check)['id']

        timekeeping_time = QTime()
        match self.timekeeping_mode:
            case TimekeepingMode.COUNTDOWN_PER_PAGE:
                timekeeping_time = self.timekeeping_time_per_page.time()
            case TimekeepingMode.COUNTDOWN_FOR_ALL_CARDS:
                timekeeping_time = self.timekeeping_time_for_all_cards.time()


        # --- Card Filtering Integration ---
        # Get selected card pool mode index (0: Scheduled, 1: Ready, 2: All)
        mode_index = self.card_selection_mode.currentIndex()

        # Fetch card IDs using the new encapsulated function
        card_ids = self.get_cards_for_mode(deck_name, mode_index)

        if not card_ids:
            QMessageBox.information(self, "No Cards Found", "No cards found for the selected criteria.")
            return
        # --- End of Filtering Integration ---

         # Prepare data structure for the MatchingExam game
        all_data = []

        # NOTE: Using the newly fetched card_ids list
        for cid in card_ids:
            card = mw.col.get_card(cid)
            note = card.note()

            # Skip cards that do not match the selected Note Type
            if note.mid != note_type_id:
                continue

            # Extract content from fields
            vocab_content = note[vocab_field]
            meaning_content = note[meaning_field]

            # Use audio_field only if it was selected; otherwise, use empty string
            audio_content = note[audio_field] if audio_field else ""

            # Check if both required fields have content
            if vocab_content and meaning_content:
                # Store the data as a 4-element tuple: (vocab, meaning, audio, card_id)
                all_data.append((vocab_content, meaning_content, audio_content, cid))

        if not all_data:
            QMessageBox.warning(self, "Empty Fields",
                                "No cards found with content in the selected Vocab and Meaning fields.")
            return

        # 3. Shuffle data and run the game
        random.shuffle(all_data)


        win = MatchingExam(
            all_data=all_data,
            page_size=self.word_count_box.value(),
            columns=self.word_columns.value(),
            anim=self.disappearing_type.currentText(),
            animtime=self.disappearing_time.value(),
            ###update_stats=update_stats,
            update_stats=self.update_stats_checkbox.isChecked(),
            font_size=self.font_size_slider.value(),
            timekeeping_mode=self.timekeeping_mode,
            timekeeping_time=timekeeping_time)

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
