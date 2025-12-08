from aqt.qt import QTimer, QTime, QLabel, QObject, pyqtSignal


class ClockdownManager(QObject):
    # Define a custom signal that is emitted when the timer reaches 0
    timeout_finished = pyqtSignal()

    def __init__(self, clockdown_time: QTime, clockdown_label: QLabel):
        super().__init__()

        # State variables
        self.secs_remaining: int = 0
        self.is_running: bool = False

        # UI references
        #self.time_edit = time_edit
        self.clockdown_time = clockdown_time
        self.clockdown_label = clockdown_label

        # QTimer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_cycle)
        self.timer.setInterval(1000)  # 1000 ms = 1 second interval

        self.clockdown_label.setText("00:00")

    def start_clockdown(self) -> None:
        # Stop existing timer if running
        if self.is_running:
            self.stop_clockdown()

        time_obj: QTime = self.clockdown_time  # self.time_edit.time()

        # Convert QTime (MM:SS) to total seconds (int)
        self.secs_remaining = time_obj.minute() * 60 + time_obj.second()

        if self.secs_remaining <= 0:
            return

        # Start the QTimer and update UI immediately
        self.is_running = True
        self.timer.start()
        self._update_label()

    def _update_cycle(self) -> None:
        # Called every second by QTimer

        if not self.is_running:
            return

        self.secs_remaining -= 1

        if self.secs_remaining <= 0:
            self.stop_clockdown()
            self.clockdown_label.setText("00:00")

            # Emit the custom signal to notify external listeners
            self.timeout_finished.emit()
            return

        self._update_label()

    def _update_label(self) -> None:
        # Updates the QLabel with the time in MM:SS format
        minutes = self.secs_remaining // 60
        seconds = self.secs_remaining % 60

        # Use f-string for concise formatting with leading zeros
        self.clockdown_label.setText(f"{minutes:02d}:{seconds:02d}")

    def stop_clockdown(self) -> None:
        # Stops the QTimer and resets the state flag
        if self.timer.isActive():
            self.timer.stop()
        self.is_running = False
