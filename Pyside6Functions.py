import sys
from PySide6.QtCore import Qt, QAbstractTableModel, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLayout,
    QLayoutItem,
    QWidget,
)


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
    # window_geometry = window.frameGeometry()
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
    from CustomControl import PlotWindow

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
