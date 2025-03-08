import sys
from enum import Enum
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QTranslator
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QTableView,
    QLabel,
    QWidget,
    QComboBox,
    QPushButton,
    QRadioButton,
    QDoubleSpinBox,
    QPlainTextEdit,
    QLineEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
)
from PredefinedData import Methods


class file_line_edit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click to select the file")
        self.mousePressEvent = self.open_file_dialog
        self.setStyleSheet("QLineEdit:hover {border:1px ridge black}")

    def open_file_dialog(self, event):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(
            "GPKG File(*.gpkg);;SHP File (*.shp);",
        )
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.setText(file_path)


class next_btn(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(90, 30)
        self.setText("Next ⏩")
        self.setFont(QFont("Segoe UI", 12))
        self.setStyleSheet(
            """
            QPushButton{
                border: 1px solid #8f8f91;
                border-radius: 1px;
                background-color: #dbdbdb;
            }
            QPushButton:hover {
                background-color: soild darkgray;  
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            """
        )


class help_btn(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(90, 30)
        self.setText("Help ❓")
        self.setFont(QFont("Segoe UI", 12))
        self.setStyleSheet(
            """
            QPushButton{
                border: 1px solid #8f8f91;
                border-radius: 1px;
                background-color: #dbdbdb;
            }
            QPushButton:hover {
                background-color: soild darkgray;  
            }"""
        )


class check_btn(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(90, 30)
        self.setText("Quit")
        self.setFont(QFont("Segoe UI", 12))
        self.setStyleSheet(
            """
            QPushButton{
                border: 1px solid #8f8f91;
                border-radius: 1px;
                background-color: #dbdbdb;
            }
            QPushButton:hover {
                background-color: soild darkgray;  
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            """
        )


class CustomComboBox(QComboBox):
    def __init__(self, options, index, parent=None):
        super().__init__(parent)
        self.addItems(options)
        self.addItems(["No data available"])
        self.index = index


# class CustomComboBox_v2(QComboBox):
#     def __init__(self, options, index, parent=None):
#         super().__init__(parent)
#         self.addItems(options)
#         self.addItems(["No data available"])
#         self.index = index


class CustomRadioButtons(QWidget):
    current_method = Signal(Enum)

    def __init__(self):
        super().__init__()
        self.radiobutton1 = QRadioButton("Experience value method")
        self.radiobutton2 = QRadioButton("Background value method")
        self.radiobutton3 = QRadioButton("PCA method")
        self.radiobutton1.setChecked(True)
        self.radiobutton1.toggled.connect(self.on_radio_button_toggled)
        self.radiobutton2.toggled.connect(self.on_radio_button_toggled)
        self.radiobutton3.toggled.connect(self.on_radio_button_toggled)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.radiobutton1)
        hlayout.addWidget(self.radiobutton2)
        hlayout.addWidget(self.radiobutton3)
        self.setLayout(hlayout)

    def on_radio_button_toggled(self):
        radiobutton = self.sender()
        if radiobutton.isChecked():
            print(type(Methods(radiobutton.text())))
            self.current_method.emit(Methods(radiobutton.text()))


class WrapButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        # 创建一个 QLabel 来承载按钮的文本
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)

        # 创建一个布局来放置 QLabel
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)


class WrapButton_EN(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        # 设置按钮的文本
        self.setText(text)

        # 设置按钮的样式
        self.setStyleSheet(
            """
            QPushButton {
                background-color: lightgray;
                border: 1px solid #A0A0A0;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                color: black;
            }
            QPushButton:hover {
                 background-color: soild darkgray;
            }
        """
        )

        # 设置按钮为 flat，避免显示默认的 3D 效果
        self.setFlat(True)


class LanguageSwitcher(QWidget):
    language_changed = Signal(str)  # 语言切换信号

    def __init__(self):
        super().__init__()
        self.translator_zh = QTranslator()
        self.translator_en = QTranslator()
        self.current_language = "zh"  # 默认语言
        self.initUI()

    def initUI(self):
        # 主布局
        self.layout = QVBoxLayout()

        # 语言切换按钮
        self.language_button = QPushButton()
        self.language_button.setFixedSize(60, 30)  # 设置按钮大小
        self.language_button.setFont(QFont("Arial", 10))
        self.update_button_text()
        self.language_button.clicked.connect(self.switch_language)

        # 添加到布局
        self.layout.addWidget(self.language_button)
        self.setLayout(self.layout)

        # 加载初始翻译
        self.load_translation(self.current_language)

    def switch_language(self):
        # 切换语言
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        self.load_translation(self.current_language)
        self.update_button_text()
        self.language_changed.emit(self.current_language)  # 发射语言切换信号

    def load_translation(self, language):
        # 加载翻译文件
        QApplication.instance().removeTranslator(self.translator_zh)
        QApplication.instance().removeTranslator(self.translator_en)
        if language == "zh":
            self.translator_zh.load("translation_zh.qm")
            QApplication.instance().installTranslator(self.translator_zh)
        else:
            self.translator_en.load("translation_en.qm")
            QApplication.instance().installTranslator(self.translator_en)

    def update_button_text(self):
        # 更新按钮文本
        if self.current_language == "zh":
            self.language_button.setText("EN")
        else:
            self.language_button.setText("中文")


class GeoDataFrameModel(QAbstractTableModel):
    def __init__(self, gdf, columns_to_display):
        super().__init__()

        self._gdf = gdf
        self._columns_to_display = columns_to_display

    def rowCount(self, parent=None):
        return len(self._gdf)

    def columnCount(self, parent=None):
        return len(self._columns_to_display)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            column_name = self._columns_to_display[index.column()]
            return str(self._gdf.iloc[index.row()][column_name])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._columns_to_display[section]
            if orientation == Qt.Vertical:
                return str(self._gdf.index[section])
        return None


class Interpolation_method_selection(QWidget):
    Interpolation_method = Signal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout()
        self.label = QLabel("Interpolation method:")

        self.combobox = QComboBox()
        self.combobox.addItems(
            [
                "Nearest",
                "Cubic",
                "IDW",
                "Kriging",
            ]
        )
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combobox)
        self.setLayout(self.layout)
        self.combobox.currentIndexChanged.connect(self.update_interpolation_method)

    def update_interpolation_method(self):
        self.Interpolation_method.emit(self.combobox.currentText())
