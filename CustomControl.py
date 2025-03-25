import sys
from enum import Enum
from PySide6.QtCore import (
    Qt,
    QEvent,
    QAbstractTableModel,
    Signal,
    QTranslator,
    QPoint,
    QSettings,
)
from PySide6.QtGui import QFont, QIcon
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
    QProgressBar,
)
from PredefinedData import Methods
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
)
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from Pyside6Functions import center_window


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
    def __init__(self, options, attribute, parent=None):
        super().__init__(parent)
        self.options = options
        self.attribute = attribute
        self.addItems(["No data available"])
        if self.options:
            self.addItems(options)
        self._set_current_index()

    def _set_current_index(self):
        if self.attribute in self.options:
            index = self.options.index(self.attribute) + 1
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(0)
        # if self.attribute == "Point_ID":
        #     self.setCurrentIndex(1)
        # else:
        #     if self.attribute.value.name in self.options:
        #         index = self.options.index(self.attribute.value.name) + 1
        #         self.setCurrentIndex(index)
        #     else:
        #         self.setCurrentIndex(0)


class background_value_input_doublespinbox(QDoubleSpinBox):
    def __init__(self, range):
        super().__init__()
        self.setRange(0.0, range)
        self.setDecimals(4)


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
        self.current_language = "en"  # 默认语言
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # 加载初始翻译
        self.load_translation(self.current_language)

    def switch_language(self):
        # 切换语言
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        settings = QSettings("HFUT", "MIM_GUI")
        settings.setValue("language", self.current_language)
        self.load_translation(self.current_language)
        self.update_button_text()
        self.language_changed.emit(self.current_language)  # 发射语言切换信号

    def load_translation(self, language):
        # 加载翻译文件
        QApplication.instance().removeTranslator(self.translator_zh)
        QApplication.instance().removeTranslator(self.translator_en)
        if language == "zh":
            self.translator_zh.load("zh_CN.qm")
            QApplication.instance().installTranslator(self.translator_zh)
        else:
            self.translator_en.load("en_US.qm")
            QApplication.instance().installTranslator(self.translator_en)

    def update_button_text(self):
        # 更新按钮文本
        if self.current_language == "zh":
            self.language_button.setText("EN")
        else:
            self.language_button.setText("中文")

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.update_button_text()
        super().changeEvent(event)


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


class bottom_buttons(QWidget):
    help_btn_clicked = Signal()
    next_btn_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.help_btn = help_btn()
        self.next_btn = next_btn()
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch(90)
        self.btn_layout.addWidget(self.help_btn, alignment=Qt.AlignRight)
        self.btn_layout.addStretch(2)
        self.btn_layout.addWidget(self.next_btn, alignment=Qt.AlignRight)
        self.next_btn.clicked.connect(self.next_btn_clicked.emit)
        self.help_btn.clicked.connect(self.help_btn_clicked.emit)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.btn_layout)


class LoadingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setWindowTitle("Loading")
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # 置顶显示
        self.setWindowFlag(Qt.FramelessWindowHint)  # 无边框
        self.setWindowModality(Qt.ApplicationModal)  # 模态窗口
        self.resize(300, 100)
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        self.close_btn = QPushButton("x")
        self.close_btn.setFont(QFont("Arial", 12))
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_btn)
        title_bar.setLayout(title_bar_layout)
        ###
        layout = QVBoxLayout()
        self.label = QLabel("Processing, please wait...")
        self.label.setFont(QFont("Arial", 10))
        self.label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 不确定模式（持续滚动）
        self.progress.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_bar)
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        center_window(self)

        self.draggable = True
        self.drag_position = QPoint()

    # 鼠标事件：拖动窗口
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draggable:
            # 将 QPointF 转换为 QPoint
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.draggable:
            # 使用 globalPosition
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class PlotWindow(QWidget):
    def __init__(self, fig):
        super().__init__()
        self.setWindowTitle("Data Visualization")
        self.setGeometry(100, 100, 400, 300)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setMinimumSize(400, 300)

        # 创建绘图区域
        self.canvas = None
        self.toolbar = None
        self.fig = fig
        # 安全初始化
        if not self.fig:
            QMessageBox.critical(self, "Error", self.tr("Invalid graphic objects"))
            self.close()

        # 设置界面
        self.setup_ui()

    def setup_ui(self):
        # 创建 FigureCanvas 对象
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
