import sys
import numpy as np
import h5py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QPushButton, QWidget, QComboBox,
    QLabel, QFileDialog, QStyledItemDelegate, QInputDialog, QHBoxLayout
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem,QBrush, QColor
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class ColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        value = float(index.data(Qt.DisplayRole))
        if value > 0:
            color = QColor(0, 255, 0)  # Зеленый для положительных значений (RGB: 0, 255, 0)
        elif value < 0:
            color = QColor(255, 0, 0)  # Красный для отрицательных значений (RGB: 255, 0, 0)
        else:
            color = QColor(255,255,255)

        painter.fillRect(option.rect, QBrush(color))
        super().paint(painter, option, index)
class DataTable(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Data Table and Plot")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)

        # Создаем таблицу
        self.table_view = QTableView()

        # Создаем модель данных
        self.model = self.createTableModel()
        self.table_view.setModel(self.model)

        # Создаем выпадающий список для первого столбца
        self.createComboBoxDelegateForColumn(0)

        # Устанавливаем делегат для второго столбца
        self.table_view.setItemDelegateForColumn(2, ColorDelegate())

        layout.addWidget(self.table_view)

        # Создаем кнопки
        button_layout = QHBoxLayout()

        save_button = QPushButton("Сохранить данные")
        save_button.clicked.connect(self.saveData)
        button_layout.addWidget(save_button)

        load_button = QPushButton("Загрузить данные")
        load_button.clicked.connect(self.loadData)
        button_layout.addWidget(load_button)

        resize_button = QPushButton("Изменить размер таблицы")
        resize_button.clicked.connect(self.resizeTable)
        button_layout.addWidget(resize_button)

        random_button = QPushButton("Заполнить случайными значениями")
        random_button.clicked.connect(self.fillRandomValues)
        button_layout.addWidget(random_button)

        layout.addLayout(button_layout)

        # Создаем виджет для графика с использованием pyqtgraph
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        # Подключаем события для построения графика
        self.model.itemChanged.connect(self.updateValues)
        self.table_view.selectionModel().selectionChanged.connect(self.plotData)

    def createTableModel(self):
        model = QStandardItemModel(self)
        model.setColumnCount(5)
        model.setRowCount(5)  # Изменено на 5x5
        model.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3", "Column 4", "Column 5"])

        for row in range(model.rowCount()):
            for col in range(model.columnCount()):
                item = QStandardItem("0")  # Устанавливаем значение по умолчанию, например, "0"
                model.setItem(row, col, item)

        return model

    def createComboBoxDelegateForColumn(self, column_index):
        class ComboBoxDelegate(QStyledItemDelegate):
            def createEditor(self, parent, option, index):
                combo = QComboBox(parent)
                combo.addItems(["1", "2", "3", "4", "5"])
                return combo

        combo_delegate = ComboBoxDelegate(self)
        self.table_view.setItemDelegateForColumn(column_index, combo_delegate)
    def saveData(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить данные", "", "HDF5 Files (*.h5)")
        if file_name:
            with h5py.File(file_name, "w") as hf:
                data = np.array([[self.model.item(row, col).text() for col in range(self.model.columnCount())]
                                 for row in range(self.model.rowCount())], dtype=float)
                hf.create_dataset("data", data=data)

    def loadData(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Открыть данные", "", "HDF5 Files (*.h5)")
        if file_name:
            with h5py.File(file_name, "r") as hf:
                data = hf["data"][:]
                rows, cols = data.shape
                self.model.clear()
                self.model.setRowCount(rows)
                self.model.setColumnCount(cols)
                for row in range(rows):
                    for col in range(cols):
                        item = QStandardItem(str(data[row, col]))
                        self.model.setItem(row, col, item)
    def resizeTable(self):
        rows, ok = QInputDialog.getInt(self, "Изменить размер таблицы", "Введите количество строк:",
                                       self.model.rowCount())
        if ok:
            self.model.setRowCount(rows)

    def fillRandomValues(self):
        for row in range(self.model.rowCount()):
            for col in range(self.model.columnCount()):
                if col != 2:  # Пропускаем столбец, в котором считается сумма
                    item = QStandardItem(str(np.random.randint(1, 6)))
                    self.model.setItem(row, col, item)

    def updateValues(self, item):
        row = item.row()
        col = item.column()

        if col == 1:  # Если изменена ячейка во 2 столбце, пересчитываем значение в 3 столбце
            value = float(item.text())
            sin_value = np.sin(value)
            self.model.setItem(row, 2, QStandardItem(str(sin_value)))

        if col == 0:  # Если изменена ячейка в 1 столбце, пересчитываем значения в 4 столбце
            sum_values = []
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                if item is not None and item.text() is not None:
                    sum_value = sum(float(self.model.item(j, 0).text()) for j in range(i + 1))
                    sum_values.append(sum_value)
                else:
                    sum_values.append(None)

            for i, sum_value in enumerate(sum_values):
                if sum_value is not None:
                    self.model.setItem(i, 3, QStandardItem(str(sum_value)))

    def plotData(self):
        selected_indexes = self.table_view.selectionModel().selectedIndexes()

        # Проверяем, что выбрано как минимум два элемента
        if len(selected_indexes) < 2:
            return

        x_col = selected_indexes[0].column()  # Индекс первого выбранного столбца
        y_col = selected_indexes[1].column()  # Индекс второго выбранного столбца

        x_values = [float(self.model.item(row, x_col).text()) for row in range(self.model.rowCount())]
        y_values = [float(self.model.item(row, y_col).text()) for row in range(self.model.rowCount())]

        self.plot_widget.clear()
        self.plot_widget.plot(x_values, y_values, pen='b')


def main():
    app = QApplication(sys.argv)
    window = DataTable()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
