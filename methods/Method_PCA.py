from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QThread, Slot
from PySide6.QtWidgets import (
    QMessageBox,
    QWidget,
    QFileDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

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
from app.Method_Functions import return_PCA_results
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
                "gpkg (*.gpkg);;shp (*.shp)",
            )

            if filename:
                gdf.to_file(filename, driver="gpkg")
                QMessageBox.information(self, "Success", "Data exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def show_help(self):
        QMessageBox.information(
            self,
            self.tr("Help"),
            self.tr("PC1 interpolation plot: The interpolation plot of PC1 scores."),
            QMessageBox.Ok,
        )
