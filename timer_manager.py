from aqt.qt import QTimer, QLabel, QObject, pyqtSignal


class TimerManager(QObject):
    # Define a custom signal that is emitted when the timer reaches 0

    def __init__(self, timer_label: QLabel):
        super().__init__()

        # State variables
        self.secs_remaining: int = 0
        self.is_running: bool = False

        self.timer_seconds = 0
        self.timer_label = timer_label

        # QTimer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_cycle)
        self.timer.setInterval(1000)  # 1000 ms = 1 second interval

        self.timer_label.setText("00:00")

    def start_timer(self) -> None:
        # Stop existing timer if running
        if self.is_running:
            self.stop_timer()

        # Start the QTimer and update UI immediately
        self.is_running = True
        self.timer.start()
        self._update_label()

    def _update_cycle(self) -> None:
        # Called every second by QTimer
        if not self.is_running:
            return

        self.timer_seconds += 1
        self._update_label()

    def _update_label(self) -> None:
        # Updates the QLabel with the time in MM:SS format
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60

        # Use f-string for concise formatting with leading zeros
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def stop_timer(self) -> None:
        # Stops the QTimer and resets the state flag
        if self.timer.isActive():
            self.timer.stop()
        self.is_running = False
        self.timer_seconds = 0
