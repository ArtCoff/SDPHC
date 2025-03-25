import sys
from enum import Enum
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QThread, Slot
from PySide6.QtWidgets import (
    QMessageBox,
    QWidget,
    QFrame,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from app.Method_Functions import (
    point_dataset_preprocess,
    process_PCA,
    plot_PCA_variance_contribution,
    plot_PCA_loading_plot,
    plot_PCA_Biplot,
    plot_PC1_interpolation,
    return_PCA_results,
)
from app.PredefinedData import Software_info
from app.CustomControl import (
    next_btn,
    help_btn,
    check_btn,
    Interpolation_method_selection,
    LoadingWindow,
    bottom_buttons,
)
from app.Pyside6Functions import center_window, show_multiple_plots
from methods.Method_ExperienceValue import Attribute_Window


class PCA_worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, point_dataset, options, outline_dataset):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options
        self.outline_dataset = outline_dataset

    def run(self):
        # 执行PCA分析
        # 返回绘图对象结果
        result_dict = return_PCA_results(
            point_dataset=self.point_dataset,
            options=self.options,
            outline_dataset=self.outline_dataset,
        )
        self.result_ready.emit(result_dict)
        self.finished_signal.emit()


class Attribute_Window_PCA(Attribute_Window):

    def __init__(self, point_dataset, outline_dataset, method):
        super().__init__(
            point_dataset=point_dataset, outline_dataset=outline_dataset, method=method
        )
        self.point_dataset = point_dataset
        self.outline_dataset = outline_dataset

    def on_next_clicked(self):
        contents = self.get_combos_content()
        self.loading_window = LoadingWindow()
        self.loading_window.show()
        self.worker = PCA_worker(
            point_dataset=self.point_dataset,
            options=contents,
            outline_dataset=self.outline_dataset,
        )
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)
    def on_worker_result_ready(self, result_dict):
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
        self.PCA_win = PC1_Interpolation(result_dict=result_dict)
        self.PCA_win.show()
        self.close()


# class PCAplot(QWidget):
#     def __init__(self, point_dataset, options, outline_dataset):
#         super().__init__()
#         self.point_dataset = point_dataset
#         self.outline_dataset = outline_dataset
#         self.pca_columns = process_no_data_list(options)
#         self.setGeometry(100, 100, 600, 300)
#         # Process the data
#         # self.pca_results, self.pca_loadings, self.pca_var_ratio, self.pca_scores = (
#         #     process_PCA(point_dataset, pca_columns=self.pca_columns)
#         # )

#         # 创建主布局
#         self.setWindowTitle(self.tr(Software_info.software_name.value))
#         self.setWindowIcon(QIcon(r"./static/icon.ico"))
#         self.layout = QHBoxLayout()
#         self.total_layout = QVBoxLayout()
#         self.bottom_buttons = bottom_buttons()
#         self.bottom_buttons.next_btn.clicked.connect(self.on_next_clicked)
#         self.bottom_buttons.help_btn.clicked.connect(self.on_help_clicked)
#         self.bottom_buttons.next_btn_clicked.connect(self.on_next_clicked)
#         self.bottom_buttons.help_btn_clicked.connect(self.on_help_clicked)
#         self.total_layout.addLayout(self.layout)
#         self.total_layout.addWidget(self.bottom_buttons)
#         self.setLayout(self.total_layout)
#         center_window(self)

#         # self.plot_names = [
#         #     "PCA variance contribution",
#         #     "PCA loading plot",
#         #     "PCA Biplot",
#         # ]

#         class plot_param(Enum):
#             PCA_variance_contribution = 0
#             PCA_loading_plot = 1
#             PCA_Biplot = 2

#         for i in range(3):
#             canvas = self.create_plot(
#                 plot_param=plot_param(i),
#                 name=self.plot_names[i],
#             )
#             temp_layout = QVBoxLayout()
#             toolbar = NavigationToolbar(canvas, self)
#             temp_layout.addWidget(toolbar)
#             temp_layout.addWidget(canvas)
#             qf = QFrame()
#             qf.setLayout(temp_layout)
#             self.layout.addWidget(qf)

