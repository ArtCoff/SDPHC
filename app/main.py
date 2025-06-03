import sys
from pathlib import Path
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
)
from utils.predefined_data import Software_info, Methods
from utils.pyside6_utils import AppStyle, center_window, load_settings
from gui.custom_controls import (
    file_line_edit,
    next_btn,
    help_btn,
    CustomRadioButtons,
    LanguageSwitcher,
)
from gui.empirical_threshold_analysis import Attribute_Window
from gui.background_level_analysis import Attribute_Window_BackgroundValue
from gui.principal_component_analysis import Attribute_Window_PCA


class start_window(QWidget):
    def __init__(self, parent=None):
        super(start_window, self).__init__(parent)
        self.initUI()
        self.attribute_window_factory = {
            Methods.Empirical_Threshold_Analysis: Attribute_Window,
            Methods.Background_Level_Analysis: Attribute_Window_BackgroundValue,
            Methods.Principal_Component_Analysis: Attribute_Window_PCA,
        }
        self.current_attribute_window = None

    def initUI(self):
        self.setWindowIcon(AppStyle.icon())
        self.setWindowTitle(self.tr(Software_info.software_name.value))
        self.resize(600, 300)
        self.setMinimumSize(400, 300)

        self.help_btn = help_btn()
        self.next_btn = next_btn()
        self.outline_dataset = file_line_edit()
        self.point_dataset = file_line_edit()
        self.method_radiobtns = CustomRadioButtons()
        self.language_switcher = LanguageSwitcher()

        #! Default settings for boundary file and point data file paths used for testing
        test = False
        # test_boundary = (
        #     Path.cwd().joinpath("tests/JN_boundary.gpkg").resolve().as_posix()
        # )
        # test_nis = Path.cwd().joinpath("tests/JN_NIS.gpkg").resolve().as_posix()
        # test_boundary = Path.cwd().joinpath("tests/_boundary.gpkg").resolve().as_posix()
        # test_nis = Path.cwd().joinpath("tests/_NIS.gpkg").resolve().as_posix()
        if test:
            self.outline_dataset.setText(test_boundary)
            self.point_dataset.setText(test_nis)
        #!
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Boundary File:"), self.outline_dataset)
        form_layout.addRow(self.tr("Survey File:"), self.point_dataset)
        form_layout.addRow(self.tr("Analysis Methods:"), self.method_radiobtns)
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
        v_layout = QVBoxLayout()
        v_layout.addLayout(form_layout)
        v_layout.addStretch()
        v_layout.addLayout(btn_layout)

        self.setLayout(v_layout)
        center_window(self)

    def on_help_clicked(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(self.tr("Help"))
        msg_box.setText(
            self.tr(
                """
            Click the input box to open the file explorer and select the input.\n
            Supports GPKG and SHP files(GPKG recommended).\n
            """
            )
        )
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def on_next_clicked(self):
        if not self.point_dataset.text():
            QMessageBox.critical(
                self,
                self.tr("Data Error"),
                self.tr("Survey point data should not be empty."),
            )
            return
        attribute_window_class = self.attribute_window_factory.get(
            self.method_radiobtns.get_method
        )
        if not attribute_window_class:
            QMessageBox.critical(self, "Error", "Unsupported method selected")
            return
        attribute_window_args = {
            "point_dataset": self.point_dataset.text(),
            "outline_dataset": self.outline_dataset.text(),
            "method": self.method_radiobtns.get_method,
        }
        # 如果当前有窗口打开，关闭当前窗口
        if self.current_attribute_window:
            self.current_attribute_window.close()
        self.current_attribute_window = attribute_window_class(**attribute_window_args)
        self.current_attribute_window.show()
        self.close()


if __name__ == "__main__":
    import os

    settings = load_settings()
    # Scaling issues can be solved by setting the value of QT_SCALE_FACTOR
    qt_scale_factor = settings.get("QT_SCALE_FACTOR", "1.00")
    os.environ["QT_SCALE_FACTOR"] = qt_scale_factor
    app = QApplication(sys.argv)

    # internationalization
    trans = QTranslator()
    lang = settings.get("DEFAULT_LANG", "en_US")
    trans.load(f"./assets/locales/{lang}.qm")
    app.installTranslator(trans)
    # set application style
    # app.setStyle("Windows")
    font_family = settings.get("FONT_FAMILY", "Arial")
    font_size = int(settings.get("FONT_SIZE", "12"))
    app.setFont(QFont(font_family, font_size))
    main = start_window()
    main.show()
    sys.exit(app.exec())
