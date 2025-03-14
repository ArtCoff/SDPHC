import sys
from enum import Enum
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, Slot, QThreadPool, QThread
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QTableView,
    QWidget,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
)
from Method_Functions import (
    plot_basic_info,
    read_file_columns,
    point_dataset_preprocess,
    calculate_ExperienceValueMethod_scores,
    绘制污染源区图,
    绘制污染范围,
    绘制超标点位,
    污染等级识别,
)
from PredefinedData import (
    software_name,
    Methods,
    Secondary_Functions_of_ExperienceValue,
)
from CustomControl import (
    next_btn,
    help_btn,
    CustomComboBox,
    # WrapButton,
    WrapButton_EN,
    GeoDataFrameModel,
    PlotWindow,
    bottom_buttons,
    LoadingWindow,
)
from Pyside6Functions import center_window


class worker(QThread):
    finished_signal = Signal()
    # progress_signal = Signal(int)
    result_ready = Signal(object)

    def __init__(self, point_dataset, options):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options

    def run(self):
        gdf = point_dataset_preprocess(self.point_dataset, self.options)
        result_gdf = calculate_ExperienceValueMethod_scores(gdf)
        self.result_ready.emit(result_gdf)
        self.finished_signal.emit()


class Attribute_Window(QWidget):

    def __init__(self, point_dataset, outline_dataset, method: Enum):
        super().__init__()
        self.method = method
        self.thread_pool = QThreadPool.globalInstance()
        self.point_dataset = point_dataset
        self.outline_dataset = outline_dataset
        self.combos = []
        self.initUI(options=read_file_columns(point_dataset))

    def initUI(self, options):
        self.setWindowTitle(software_name)
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumSize(400, 300)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.plot_dataset_info_btn = QPushButton(
            self.tr("Displays an overview of the data")
        )
        self.plot_dataset_info_btn.clicked.connect(self.plot_dataset_info)
        self.help_btn = help_btn()
        self.next_btn = next_btn()
        self.form_layout = QFormLayout()
        self.bottom_buttons = bottom_buttons()
        self.bottom_buttons.next_btn_clicked.connect(self.on_next_clicked)
        self.bottom_buttons.help_btn_clicked.connect(self.on_help_clicked)

        total_layout = QVBoxLayout()
        total_layout.addWidget(self.plot_dataset_info_btn)
        total_layout.addLayout(self.form_layout)
        total_layout.addWidget(self.bottom_buttons)

        indicator_labels = [
            self.tr("Point number"),
            self.tr("Radon"),
            "VOCs",
            "CO<sub>2</sub>",
            "O<sub>2</sub>",
            "CH<sub>4</sub>",
            "H<sub>2</sub>",
            "H<sub>2</sub>S",
            self.tr("Functional genes"),
        ]
        for i in range(9):
            combo = CustomComboBox(options, i)
            self.form_layout.addRow(f"{indicator_labels[i]}:", combo)
            self.combos.append(combo)
        self.set_initial_selections(options)
        self.method_control_combos(self.method)
        self.setLayout(total_layout)
        center_window(self)

    def set_initial_selections(self, options):
        Monitoring_indicators = [
            "Point_code",
            "Radon",
            "VOCs",
            "CO2",
            "O2",
            "CH4",
            "H2",
            "H2S",
            "Functional genes",
        ]
        for i, data in enumerate(Monitoring_indicators):
            if data in options:
                index = options.index(data)
                self.combos[i].setCurrentIndex(index)
            else:
                self.combos[i].setCurrentIndex(-1)
                last_index = self.combos[i].count() - 1
                if last_index >= 0:  # 确保至少有一个选项
                    self.combos[i].setCurrentIndex(last_index)

    def on_help_clicked(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(self.tr("Help"))
        msg_box.setText(
            self.tr(
                "Select the field corresponding to the monitoring indicator in the drop-down box.\n\n"
            )
        )
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def on_next_clicked(self):

        contents = self.get_combos_content()

        self.loading_window = LoadingWindow()
        self.loading_window.show()
        self.worker = worker(self.point_dataset, contents)
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)
    def on_worker_result_ready(self, result_gdf):
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
        self.Contamination_identification_win = Contamination_identification_win(
            result_gdf=result_gdf,
            outline_dataset=self.outline_dataset,
        )
        self.Contamination_identification_win.show()
        self.close()

    def plot_dataset_info(self):
        fig = plot_basic_info(
            point_dataset=self.point_dataset, outline_dataset=self.outline_dataset
        )
        self.plot_window = PlotWindow(fig)
        self.plot_window.show()

    def get_combos_content(self):
        return [combo.currentText() for combo in self.combos]

    def Validate_input_Data(self):
        [combo.currentText() for combo in self.combos]

    def method_control_combos(self, method):
        if method == Methods.Experience_value_method:
            self.combos[-1].setEnabled(False)