#     def create_plot(self, plot_param, name):
#         if plot_param == plot_param.PCA_variance_contribution:
#             fig = plot_PCA_variance_contribution(self.pca_var_ratio)
#         elif plot_param == plot_param.PCA_loading_plot:
#             fig = plot_PCA_loading_plot(self.pca_loadings, self.pca_var_ratio)
#         elif plot_param == plot_param.PCA_Biplot:
#             fig = plot_PCA_Biplot(
#                 self.pca_results, self.pca_loadings, self.pca_var_ratio
#             )
#         # 创建画布
#         canvas = FigureCanvas(fig)
#         canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 关键
#         canvas.setMinimumSize(300, 300)  # 设置最小尺寸约束
#         return canvas

#     def on_next_clicked(self):
#         self.hide()
#         self.pc1_interpolation = PC1_Interpolation(
#             point_dataset=self.point_dataset,
#             outline_dataset=self.outline_dataset,
#             pca_scores=self.pca_scores,
#         )
#         self.pc1_interpolation.show()

#     def on_help_clicked(self):
#         msg_box = QMessageBox(self)
#         msg_box.setWindowTitle(self.tr("Help"))  # 设置标题
#         msg_box.setText(
#             self.tr(
#                 """
#             PCA variance contribution: The contribution of each principal component to the total variance.\n
#             PCA loading plot: The loading plot of each principal component.\n
#             PCA Biplot: The biplot of PCA.\n
#             """
#             )
#         )
#         msg_box.setStandardButtons(QMessageBox.Ok)
#         msg_box.exec_()


# class PC1_Interpolation(QWidget):
#     def __init__(self, result_dict):
#         super().__init__()
#         self.result_dict = result_dict
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle("PC1 interpolation plot")
#         self.setWindowIcon(QIcon(r"./static/icon.ico"))
#         self.setGeometry(100, 100, 600, 300)
#         self.setMinimumSize(300, 300)
#         self.layout = QVBoxLayout()
#         self.canvas_layout = QVBoxLayout()
#         self.function_layout = QHBoxLayout()
#         self.canvas = self.create_plot()
#         self.toolbar = NavigationToolbar(self.canvas, self)
#         self.canvas_layout.addWidget(self.toolbar)
#         self.canvas_layout.addWidget(self.canvas)
#         #
#         self.interpolation_method = Interpolation_method_selection()
#         self.interpolation_method.Interpolation_method.connect(self.update_plot)
#         self.check_btn = check_btn()
#         self.help_btn = help_btn()
#         self.show_PCA_plots_btn = QPushButton("Show PCA analysis plots")
#         self.show_PCA_plots_btn.clicked.connect(self.display_PCA_plots)
#         self.check_btn.clicked.connect(self.on_check_clicked)
#         self.help_btn.clicked.connect(self.on_help_clicked)

#         self.function_layout.addWidget(self.interpolation_method)
#         self.function_layout.addWidget(self.show_PCA_plots_btn)
#         self.function_layout.addStretch()
#         self.function_layout.addWidget(self.help_btn)
#         self.function_layout.addWidget(self.check_btn)

#         self.layout.addLayout(self.canvas_layout)
#         self.layout.addLayout(self.function_layout)
#         self.setLayout(self.layout)
#         center_window(self)

#     def update_plot(self, interpolation_method):

#         self.canvas_layout.removeWidget(self.canvas)  # 移除旧画布
#         # 删除旧画布和控件
#         self.canvas_layout.removeWidget(self.canvas)
#         self.canvas.deleteLater()
#         self.toolbar.deleteLater()
#         # 重新创建图像并添加到布局
#         self.canvas = self.create_plot(interpolation_method=interpolation_method)
#         self.canvas.setMinimumSize(400, 400)
#         self.toolbar = NavigationToolbar(self.canvas, self)
#         self.canvas_layout.addWidget(self.toolbar)
#         self.canvas_layout.addWidget(self.canvas)

#     def create_plot(self, interpolation_method="Nearest"):
#         fig = self.result_dict.get("PC1_interpolation_figs").get(interpolation_method)
#         canvas = FigureCanvas(fig)
#         canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 关键
#         canvas.setMinimumSize(400, 300)  # 设置最小尺寸约束
#         return canvas

#     def display_PCA_plots(self):
#         figs = [
#             self.result_dict.get("PCA_variance_contribution_fig"),
#             self.result_dict.get("PCA_loading_plot_fig"),
#             self.result_dict.get("PCA_Biplot_fig"),
#         ]
#         show_multiple_plots(figs)

#     def on_check_clicked(self):
#         self.close()

