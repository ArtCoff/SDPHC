from PySide6.QtCore import Signal, QThread, Slot, Qt
from PySide6.QtWidgets import (
    QMessageBox,
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from utils.predefined_data import Software_info
from gui.empirical_threshold_analysis import Attribute_Window
from gui.custom_controls import (
    Interpolation_method_selection,
    LoadingWindow,
    WrapButton,
)
from utils import center_window, show_multiple_plots, AppStyle
from core import return_PCA_results


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
        self.PCA_win = PCA_function_win(result_dict=result_dict)
        self.PCA_win.show()
        self.close()


class PCA_function_win(QWidget):

    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.initUI()

    def initUI(self):
        self.setWindowTitle(Software_info.software_name.value)
        self.resize(600, 300)
        self.setMinimumSize(400, 200)
        self.setWindowIcon(AppStyle.icon())

        self.analysis_btn = WrapButton(self.tr("View graph of PCA analysis results"))
        self.point_btn = WrapButton(self.tr("View PC1 point distribution"))
        self.interpolation_btn = WrapButton(self.tr("View PC1 interpolation results"))
        self.export_btn = WrapButton(
            self.tr("Export vector results (including principal component scores)")
        )

        # 功能连接
        self.analysis_btn.clicked.connect(self.display_PCA_plots)
        self.point_btn.clicked.connect(self.display_PC1_point_distribution)
        self.interpolation_btn.clicked.connect(self.display_PC1_interpolation)
        self.export_btn.clicked.connect(self.export_gdf)
        # Layout
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.analysis_btn)
        btn_layout.addWidget(self.point_btn)
        btn_layout.addWidget(self.interpolation_btn)
        btn_layout.addWidget(self.export_btn)
        self.setLayout(btn_layout)
        center_window(self)

    def display_PCA_plots(self):
        figs = [
            self.result_dict["PCA_variance_contribution_fig"],
            self.result_dict["PCA_loading_plot_fig"],
            self.result_dict["PCA_Biplot_fig"],
        ]
        show_multiple_plots(figs)

    def display_PC1_point_distribution(self):
        show_multiple_plots([self.result_dict["PC1_score_fig"]])

    def display_PC1_interpolation(self):
        self.PC1_interpolation_win = PC1_Interpolation(self.result_dict)
        self.PC1_interpolation_win.show()

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


class PC1_Interpolation(QWidget):
    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.current_canvas = None
        self.initUI()

    def initUI(self):
        # 主布局（垂直布局）
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.dynamic_layout = QVBoxLayout()
        self.create_initial_plot()  # 原有初始化
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)

        self.interpolation_method = Interpolation_method_selection()
        bottom_layout.addWidget(self.interpolation_method)
        self.main_layout.addLayout(self.dynamic_layout)
        self.main_layout.addLayout(bottom_layout)
        self.setLayout(self.main_layout)

        self.interpolation_method.Interpolation_method.connect(self.update_plot)

        # 窗口属性
        self.setWindowTitle("PC1 Interpolation Plot")
        self.setWindowIcon(AppStyle.icon())
        self.resize(800, 600)  # 设置窗口大小
        center_window(self)

    def update_canvas(self, method):
        """根据方法名更新画布和工具栏"""
        try:
            from copy import deepcopy

            fig = self.result_dict["PC1_interpolation_figs"][method]
            fig = deepcopy(fig)
            # 清理旧组件
            if self.current_canvas:
                self.dynamic_layout.removeWidget(self.current_canvas)
                self.current_canvas.deleteLater()
            if hasattr(self, "toolbar"):
                self.dynamic_layout.removeWidget(self.toolbar)
                self.toolbar.deleteLater()

            # 创建新组件
            self.current_canvas = FigureCanvas(fig)
            self.toolbar = NavigationToolbar(self.current_canvas, self)

            # 添加到布局
            self.dynamic_layout.addWidget(self.toolbar)
            self.dynamic_layout.addWidget(self.current_canvas)

        except KeyError:
            raise ValueError(f"Method '{method}' not found in results")
        except Exception as e:
            raise RuntimeError(f"Failed to update plot: {str(e)}")

    def create_initial_plot(self):
        self.update_canvas("Nearest")

    def update_plot(self, method):
        try:
            self.update_canvas(method)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
