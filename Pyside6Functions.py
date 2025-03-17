import sys
from PySide6.QtCore import Qt, QAbstractTableModel, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLayout,
    QLayoutItem,
    QWidget,
)
from CustomControl import PlotWindow

title_font = QFont("Arial", 12)


def center_window(window):
    """
    将窗口置于屏幕中央
    """
    # 获取主屏幕
    screen = QApplication.primaryScreen()
    # 获取屏幕的几何尺寸
    screen_geometry = screen.availableGeometry()
    # 获取窗口的几何尺寸
    window_geometry = window.frameGeometry()
    # 计算中心点
    center_point = screen_geometry.center()
    # 将窗口的中心点设置为屏幕的中心点
    window_geometry.moveCenter(center_point)
    # 移动窗口到计算后的几何位置
    window.move(window_geometry.topLeft())


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


# def center_window(window, width=None, height=None, position="center"):
#     """
#     将窗口置于屏幕的指定位置（默认为屏幕中央）。

#     参数:
#         window (QWidget): 要调整的窗口对象。
#         width (int, optional): 窗口的目标宽度。如果为 None，则使用窗口当前宽度。
#         height (int, optional): 窗口的目标高度。如果为 None，则使用窗口当前高度。
#         position (str, optional): 窗口的位置选项，支持以下值：
#             - "center": 居中显示（默认）。
#             - "top-left": 左上角。
#             - "top-right": 右上角。
#             - "bottom-left": 左下角。
#             - "bottom-right": 右下角。
#     """
#     # 获取主屏幕或其他屏幕
#     screen = QApplication.primaryScreen()
#     screen_geometry = screen.availableGeometry()  # 获取可用屏幕区域（去掉任务栏等）

#     # 动态调整窗口大小
#     if width is not None and height is not None:
#         window.resize(width, height)  # 设置窗口大小
#     else:
#         width, height = window.width(), window.height()  # 使用当前窗口大小

#     # 计算窗口的目标位置
#     if position == "center":
#         # 居中显示
#         x = (screen_geometry.width() - width) // 2 + screen_geometry.x()
#         y = (screen_geometry.height() - height) // 2 + screen_geometry.y()
#     elif position == "top-left":
#         # 左上角
#         x = screen_geometry.x()
#         y = screen_geometry.y()
#     elif position == "top-right":
#         # 右上角
#         x = screen_geometry.x() + screen_geometry.width() - width
#         y = screen_geometry.y()
#     elif position == "bottom-left":
#         # 左下角
#         x = screen_geometry.x()
#         y = screen_geometry.y() + screen_geometry.height() - height
#     elif position == "bottom-right":
#         # 右下角
#         x = screen_geometry.x() + screen_geometry.width() - width
#         y = screen_geometry.y() + screen_geometry.height() - height
#     else:
#         raise ValueError(f"Unsupported position: {position}")

#     # 移动窗口到目标位置
#     window.move(x, y)


def show_multiple_plots(figs):
    """
    显示多个 Figure 对象，每个图表在独立窗口
    :param figs: list[Figure]
    """
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
