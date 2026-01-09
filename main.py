import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class AddQuestDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(BASE_DIR, "ui/add_quest.ui"), self)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load dashboard UI
        uic.loadUi(os.path.join(BASE_DIR, "ui/dashboard.ui"), self)

        # Boss stats
        self.boss_max_hp = 100
        self.boss_hp = 100

        self.bossHpBar.setMaximum(self.boss_max_hp)
        self.bossHpBar.setValue(self.boss_hp)
        self.bossName.setText("🩸 Weekly Boss: Procrastinator")

        # Connect buttons
        self.addQuestButton.clicked.connect(self.open_add_quest)
        self.completeQuestButton.clicked.connect(self.complete_quest)

    def open_add_quest(self):
        dialog = AddQuestDialog()
        if dialog.exec_():
            quest_name = dialog.questLineEdit.text().strip()
            if quest_name:
                self.questListWidget.addItem(quest_name)

    def complete_quest(self):
        selected = self.questListWidget.currentItem()
        if not selected:
            return

        self.questListWidget.takeItem(
            self.questListWidget.row(selected)
        )

        self.damage_boss(10)

    def damage_boss(self, dmg):
        self.boss_hp -= dmg
        if self.boss_hp < 0:
            self.boss_hp = 0

        self.bossHpBar.setValue(self.boss_hp)

        if self.boss_hp == 0:
            self.bossNameLabel.setText("🏆 Boss Defeated!")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load QSS
    qss_path = os.path.join(BASE_DIR, "styles/dark_game.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