class Contamination_identification_win(QWidget):

    def __init__(self, result_gdf, outline_dataset):
        super().__init__()
        self.result_gdf = result_gdf
        self.outline_dataset = outline_dataset
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.tr(software_name))
        self.setGeometry(100, 100, 400, 200)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        center_window(self)
        self.exit_btn = QPushButton(self.tr("Quit"))
        self.function1_btn = WrapButton_EN(
            self.tr("Pollution exceedance points (except radon gas)")
        )
        self.function2_btn = WrapButton_EN(
            self.tr("Pollution source area and suspected pollution source area")
        )
        self.function4_btn = WrapButton_EN(self.tr("Scope of contamination"))
        self.function5_btn = WrapButton_EN(self.tr("Pollution level identification"))

        # 功能连接
        self.exit_btn.clicked.connect(self.close)
        self.function1_btn.clicked.connect(self.function_PCP)
        self.function2_btn.clicked.connect(self.function_PSA)
        self.function4_btn.clicked.connect(self.function_SOC)
        self.function5_btn.clicked.connect(self.function_PLI)
        # Layout
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.function1_btn)
        btn_layout.addWidget(self.function2_btn)
        btn_layout.addWidget(self.function4_btn)
        btn_layout.addWidget(self.function5_btn)

        ###
        h4_layout = QHBoxLayout()
        v_layout = QVBoxLayout()
        h4_layout.addWidget(self.exit_btn)
        v_layout.addLayout(btn_layout)
        v_layout.addLayout(h4_layout)
        self.setLayout(v_layout)

    def function_PCP(self):
        display_gdf = self.result_gdf[self.result_gdf["The_other_soil_gas_scores"] >= 6]
        self.result_win1 = function_win(
            display_gdf,
            columns_to_display=[
                "Point_Code",
                "VOCs_Score",
                "CO2_Score",
                "H2_Score",
                "O2_Score",
                "CH4_Score",
                "H2S_Score",
                "The_other_soil_gas_scores",
            ],
            all_gdf=self.result_gdf,
            outline_polygon_file=self.outline_dataset,
            funtion_name=Secondary_Functions_of_ExperienceValue.function_PCP,
        )
        self.result_win1.show()

    def function_PSA(self):
        dis_play_gdf = self.result_gdf[
            self.result_gdf["The_other_soil_gas_scores"] >= 6
        ]
        self.result_win2 = function_win(
            dis_play_gdf,
            columns_to_display=[
                "Point_Code",
                "The_other_soil_gas_scores",
                "Radon_Score",
                "All_indicators_Scores",
            ],
            # ["点位编号", "其他土壤气得分", "氡气赋分", "所有指标得分"],
            all_gdf=self.result_gdf,
            outline_polygon_file=self.outline_dataset,
            funtion_name=Secondary_Functions_of_ExperienceValue.function_PSA,
        )
        self.result_win2.show()

    def function_SOC(self):
        # gdf = 计算污染范围(self.point_dataset, self.options)
        self.result_win4 = function_win(
            display_gdf=self.result_gdf,
            columns_to_display=[
                "Point_Code",
                "The_other_soil_gas_scores",
                "Scope_of_contamination",
            ],
            # columns_to_display=["点位编号", "其他土壤气得分", "得分≥1"],
            all_gdf=self.result_gdf,
            outline_polygon_file=self.outline_dataset,
            funtion_name=Secondary_Functions_of_ExperienceValue.function_SOC,
        )
        self.result_win4.show()

    def function_PLI(self):
        pass
        # gdf = point_dataset_preprocess(
        #     self.point_dataset,
        #     self.options,
        # )

        # gdf = 计算总体得分(gdf)
        # 污染等级识别(
        #     gdf,
        #     self.outline_dataset,
        # )


class function_win(QWidget):

    def __init__(
        self,
        display_gdf,
        columns_to_display,
        all_gdf,
        outline_polygon_file,
        funtion_name,
    ):
        super().__init__()
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.gdf = display_gdf[columns_to_display]  #
        self.all_gdf = all_gdf
        self.outline_polygon_file = outline_polygon_file
        self.function_name = funtion_name
        # 创建表格视图
        self.table_view = QTableView()
        self.table_model = GeoDataFrameModel(self.gdf, columns_to_display)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

        # 调整窗口大小以适应表格内容
        self.adjustSize()
        self.resize(800, 600)
        # 创建导出按钮
        self.export_button = QPushButton(self.tr("Export to Excel"))
        self.export_button.clicked.connect(self.export_to_excel)

        # 创建绘图按钮
        self.plot_button = QPushButton(self.tr("Display plot"))
        self.plot_button.clicked.connect(self.plot_data)

        # 创建导出Shapefile按钮
        self.export_shp_button = QPushButton(self.tr("Export to GeoPackage"))
        self.export_shp_button.clicked.connect(self.export_to_gpkg)

        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.table_view)
        layout.addWidget(self.export_button)
        layout.addWidget(self.export_shp_button)
        layout.addWidget(self.plot_button)
        self.setLayout(layout)

        self.setWindowTitle("GeoDataFrame Viewer")
        center_window(self)

    def export_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            try:
                self.gdf.to_excel(file_path, index=False)
                QMessageBox.information(
                    self, "Success", "File has been exported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export file: {str(e)}")

    def export_to_gpkg(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "GeoPackage Files (*.gpkg)",
        )
        if file_path:
            try:
                self.all_gdf.to_file(file_path, driver="GPKG")
                QMessageBox.information(
                    self, "Success", "GeoPackage has been exported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to export GeoPackage: {str(e)}"
                )

    def plot_data(self):
        if self.function_name == Secondary_Functions_of_ExperienceValue.function_PSA:
            try:
                绘制污染源区图(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == Secondary_Functions_of_ExperienceValue.function_SOC:
            try:
                绘制污染范围(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == Secondary_Functions_of_ExperienceValue.function_PCP:
            try:
                绘制超标点位(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")

    def Contamination_identification(self):
        if self.function_name == Secondary_Functions_of_ExperienceValue.function_PSA:
            try:
                绘制污染源区图(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == Secondary_Functions_of_ExperienceValue.function_SOC:
            try:
                绘制污染范围(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == Secondary_Functions_of_ExperienceValue.function_PCP:
            try:
                绘制超标点位(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