#     def on_help_clicked(self):
#         msg_box = QMessageBox(self)
#         msg_box.setWindowTitle(self.tr("Help"))
#         msg_box.setText(
#             self.tr(
#                 """
#             PC1 interpolation plot: The interpolation plot of PC1 scores.\n
#             """
#             )
#         )
#         msg_box.setStandardButtons(QMessageBox.Ok)
#         msg_box.exec_()


# class PlotWindow(QWidget):
#     def __init__(self, fig):
#         super().__init__()
#         self.setWindowTitle("Geospatial Data Visualization")
#         self.setGeometry(100, 100, 400, 300)
#         self.setWindowIcon(QIcon(r"./static/icon.ico"))
#         self.setMinimumSize(400, 300)

#         # 创建绘图区域
#         self.canvas = None
#         self.toolbar = None
#         self.fig = fig
#         # 安全初始化
#         if not self.fig:
#             QMessageBox.critical(self, "Error", self.tr("Invalid graphic objects"))
#             self.close()

#         # 设置界面
#         self.setup_ui()

#     def setup_ui(self):
#         # 创建 FigureCanvas 对象
#         self.canvas = FigureCanvas(self.fig)
#         self.toolbar = NavigationToolbar(self.canvas, self)

#         # 布局
#         layout = QVBoxLayout()
#         layout.addWidget(self.toolbar)
#         layout.addWidget(self.canvas)
#         self.setLayout(layout)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QSizePolicy,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# class PC1_Interpolation(QWidget):
#     def __init__(self, result_dict):
#         super().__init__()
#         self.result_dict = result_dict
#         self.current_canvas = None  # 保存当前画布引用
#         self.initUI()

#     def initUI(self):
#         # 主布局
#         main_layout = QVBoxLayout()
#         main_layout.setSpacing(5)
#         main_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距

#         # 顶部绘图区域
#         self.canvas_layout = QVBoxLayout()
#         self.canvas_layout.setSpacing(0)
#         self.create_initial_plot()  # 初始化默认画布

#         # 底部功能区
#         function_layout = QHBoxLayout()
#         function_layout.setSpacing(10)

#         # 控件初始化
#         self.interpolation_method = Interpolation_method_selection()
#         self.show_PCA_btn = QPushButton("Show PCA Analysis")
#         self.help_btn = help_btn()
#         self.close_btn = check_btn()

#         # 按钮布局（左对齐功能控件，右对齐操作按钮）
#         function_layout.addWidget(self.interpolation_method)
#         function_layout.addWidget(self.show_PCA_btn)
#         function_layout.addStretch()  # 中间弹性空间
#         function_layout.addWidget(self.help_btn)
#         function_layout.addWidget(self.close_btn)

#         # 信号连接
#         self.interpolation_method.Interpolation_method.connect(self.update_plot)
#         self.show_PCA_btn.clicked.connect(self.display_PCA_plots)
#         self.help_btn.clicked.connect(self.show_help)
#         self.close_btn.clicked.connect(self.close)

#         # 组合布局
#         main_layout.addLayout(self.canvas_layout)
#         main_layout.addLayout(function_layout)
#         self.setLayout(main_layout)

#         # 窗口属性
#         self.setWindowTitle("PC1 Interpolation Plot")
#         self.setWindowIcon(QIcon(r"./static/icon.ico"))
#         self.setMinimumSize(600, 400)
#         center_window(self)

#     def create_initial_plot(self):
#         """初始化默认画布（最近邻插值）"""
#         if self.current_canvas:
#             self.canvas_layout.removeWidget(self.current_canvas)
#             self.current_canvas.deleteLater()

#         fig = self.result_dict["PC1_interpolation_figs"]["Nearest"]
#         self.current_canvas = FigureCanvas(fig)
#         self.current_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.toolbar = NavigationToolbar(self.current_canvas, self)

#         self.canvas_layout.addWidget(self.toolbar)
#         self.canvas_layout.addWidget(self.current_canvas)

#     def update_plot(self, method):
#         try:
#             fig = self.result_dict["PC1_interpolation_figs"][method]

#             # 直接更新画布内容（无需重建控件）
#             self.current_canvas.figure = fig
#             self.current_canvas.draw()
#             self.toolbar.update()  # 同步工具栏状态
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to update plot: {str(e)}")

#     def display_PCA_plots(self):
#         figs = [
#             self.result_dict["PCA_variance_contribution_fig"],
#             self.result_dict["PCA_loading_plot_fig"],
#             self.result_dict["PCA_Biplot_fig"],
#         ]
#         # 假设 show_multiple_plots 接受 Figure 对象列表
#         show_multiple_plots(figs)

