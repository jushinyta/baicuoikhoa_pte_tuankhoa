import sys, os, json, datetime
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QSoundEffect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "save.json")

# ------------------ BOSS DATA ------------------
BOSSES = [
    {"name": "🐉 Dragon of Procrastination", "hp": 100, "img": "dragon.png"},
    {"name": "🕷 Spider of Distraction", "hp": 120, "img": "spider.png"},
    {"name": "😈 Demon of Burnout", "hp": 150, "img": "demon.png"},
    {"name": "👹 Ogre of Laziness", "hp": 130, "img": "ogre.png"},
    {"name": "🦹‍♂️ Villain of Overwhelm", "hp": 160, "img": "villain.png"},    
]

# ------------------ DAILY QUESTS ------------------
DAILY_QUESTS = [
    ("Study 25 minutes", 20, 10),
    ("Clean your desk", 15, 8),
    ("Exercise", 25, 12),
    ("Read 10 pages", 20, 10),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        path = os.path.join(BASE_DIR, "ui/daily_quests.ui")
        print("Daily UI exists:", os.path.exists(path))
        print("Daily UI size:", os.path.getsize(path))

        
        ui_path = os.path.join(BASE_DIR, "ui/main_window.ui")
        print("UI exists:", os.path.exists(ui_path))
        print("UI size:", os.path.getsize(ui_path))

        uic.loadUi(os.path.join(BASE_DIR, "ui/main_window.ui"), self)

        # Load pages
        self.dashboard = uic.loadUi(os.path.join(BASE_DIR, "ui/dashboard.ui"))
        self.daily = uic.loadUi(os.path.join(BASE_DIR, "ui/daily_quests.ui"))

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.daily)

        # Sidebar navigation
        self.btnDashboard.clicked.connect(lambda: self.pages.setCurrentWidget(self.dashboard))
        self.btnDaily.clicked.connect(lambda: self.pages.setCurrentWidget(self.daily))

        # Game state
        self.level = 1
        self.xp = 0
        self.xp_needed = 100

        self.load_progress()
        self.setup_sounds()
        self.setup_boss()
        self.populate_daily_quests()
        self.update_ui()

    # ------------------ BOSS SYSTEM ------------------

    def setup_boss(self):
        week = datetime.date.today().isocalendar()[1]
        self.boss_data = BOSSES[week % len(BOSSES)]

        self.boss_max_hp = self.boss_data["hp"]
        self.boss_hp = self.boss_max_hp

        self.dashboard.bossName.setText(self.boss_data["name"])
        self.dashboard.bossHpBar.setMaximum(self.boss_max_hp)
        self.dashboard.bossHpBar.setValue(self.boss_hp)

        img_path = os.path.join(BASE_DIR, "assets/bosses", self.boss_data["img"])
        pix = QPixmap(img_path)
        self.dashboard.bossImage.setPixmap(
            pix.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def damage_boss(self, dmg):
        new_hp = max(0, self.boss_hp - dmg)

        anim = QPropertyAnimation(self.dashboard.bossHpBar, b"value")
        anim.setDuration(500)
        anim.setStartValue(self.boss_hp)
        anim.setEndValue(new_hp)
        anim.start()

        self.boss_hp = new_hp

    # ------------------ XP SYSTEM ------------------

    def add_xp(self, amount):
        self.xp += amount
        self.complete_sound.play()

        if self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            self.xp_needed = int(self.xp_needed * 1.2)
            self.levelup_sound.play()

        self.update_ui()
        self.save_progress()

    # ------------------ DAILY QUESTS ------------------

    def populate_daily_quests(self):
        layout = self.daily.dailyList

        # Clear old
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for text, xp, dmg in DAILY_QUESTS:
            row = QWidget()
            row_layout = QHBoxLayout(row)

            label = QLabel(text)
            btn = QPushButton("Complete")
            btn.clicked.connect(lambda _, x=xp, d=dmg: self.complete_quest(x, d))

            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(btn)

            layout.addWidget(row)

    def complete_quest(self, xp, dmg):
        self.add_xp(xp)
        self.damage_boss(dmg)

    # ------------------ SAVE SYSTEM ------------------

    def save_progress(self):
        data = {
            "level": self.level,
            "xp": self.xp,
            "xp_needed": self.xp_needed
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

    # ------------------ UI UPDATE ------------------

    def update_ui(self):
        self.dashboard.levelLabel.setText(f"Level {self.level}")
        self.dashboard.xpBar.setMaximum(self.xp_needed)
        self.dashboard.xpBar.setValue(self.xp)

    # ------------------ SOUND ------------------

    def setup_sounds(self):
        self.complete_sound = QSoundEffect()
        self.complete_sound.setSource(QUrl.fromLocalFile(
            os.path.join(BASE_DIR, "assets/sounds/complete.wav")
        ))

        self.levelup_sound = QSoundEffect()
        self.levelup_sound.setSource(QUrl.fromLocalFile(
            os.path.join(BASE_DIR, "assets/sounds/levelup.wav")
        ))


# ------------------ RUN ------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
