import re
from PySide6.QtCore import Qt, QAbstractTableModel, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QLayout,
    QLayoutItem,
    QWidget,
)


class AppStyle:
    @staticmethod
    def icon():
        return QIcon(r"./resources/icon.ico")

    @staticmethod
    def title():
        return QFont("Arial", 12, QFont.Bold)

    @staticmethod
    def body():
        return QFont("Segoe UI", 10)


# 读取配置文件 settings.txt 的函数
def load_settings():
    """
    从 settings.txt 文件中读取配置参数。
    :return: 配置字典
    """
    import os

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


def center_window(window):
    """
    将窗口置于屏幕中央
    """
    # 获取主屏幕
    screen = QApplication.primaryScreen()
    # 获取屏幕的几何尺寸
    screen_geometry = screen.availableGeometry()
    # 计算中心点
    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2
    window.move(screen_geometry.x() + x, screen_geometry.y() + y)


def traverse_layout(layout: QLayout, callback):
    """
    递归遍历布局中的所有部件和子布局
    :param layout: 要遍历的布局（QLayout）
    :param callback: 对每个部件执行的回调函数（接收 QWidget 参数）
    """
    collected = []
    for i in range(layout.count()):
        item: QLayoutItem = layout.itemAt(i)
        widget: QWidget = item.widget()
        child_layout: QLayout = item.layout()

        if widget:  # 如果是部件
            result = callback(widget)
            collected.append(result)
        elif child_layout:  # 如果是子布局
            collected.extend(traverse_layout_collect(child_layout, callback))
    return collected


def show_multiple_plots(figs):
    """
    显示多个 Figure 对象，每个图表在独立窗口
    :param figs: list[Figure]
    """
    from matplotlib.figure import Figure
    from app.CustomControl import PlotWindow

    if isinstance(figs, Figure):
        figs = [figs]
    elif not isinstance(figs, list):
        raise TypeError("参数必须是 Figure 或 list[Figure] 类型")
    app = QApplication.instance() or QApplication([])
    app.windows = []
    for i, fig in enumerate(figs):
        window = PlotWindow(fig)
        window.setWindowTitle(f"Plot {i+1} - {window.windowTitle()}")

        # 偏移窗口位置避免完全重叠
        if i > 0:
            window.move(window.x() + 30 * i, window.y() + 30 * i)

        window.show()
        app.windows.append(window)

    app.exec()


def update_config_value(key, new_value, backup=False):
    """
    修改配置文件中指定键的值，支持字符串、数字等类型。

    :param file_path: 配置文件路径
    :param key: 要修改的键（如 "FONT_SIZE"）
    :param new_value: 新值（自动处理引号）
    :param backup: 是否备份原文件（默认 True）
    """
    import os

    # 正则表达式匹配模式：键值对格式如 "KEY"="VALUE"
    pattern = re.compile(rf'^"{key}"\s*=\s*(".*?"|\S+)', re.IGNORECASE)
    lines = []
    updated = False
    file_path = os.path.abspath("settings.txt")
    # 读取文件并逐行处理
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # 匹配目标键
            match = pattern.match(line.strip())
            if match:
                # 构造新行（自动添加引号）
                if isinstance(new_value, str):
                    quoted_value = f'"{new_value}"'
                else:
                    quoted_value = str(new_value)
                new_line = f'"{key}"={quoted_value}\n'
                lines.append(new_line)
                updated = True
            else:
                lines.append(line)

    # 若未找到键，可选择抛出异常或静默处理
    if not updated:
        raise KeyError(f"Key '{key}' not found in {file_path}")

    # 备份原文件
    if backup:
        import shutil

        shutil.copy2(file_path, file_path + ".bak")

    # 写入修改后的内容
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
