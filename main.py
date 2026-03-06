import sys, os, json, datetime, random
from PyQt6 import uic
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QPropertyAnimation, QPoint, QTimer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "save.json")

BOSSES = [
"🐉 Dragon of Procrastination",
"🕷 Spider of Distraction",
"😈 Demon of Burnout",
"👹 Ogre of Laziness",
"🦹 Villain of Overwhelm",
]

MOTIVATION = [
"Stay focused. The boss fears productivity.",
"Small progress is still progress.",
"Every task is damage to the boss.",
"Discipline beats motivation.",
"Keep going. You're leveling up."
]


class GameState:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.xp_needed = 100
        self.gold = 0
        self.tasks = []
        self.streak = 0

        self.stats = {"strength":1,"focus":1,"luck":1}

        self.upgrades = {
            "sword":False,
            "xp_boost":False,
            "gold_boost":False
        }


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        uic.loadUi(os.path.join(BASE_DIR,"ui","main_window.ui"),self)

        self.game = GameState()

        self.load_game()

        self.animations = []

        # UI style
        self.setStyleSheet("""
        QMainWindow { background:#1e1e2e; color:white; font-family:Segoe UI;}
        QPushButton {
            background-color:#313244;
            border-radius:10px;
            padding:14px;
            font-size:15px;
        }
        QPushButton:hover {background:#45475a;}
        QPushButton:pressed {background:#585b70;}

        QFrame {background:#2a2b3d;border-radius:10px;padding:10px;}

        QProgressBar {
            border:none;
            background:#45475a;
            border-radius:6px;
            text-align:center;
        }

        QProgressBar::chunk {
            background:#89b4fa;
            border-radius:6px;
        }
        """)

        self.bossHpBar.setStyleSheet("""
        QProgressBar::chunk {background:#f38ba8;}
        """)

        self.setup_navigation()
        self.setup_boss()
        self.setup_shop()
        self.setup_tasks()
        self.populate_tasks()
        self.generate_daily_quests()

        # motivation refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_motivation)
        self.timer.start(10000)

        self.update_ui()

    # ---------------------------
    # NAVIGATION
    # ---------------------------

    def setup_navigation(self):
        self.btnDashboard.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageDashboard))
        self.btnDaily.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageDaily))
        self.btnTasks.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageTasks))
        self.btnShop.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageShop))

    # ---------------------------
    # BOSS
    # ---------------------------

    def setup_boss(self):

        week = datetime.date.today().isocalendar()[1]
        self.boss_name = BOSSES[week % len(BOSSES)]

        self.boss_max_hp = 200 + self.game.level * 50
        self.boss_hp = self.boss_max_hp

        self.bossName.setText(self.boss_name)
        self.bossHpBar.setMaximum(self.boss_max_hp)
        self.bossHpBar.setValue(self.boss_hp)

    def damage_boss(self, dmg):

        # strength bonus
        dmg += self.game.stats["strength"]

        if self.game.upgrades["sword"]:
            dmg += 5

        old = self.boss_hp
        self.boss_hp = max(0,self.boss_hp-dmg)

        anim = QPropertyAnimation(self.bossHpBar,b"value")
        anim.setDuration(400)
        anim.setStartValue(old)
        anim.setEndValue(self.boss_hp)
        anim.start()

        self.animations.append(anim)

        self.show_damage_popup(dmg)

        if self.boss_hp == 0:

            reward = random.randint(100,200)

            if self.game.upgrades["gold_boost"]:
                reward = int(reward * 1.5)

            self.game.gold += reward

            QMessageBox.information(
                self,
                "Boss Defeated!",
                f"You defeated {self.boss_name}\nReward: {reward} gold"
            )

            self.setup_boss()

    # ---------------------------
    # DAMAGE POPUP
    # ---------------------------

    def show_damage_popup(self,dmg):

        label = QLabel(f"-{dmg}",self)
        label.setStyleSheet("""
        color:#f38ba8;
        font-size:22px;
        font-weight:bold;
        """)
        label.adjustSize()

        start_x = self.bossHpBar.x() + 200
        start_y = self.bossHpBar.y() - 10

        label.move(start_x,start_y)
        label.show()

        anim = QPropertyAnimation(label,b"pos")
        anim.setDuration(800)
        anim.setStartValue(QPoint(start_x,start_y))
        anim.setEndValue(QPoint(start_x,start_y-40))
        anim.start()

        self.animations.append(anim)

        QTimer.singleShot(800,label.deleteLater)

    # ---------------------------
    # SHOP
    # ---------------------------

    def setup_shop(self):

        self.btnSword.clicked.connect(lambda:self.buy("sword",200))
        self.btnXP.clicked.connect(lambda:self.buy("xp_boost",150))
        self.btnGold.clicked.connect(lambda:self.buy("gold_boost",150))

    def buy(self,name,cost):

        if self.game.gold < cost:
            QMessageBox.information(self,"Shop","Not enough gold")
            return

        if self.game.upgrades[name]:
            QMessageBox.information(self,"Shop","Already owned")
            return

        self.game.gold -= cost
        self.game.upgrades[name]=True

        QMessageBox.information(self,"Shop","Purchased!")

        self.update_ui()
        self.save_game()

    # ---------------------------
    # TASKS
    # ---------------------------

    def setup_tasks(self):

        row=QWidget()
        r=QHBoxLayout(row)

        self.taskName=QLineEdit()
        self.taskName.setPlaceholderText("Task name")

        self.taskXP=QSpinBox()
        self.taskXP.setValue(20)

        self.taskDMG=QSpinBox()
        self.taskDMG.setValue(10)

        add=QPushButton("Add Task")
        add.clicked.connect(self.create_task)

        r.addWidget(self.taskName)
        r.addWidget(self.taskXP)
        r.addWidget(self.taskDMG)
        r.addWidget(add)

        self.tasksContainerLayout.addWidget(row)

    def create_task(self):

        name=self.taskName.text()
        if not name:
            return

        xp=self.taskXP.value()
        dmg=self.taskDMG.value()

        task={"name":name,"xp":xp,"dmg":dmg}

        self.game.tasks.append(task)

        self.populate_tasks()
        self.save_game()

    def populate_tasks(self):

        layout=self.tasksContainerLayout

        while layout.count()>1:
            item=layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for task in self.game.tasks:

            row=QWidget()
            r=QHBoxLayout(row)

            label=QLabel(f"{task['name']} (+{task['xp']}XP)")
            btn=QPushButton("Complete")

            btn.clicked.connect(lambda _,t=task:self.complete_task(t))

            r.addWidget(label)
            r.addWidget(btn)

            layout.addWidget(row)

    def complete_task(self,task):

        xp = task["xp"]

        if self.game.upgrades["xp_boost"]:
            xp = int(xp*1.5)

        self.game.xp += xp
        self.game.gold += 10
        self.game.streak += 1

        self.damage_boss(task["dmg"])

        self.game.tasks.remove(task)

        self.populate_tasks()

        self.check_level_up()

        self.update_ui()
        self.save_game()

    # ---------------------------
    # DAILY QUESTS
    # ---------------------------

    def generate_daily_quests(self):

        quests = [
        ("Study 30 minutes",30,20),
        ("Exercise",25,15),
        ("Read book",20,10),
        ("Clean workspace",15,10),
        ("Practice coding",35,25)
        ]

        layout=self.dailyTasksLayout

        for name,xp,dmg in quests:

            row=QWidget()
            r=QHBoxLayout(row)

            label=QLabel(f"{name} (+{xp}XP)")
            btn=QPushButton("Complete")

            btn.clicked.connect(lambda _,t=(name,xp,dmg): self.complete_daily(t))

            r.addWidget(label)
            r.addWidget(btn)

            layout.addWidget(row)

    def complete_daily(self,quest):

        name,xp,dmg = quest

        self.game.xp += xp
        self.damage_boss(dmg)

        self.check_level_up()

        self.update_ui()
        self.save_game()

    # ---------------------------
    # LEVEL
    # ---------------------------

    def check_level_up(self):

        while self.game.xp >= self.game.xp_needed:

            self.game.xp -= self.game.xp_needed
            self.game.level += 1
            self.game.xp_needed = int(self.game.xp_needed * 1.3)

            self.game.stats["strength"] += 1
            self.game.stats["focus"] += 1
            self.game.stats["luck"] += 1

            QMessageBox.information(self,"LEVEL UP",f"You reached level {self.game.level}!")

    # ---------------------------
    # SAVE
    # ---------------------------

    def save_game(self):

        data = {
            "level":self.game.level,
            "xp":self.game.xp,
            "gold":self.game.gold,
            "tasks":self.game.tasks
        }

        with open(SAVE_FILE,"w") as f:
            json.dump(data,f)

    def load_game(self):

        if os.path.exists(SAVE_FILE):

            with open(SAVE_FILE,"r") as f:
                data=json.load(f)

            self.game.level=data.get("level",1)
            self.game.xp=data.get("xp",0)
            self.game.gold=data.get("gold",0)
            self.game.tasks=data.get("tasks",[])

    # ---------------------------
    # UI
    # ---------------------------

    def update_ui(self):

        self.levelLabel.setText(f"Level {self.game.level}")
        self.goldLabel.setText(f"Gold: {self.game.gold}")

        self.xpBar.setMaximum(self.game.xp_needed)

        anim = QPropertyAnimation(self.xpBar,b"value")
        anim.setDuration(400)
        anim.setStartValue(self.xpBar.value())
        anim.setEndValue(self.game.xp)
        anim.start()

        self.animations.append(anim)

        self.statsLabel.setText(
        f"Strength:{self.game.stats['strength']}  "
        f"Focus:{self.game.stats['focus']}  "
        f"Luck:{self.game.stats['luck']}"
        )

        self.streakLabel.setText(f"Streak: {self.game.streak}")

        quote = random.choice(MOTIVATION)
        self.motivationLabel.setText(f'"{quote}"')

    def update_motivation(self):
        self.motivationLabel.setText(random.choice(MOTIVATION))


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())