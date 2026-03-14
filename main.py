import sys, os, json, datetime, random, hashlib
from PyQt6 import uic
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QPropertyAnimation, QPoint, QTimer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAVE_DIR = os.path.join(BASE_DIR, "saves")
USERS_FILE = os.path.join(SAVE_DIR, "users.json")

os.makedirs(SAVE_DIR, exist_ok=True)

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


# GAME STATE

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


# LOGIN WINDOW

class LoginWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        uic.loadUi(os.path.join(BASE_DIR,"ui","login_window.ui"),self)

        self.loginButton.clicked.connect(self.login)

        self.passwordInput.returnPressed.connect(self.login)

        self.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e2e;
        }

        QLineEdit {
            border: none;
        }

        QPushButton {
            font-weight: bold;
        }
        """)

    def hash_password(self,password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):

        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        if not username or not password:
            QMessageBox.warning(self,"Login","Enter username and password")
            return

        password_hash = self.hash_password(password)

        users = {}

        if os.path.exists(USERS_FILE):
            with open(USERS_FILE,"r") as f:
                users = json.load(f)

        if username not in users:

            users[username] = password_hash

            with open(USERS_FILE,"w") as f:
                json.dump(users,f,indent=2)

            QMessageBox.information(self,"Account Created","New account created!")

        else:

            if users[username] != password_hash:
                QMessageBox.warning(self,"Login","Wrong password")
                return

        self.main = MainWindow(username)
        self.main.show()

        self.close()


# MAIN GAME WINDOW

class MainWindow(QMainWindow):

    def __init__(self,username):
        super().__init__()

        self.username = username
        self.save_file = os.path.join(SAVE_DIR,f"{username}.json")

        uic.loadUi(os.path.join(BASE_DIR,"ui","main_window.ui"),self)

        self.game = GameState()

        self.load_game()

        self.animations = []

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_motivation)
        self.timer.start(10000)

        self.update_ui()

    # NAVIGATION

    def setup_navigation(self):
        self.btnDashboard.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageDashboard))
        self.btnDaily.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageDaily))
        self.btnTasks.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageTasks))
        self.btnShop.clicked.connect(lambda: self.pages.setCurrentWidget(self.pageShop))

    # BOSS

    def shake_widget(self, widget):

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(300)

        start = widget.pos()

        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.25, start + QPoint(-10, 0))
        anim.setKeyValueAt(0.5, start + QPoint(10, 0))
        anim.setKeyValueAt(0.75, start + QPoint(-6, 0))
        anim.setKeyValueAt(1, start)

        anim.start()

        self.animations.append(anim)

    def setup_boss(self):

        week = datetime.date.today().isocalendar()[1]
        self.boss_name = BOSSES[week % len(BOSSES)]

        self.boss_max_hp = 200 + self.game.level * 50
        self.boss_hp = self.boss_max_hp

        self.bossName.setText(self.boss_name)
        self.bossHpBar.setMaximum(self.boss_max_hp)
        self.bossHpBar.setValue(self.boss_hp)

    def damage_boss(self,dmg):

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
        self.shake_widget(self.bossHpBar)

        if self.boss_hp == 0:

            reward = random.randint(100,200)

            if self.game.upgrades["gold_boost"]:
                reward = int(reward*1.5)

            self.game.gold += reward

            QMessageBox.information(
                self,
                "Boss Defeated!",
                f"You defeated {self.boss_name}\nReward: {reward} gold"
            )

            self.setup_boss()

    # DAMAGE POPUP

    def show_damage_popup(self,dmg):

        label = QLabel(f"-{dmg}",self)
        label.setStyleSheet("color:#f38ba8;font-size:22px;font-weight:bold;")
        label.adjustSize()

        start_x = self.bossHpBar.x()+200
        start_y = self.bossHpBar.y()-10

        label.move(start_x,start_y)
        label.show()

        anim = QPropertyAnimation(label,b"pos")
        anim.setDuration(800)
        anim.setStartValue(QPoint(start_x,start_y))
        anim.setEndValue(QPoint(start_x,start_y-40))
        anim.start()

        self.animations.append(anim)

        QTimer.singleShot(800,label.deleteLater)

    # XP POPUP

    def show_xp_popup(self, xp):

        label = QLabel(f"+{xp} XP", self)
        label.setStyleSheet("color:#a6e3a1;font-size:18px;font-weight:bold;")
        label.adjustSize()

        start_x = self.xpBar.x() + 150
        start_y = self.xpBar.y() - 10

        label.move(start_x, start_y)
        label.show()

        anim = QPropertyAnimation(label, b"pos")
        anim.setDuration(800)
        anim.setStartValue(QPoint(start_x, start_y))
        anim.setEndValue(QPoint(start_x, start_y - 40))
        anim.start()

        self.animations.append(anim)

        QTimer.singleShot(800, label.deleteLater)

    # SHOP

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

    # TASKS

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

        if len(self.game.tasks) >= 20:
            QMessageBox.information(self,"Tasks","Task limit reached")
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
        self.show_xp_popup(xp)
        self.game.gold += 10
        self.game.streak += 1

        self.damage_boss(task["dmg"])

        self.game.tasks.remove(task)

        self.populate_tasks()

        self.check_level_up()

        self.update_ui()
        self.save_game()

    # DAILY QUESTS

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

    # LEVEL

    def level_up_effect(self):

        self.xpBar.setStyleSheet("""
        QProgressBar::chunk {
            background: gold;
            border-radius:6px;
        }
        """)

        QTimer.singleShot(1200, lambda: self.xpBar.setStyleSheet("""
        QProgressBar::chunk {
            background:#89b4fa;
            border-radius:6px;
        }
        """))

    def check_level_up(self):

        while self.game.xp >= self.game.xp_needed:

            self.game.xp -= self.game.xp_needed
            self.game.level += 1
            self.game.xp_needed = int(self.game.xp_needed * 1.3)

            self.game.stats["strength"] += 1
            self.game.stats["focus"] += 1
            self.game.stats["luck"] += 1

            QMessageBox.information(self,"LEVEL UP",f"You reached level {self.game.level}!")
            self.level_up_effect()

    # SAVE / LOAD

    def save_game(self):

        data = {
            "level":self.game.level,
            "xp":self.game.xp,
            "gold":self.game.gold,
            "tasks":self.game.tasks,
            "stats":self.game.stats,
            "upgrades":self.game.upgrades,
            "streak":self.game.streak
        }

        with open(self.save_file,"w") as f:
            json.dump(data,f,indent=2)

    def load_game(self):

        if os.path.exists(self.save_file):

            with open(self.save_file,"r") as f:
                data=json.load(f)

            self.game.level=data.get("level",1)
            self.game.xp=data.get("xp",0)
            self.game.gold=data.get("gold",0)
            self.game.tasks=data.get("tasks",[])
            self.game.stats=data.get("stats",self.game.stats)
            self.game.upgrades=data.get("upgrades",self.game.upgrades)
            self.game.streak=data.get("streak",0)

    # UI

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

    login = LoginWindow()
    login.show()

    sys.exit(app.exec())