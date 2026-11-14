from PyQt6.QtWidgets import (QApplication, QWidget, QTableWidgetItem, QDialog,
                             QMessageBox, QAbstractItemView)
from PyQt6 import uic
import sys
import sqlite3 as sl


class Dialog(QDialog):
    def __init__(
            self, par, variety=None, roast=None, tp=None,
            desc=None, price=None, vol=None, redact=False
    ):
        super().__init__(par)
        self.par = par
        dialog_name = "addEditCoffeeForm.ui"
        uic.loadUi(dialog_name, self)
        self.type_combo.addItems(["", "Молотый", "В зернах"])
        if redact:
            self.variety_edit.setText(variety)
            self.roast_edit.setText(roast)
            self.type_combo.setCurrentText(tp)
            self.desc_edit.setPlainText(desc)
            self.price_edit.setText(price)
            self.volume_edit.setText(vol)
        self.initUI()

    def initUI(self):
        self.ok_btn.clicked.connect(self.check)
        self.cancel_btn.clicked.connect(self.reject)

    def check(self):
        tp = self.type_combo.currentText()
        if not tp:
            QMessageBox.warning(self, 'Ошибка', 'Выберите тип')
            return
        try:
            var = self.variety_edit.text().strip()
            roast = self.roast_edit.text().strip()
            tp = self.type_combo.currentText()
            desc = self.desc_edit.toPlainText().strip()
            price = float(self.price_edit.text().strip())
            vol = float(self.volume_edit.text().strip())
            if not var or not roast or not tp:
                raise ValueError
            self.res_data = var, roast, tp, desc, price, vol
            self.accept()
        except ValueError:
            QMessageBox.warning(
                self, 'Ошибка',
                'Проверьте, что все текстовые поля кроме описания заполнены, '
                'а цена и объем - числа'
            )
            return


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db_name = 'coffee.sqlite'
        uic.loadUi("main.ui", self)
        self.initUI()

    def initUI(self):
        self.upd_btn.clicked.connect(self.upd_table)
        self.add_btn.clicked.connect(self.add)
        self.change_btn.clicked.connect(self.change)

        # устанавливаем выделение по строкам а не по ячейкам
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        # устанавливаем скрол нижнего ползунка по пикселям
        # а не по столбцам таблицы
        self.table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.upd_table()

    def upd_table(self):
        rows, headers = self.get_data()

        self.table.clear()

        if not rows or not headers:
            return

        # задаем параметры для таблицы
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(rows[0]))

        # устанавливаем заголовки
        self.table.setHorizontalHeaderLabels(headers)

        # записываем значения в каждую ячейку
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                display_val = "" if val is None else str(val)
                self.table.setItem(r, c, QTableWidgetItem(display_val))

        # скрываем колонку с id
        self.table.setColumnHidden(0, True)

    def get_data(self):
        rows, headers = self.fetch('SELECT * FROM coffee')
        return rows, headers

    def execute(self, query: str, params: tuple = ()):
        with sl.connect(self.db_name) as con:
            cur = con.cursor()
            cur.execute(query, params)
            con.commit()

    def fetch(
            self, query: str, params: tuple = ()
    ) -> tuple[list[tuple[str | int, ...]], list[str]]:
        with sl.connect(self.db_name) as con:
            cur = con.cursor()
            cur.execute(query, params)
            headers = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return rows, headers

    def add(self):
        dial = Dialog(self)
        dial.setWindowTitle('Добавление строки')

        if dial.exec() == QDialog.DialogCode.Accepted:
            variety, roast, tp, desc, price, vol = dial.res_data
            self.execute("""
                INSERT INTO
                coffee (variety, roast, type, description, price, volume)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (variety, roast, tp, desc, price, vol))
            self.upd_table()

    def change(self):
        r = self.table.currentRow()
        if r == -1:
            QMessageBox.warning(
                self, 'Предупреждение', 'Выберите строку таблицы')
            return
        id = int(self.table.item(r, 0).text())
        variety = self.table.item(r, 1).text()
        roast = self.table.item(r, 2).text()
        tp = self.table.item(r, 3).text()
        desc = self.table.item(r, 4).text()
        price = self.table.item(r, 5).text()
        vol = self.table.item(r, 6).text()

        dial = Dialog(self, variety, roast, tp, desc, price, vol, redact=True)
        dial.setWindowTitle('Изменение строки')

        if dial.exec() == QDialog.DialogCode.Accepted:
            variety, roast, tp, desc, price, vol = dial.res_data
            self.execute("""
                UPDATE coffee
                SET variety = ?, roast = ?, type = ?,
                description = ?, price = ?, volume = ?
                WHERE id = ?
            """, (variety, roast, tp, desc, price, vol, id))
            self.upd_table()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
