import sys, os, json, datetime
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout
)
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QPixmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "save.json")

# ------------------ BOSS DATA ------------------

BOSSES = [
    {"name": "🐉 Dragon of Procrastination", "hp": 100},
    {"name": "🕷 Spider of Distraction", "hp": 120},
    {"name": "😈 Demon of Burnout", "hp": 150},
    {"name": "👹 Ogre of Laziness", "hp": 130},
    {"name": "🦹 Villain of Overwhelm", "hp": 160},
]

# =================================================

class MainWindow(QMainWindow):
    def __init__(self, username="Player"):
        super().__init__()
        uic.loadUi(os.path.join(BASE_DIR, "ui/main_window.ui"), self)

        self.setStyleSheet("""
        /* ===== MAIN WINDOW ===== */
        QMainWindow {
            background-color: #12121a;
        }

        /* Central Area */
        QWidget#centralwidget {
            background-color: #181824;
            color: #e6e6e6;
            font-family: Segoe UI;
            font-size: 14px;
        }

        /* ===== SIDEBAR ===== */
        QFrame#sidebar {
            background-color: #0f0f18;
        }

        QPushButton {
            background-color: #23233a;
            color: #e6e6e6;
            border: none;
            padding: 8px;
            border-radius: 8px;
            text-align: left;
        }

        QPushButton:hover {
            background-color: #2e2e4d;
        }

        QPushButton:pressed {
            background-color: #3b3b66;
        }

        /* ===== LABELS ===== */
        QLabel {
            color: #e6e6e6;
        }

        /* ===== PROGRESS BARS (Boss HP / XP later) ===== */
        QProgressBar {
            background-color: #2a2a3d;
            border-radius: 8px;
            text-align: center;
            height: 18px;
        }

        QProgressBar::chunk {
            background-color: #8b0000;  /* Dark red boss HP */
            border-radius: 8px;
        }

        /* ===== INPUTS ===== */
        QLineEdit, QSpinBox {
            background-color: #23233a;
            border: 1px solid #33334d;
            padding: 4px;
            border-radius: 6px;
            color: #ffffff;
        }

        /* ===== SCROLL AREA ===== */
        QScrollArea {
            border: none;
        }
        """)

        # Game state
        self.username = username
        self.level = 1
        self.xp = 0
        self.xp_needed = 100
        self.custom_tasks = []

        # Navigation
        self.btnDashboard.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.pageDashboard)
        )
        self.btnDaily.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.pageDaily)
        )
        self.btnTasks.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.pageTasks)
        )

        # Setup systems
        self.setup_boss()
        self.setup_task_system()
        self.load_progress()
        self.update_ui()

    # ------------------ BOSS ------------------

    def setup_boss(self):
        week = datetime.date.today().isocalendar()[1]
        self.boss_data = BOSSES[week % len(BOSSES)]

        self.boss_max_hp = self.boss_data["hp"]
        self.boss_hp = self.boss_max_hp

        # Create boss UI dynamically
        layout = self.dashboardContentLayout

        self.bossName = QLabel(self.boss_data["name"])
        self.bossName.setStyleSheet("font-size:18px; font-weight:bold;")

        self.bossHpBar = QLabel(f"Boss HP: {self.boss_hp}/{self.boss_max_hp}")

        layout.addWidget(self.bossName)
        layout.addWidget(self.bossHpBar)

    def damage_boss(self, dmg):
        self.boss_hp = max(0, self.boss_hp - dmg)
        self.bossHpBar.setText(
            f"Boss HP: {self.boss_hp}/{self.boss_max_hp}"
        )

    # ------------------ XP ------------------

    def add_xp(self, amount):
        self.xp += amount

        if self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            self.xp_needed = int(self.xp_needed * 1.2)

        self.update_ui()
        self.save_progress()

    def update_ui(self):
        self.setWindowTitle(f"{self.username} - Level {self.level}")

    # ------------------ TASK SYSTEM ------------------

    def setup_task_system(self):
        layout = self.tasksContainerLayout

        # Add input row
        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)

        self.taskNameInput = QLabel("Use code to add tasks")  # placeholder

        input_layout.addWidget(self.taskNameInput)
        layout.addWidget(input_row)

    def add_task(self, name, xp, dmg):
        task = {"name": name, "xp": xp, "dmg": dmg}
        self.custom_tasks.append(task)
        self.populate_tasks()
        self.save_progress()

    def populate_tasks(self):
        layout = self.tasksContainerLayout

        # Clear existing
        while layout.count() > 1:
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for task in self.custom_tasks:
            row = QWidget()
            row_layout = QHBoxLayout(row)

            label = QLabel(
                f"{task['name']} (+{task['xp']} XP, -{task['dmg']} HP)"
            )
            btn = QPushButton("Complete")

            btn.clicked.connect(
                lambda _, t=task: self.complete_task(t)
            )

            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(btn)

            layout.addWidget(row)

    def complete_task(self, task):
        self.add_xp(task["xp"])
        self.damage_boss(task["dmg"])
        self.custom_tasks.remove(task)
        self.populate_tasks()
        self.save_progress()

    # ------------------ SAVE ------------------

    def save_progress(self):
        data = {
            "level": self.level,
            "xp": self.xp,
            "xp_needed": self.xp_needed,
            "tasks": self.custom_tasks
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load_progress(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                self.level = data.get("level", 1)
                self.xp = data.get("xp", 0)
                self.xp_needed = data.get("xp_needed", 100)
                self.custom_tasks = data.get("tasks", [])
        self.populate_tasks()

# ------------------ RUN ------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("Player")
    window.show()
    sys.exit(app.exec_())