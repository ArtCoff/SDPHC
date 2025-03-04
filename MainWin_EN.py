import sys
from enum import Enum
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
)
from PredefinedData import software_name, Methods
from Pyside6Functions import center_window, title_font
from CustomControl import (
    file_line_edit,
    next_btn,
    help_btn,
    CustomRadioButtons,
    LanguageSwitcher,
)
from Method_ExperienceValue import Attribute_Window
from Method_BackgroundValue import Attribute_Window_BackgroundValue
from Method_PCA import Attribute_Window_PCA


class Start_Window(QWidget):
    def __init__(self, parent=None):
        super(Start_Window, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setWindowTitle(self.tr(software_name))

        self.setMinimumSize(400, 300)
        self.language_switcher = LanguageSwitcher()
        self.current_language = "EN"
        self.language_switcher.language_changed.connect(self.update_language)
        form_layout = QFormLayout()
        self.outline_dataset = file_line_edit()
        self.point_dataset = file_line_edit()
        self.method = CustomRadioButtons()
        self.current_method_status = Methods.Experience_value_method
        self.method.current_method.connect(self.update_method)
        self.help_btn = help_btn()
        self.next_btn = next_btn()
        form_layout.addRow(self.tr("Site boundary file:"), self.outline_dataset)
        form_layout.addRow(self.tr("Survey site file:"), self.point_dataset)
        form_layout.addRow(self.tr("Method:"), self.method)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(
            self.language_switcher, alignment=Qt.AlignTop | Qt.AlignLeft
        )
        btn_layout.addStretch(90)
        btn_layout.addWidget(self.help_btn, alignment=Qt.AlignRight)
        btn_layout.addStretch(2)
        btn_layout.addWidget(self.next_btn, alignment=Qt.AlignRight)
        btn_layout.addStretch(8)
        self.help_btn.clicked.connect(self.on_help_clicked)
        self.next_btn.clicked.connect(self.on_next_clicked)
        # 总体布局
        v_layput = QVBoxLayout()
        v_layput.addLayout(form_layout)
        v_layput.addStretch()
        v_layput.addLayout(btn_layout)

        self.setLayout(v_layput)
        center_window(self)

    def on_help_clicked(self):
        msg_box = QMessageBox(self)
        # msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(self.tr("Help"))  # 设置标题
        msg_box.setText(
            self.tr(
                """
            Click the input box to open the file explorer and select the input.\n
            Supports GPKG and SHP files(GPKG recommended).\n
            """
            )
        )
        msg_box.setStandardButtons(QMessageBox.Ok)

        # 显示消息框
        msg_box.exec_()

    def on_next_clicked(self):
        if not self.point_dataset.text():
            QMessageBox.critical(
                self, "Dataset Error", self.tr("Survey point data should not be empty.")
            )
            return
        self.hide()
        if self.current_method_status == Methods.Experience_value_method:
            self.attribute_window = Attribute_Window(
                point_dataset=self.point_dataset.text(),
                outline_dataset=self.outline_dataset.text(),
            )
            self.attribute_window.show()
        elif self.current_method_status == Methods.Background_value_method:
            self.KmeansWin = Attribute_Window_BackgroundValue(
                self.point_dataset.text(),
                self.outline_dataset.text(),
            )
            self.KmeansWin.show()
        elif self.current_method_status == Methods.PCA_method:
            self.attribute_window_PCA = Attribute_Window_PCA(
                self.point_dataset.text(),
                self.outline_dataset.text(),
            )
            self.attribute_window_PCA.show()

    def update_method(self, method):
        self.current_method_status = method

    def update_language(self, language):
        self.current_language = language
        print(self.current_language)
        # self.language_switcher.update_button_text()


if __name__ == "__main__":
    import os

    os.environ["QT_SCALE_FACTOR"] = "1.00"
    app = QApplication(sys.argv)

    # 正确获取主屏幕
    # screen = app.primaryScreen()
    # scale_factor = screen.devicePixelRatio()
    # print(f"Scale Factor: {scale_factor}")
    app.setFont(QFont("Arial", 12))
    main = Start_Window()
    main.show()
    sys.exit(app.exec())