#     def show_help(self):
#         """优化后的帮助提示（支持国际化）"""
#         QMessageBox.information(
#             self,
#             self.tr("Help"),
#             self.tr("PC1 interpolation plot: The interpolation plot of PC1 scores."),
#             QMessageBox.Ok,
#         )

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class PC1_Interpolation(QWidget):
    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.current_canvas = None  # 右侧动态画布
        self.fixed_canvas = None  # 新增左侧固定画布
        self.initUI()

    def initUI(self):
        # 主布局（垂直布局）
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 顶部双画布容器
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # 左侧固定画布（从result_dict获取）
        if "PC1_score_fig" in self.result_dict:  # 假设固定fig的键为reference_fig
            self.fixed_canvas = FigureCanvas(self.result_dict["PC1_score_fig"])
            self.fixed_canvas.setFixedSize(300, 300)  # 固定尺寸
            self.fixed_canvas.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            top_layout.addWidget(self.fixed_canvas)

        # 右侧动态画布区域（原有逻辑）
        self.dynamic_container = QWidget()
        self.dynamic_layout = QVBoxLayout()
        self.dynamic_container.setLayout(self.dynamic_layout)
        self.create_initial_plot()  # 原有初始化
        top_layout.addWidget(self.dynamic_container)

        # 底部功能区
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(5)

        # 第一行：插值方法选择器（左对齐）
        method_layout = QHBoxLayout()
        self.interpolation_method = Interpolation_method_selection()
        method_layout.addWidget(self.interpolation_method)
        method_layout.addStretch()  # 推动控件左对齐
        bottom_layout.addLayout(method_layout)

        # 第二行：功能按钮（保持原有布局）
        button_layout = QHBoxLayout()
        self.show_PCA_btn = QPushButton("Show PCA Analysis")
        self.export_btn = QPushButton("Export GDF")  # 新增导出按钮
        self.help_btn = help_btn()
        self.close_btn = check_btn()

        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.show_PCA_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.help_btn)
        button_layout.addWidget(self.close_btn)
        bottom_layout.addLayout(button_layout)

        # 组合总布局
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # 信号连接（新增导出功能）
        self.export_btn.clicked.connect(self.export_gdf)
        self.interpolation_method.Interpolation_method.connect(self.update_plot)
        self.show_PCA_btn.clicked.connect(self.display_PCA_plots)
        self.help_btn.clicked.connect(self.show_help)
        self.close_btn.clicked.connect(self.close)

        # 窗口属性
        self.setWindowTitle("PC1 Interpolation Plot")
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setMinimumSize(900, 600)  # 扩展窗口大小
        center_window(self)

    # 原有方法保持不变
    def create_initial_plot(self):
        if self.current_canvas:
            self.dynamic_layout.removeWidget(self.current_canvas)
            self.current_canvas.deleteLater()

        fig = self.result_dict["PC1_interpolation_figs"]["Nearest"]
        self.current_canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.current_canvas, self)

        self.dynamic_layout.addWidget(self.toolbar)
        self.dynamic_layout.addWidget(self.current_canvas)

    def update_plot(self, method):
        try:
            fig = self.result_dict["PC1_interpolation_figs"][method]
            self.current_canvas.figure = fig
            self.current_canvas.draw()
            self.toolbar.update()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def display_PCA_plots(self):
        figs = [
            self.result_dict["PCA_variance_contribution_fig"],
            self.result_dict["PCA_loading_plot_fig"],
            self.result_dict["PCA_Biplot_fig"],
        ]
        # 假设 show_multiple_plots 接受 Figure 对象列表
        show_multiple_plots(figs)

    # 新增导出功能
    def export_gdf(self):
        try:
            gdf = self.result_dict.get("gdf")
            if gdf is None:
                raise ValueError("No valid data to export")

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export GeoDataFrame",
                "",
                "Shapefile (*.shp);;GeoJSON (*.geojson)",
            )

            if filename:
                gdf.to_file(filename)
                QMessageBox.information(self, "Success", "Data exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def show_help(self):
        """优化后的帮助提示（支持国际化）"""
        QMessageBox.information(
            self,
            self.tr("Help"),
            self.tr("PC1 interpolation plot: The interpolation plot of PC1 scores."),
            QMessageBox.Ok,
        )
