import sys
from enum import Enum
from PySide6.QtCore import Qt, QEvent, QSettings
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
)
from app.PredefinedData import Software_info, Methods
from app.Pyside6Functions import center_window
from app.CustomControl import (
    file_line_edit,
    next_btn,
    help_btn,
    CustomRadioButtons,
    LanguageSwitcher,
    bottom_buttons,
)
from methods.Method_ExperienceValue import Attribute_Window
from methods.Method_BackgroundValue import Attribute_Window_BackgroundValue
from methods.Method_PCA import Attribute_Window_PCA


class Start_Window(QWidget):
    def __init__(self, parent=None):
        super(Start_Window, self).__init__(parent)
        self.initUI()
        self.attribute_window_factory = {
            Methods.Experience_value_method: Attribute_Window,
            Methods.Background_value_method: Attribute_Window_BackgroundValue,
            Methods.PCA_method: Attribute_Window_PCA,
        }
        self.current_attribute_window = None

    def initUI(self):
        # settings = QSettings("HFUT", "MIM_GUI")
        # self.current_language = settings.value("language", "en")
        # self.load_translation(self.current_language)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setWindowTitle(self.tr(Software_info.software_name.value))
        self.resize(600, 400)
        self.setMinimumSize(400, 300)
        self.language_switcher = LanguageSwitcher()
        # self.language_switcher.language_changed.connect(self.update_language)
        form_layout = QFormLayout()
        self.outline_dataset = file_line_edit()
        self.point_dataset = file_line_edit()
        self.method = CustomRadioButtons()
        self.current_method_status = Methods.Experience_value_method
        self.method.current_method.connect(self.update_method)
        #!
        self.outline_dataset.setText(r"C:\Users\Apple\Desktop\MIM\tests\boundary.gpkg")
        self.point_dataset.setText(r"C:\Users\Apple\Desktop\MIM\tests\Lanxing.gpkg")

        #!

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
        # 检查输入数据集
        if not self.point_dataset.text():
            QMessageBox.critical(
                self, "Dataset Error", self.tr("Survey point data should not be empty.")
            )
            return
        attribute_window_class = self.attribute_window_factory.get(
            self.current_method_status
        )
        if not attribute_window_class:
            QMessageBox.critical(self, "Error", "Unsupported method selected")
            return
        attribute_window_args = {
            "point_dataset": self.point_dataset.text(),
            "outline_dataset": self.outline_dataset.text(),
            "method": self.current_method_status,
        }
        # 如果当前有窗口打开，关闭当前窗口
        if self.current_attribute_window:
            self.current_attribute_window.close()
        self.current_attribute_window = attribute_window_class(**attribute_window_args)
        self.current_attribute_window.show()
        self.close()

    def update_method(self, method):
        self.current_method_status = method

    # def update_language(self, lang):
    #     print(f"Switch language to {lang}")
    #     self.update()

    # def load_translation(self, lang):
    #     # 语言切换由 LanguageSwitcher 控制，此处只需初始化
    #     pass  # 主逻辑在 LanguageSwitcher 中

    # def changeEvent(self, event):
    #     # 捕获语言变化事件
    #     if event.type() == QEvent.LanguageChange:
    #         self.restart()
    #     # super().changeEvent(event)

    # def restart(self):
    #     self.close()
    #     new_window = Start_Window()
    #     new_window.show()
    #     self.setParent(new_window)


# 读取配置文件 settings.txt 的函数
def load_settings():
    """
    从 settings.txt 文件中读取配置参数。
    :return: 配置字典
    """
    settings = {}
    settings_path = os.path.abspath("settings.txt")  # 获取根目录下的 settings.txt
    if not os.path.exists(settings_path):
        print("配置文件 settings.txt 不存在，使用默认值。")
        return settings

    with open(settings_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):  # 跳过注释和空行
                try:
                    key, value = line.split("=", 1)  # 分割键值对
                    key = key.strip().strip('"')  # 去除多余的引号和空格
                    value = value.strip().strip('"')
                    settings[key] = value
                except ValueError:
                    print(f"忽略无效配置行：{line}")
    return settings


if __name__ == "__main__":
    import os

    settings = load_settings()
    qt_scale_factor = settings.get("QT_SCALE_FACTOR", "1.00")
    os.environ["QT_SCALE_FACTOR"] = qt_scale_factor
    app = QApplication(sys.argv)
    # app.setStyle("Windows")

    # 正确获取主屏幕
    font_family = settings.get("FONT_FAMILY", "Arial")
    font_size = int(settings.get("FONT_SIZE", "12"))
    app.setFont(QFont(font_family, font_size))
    main = Start_Window()
    main.show()
    sys.exit(app.exec())
