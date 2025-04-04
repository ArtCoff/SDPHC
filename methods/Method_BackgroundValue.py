from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QThread, Slot
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMessageBox,
    QTableView,
    QLabel,
    QWidget,
    QPushButton,
    QPlainTextEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
)
from methods.Method_ExperienceValue import Attribute_Window
from app.Method_Functions import (
    read_file_columns,
    point_dataset_preprocess,
    process_background_value_method,
    calculate_backgroundValue,
)
from app.PredefinedData import Software_info, MIM_indicators
from app.CustomControl import (
    background_value_input_doublespinbox,
    bottom_buttons,
    LoadingWindow,
)
from app.Pyside6Functions import (
    AppStyle,
    center_window,
    traverse_layout,
    show_multiple_plots,
)
from app.Auto_report_EN import auto_report_EN as auto_report


class backgroundValue_worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, point_dataset, options):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options

    def run(self):
        # 返回ECDF绘图对象
        # 返回Kmeans绘图对象和边界值
        # 返回预处理的gdf
        # 返回异常点位绘图对象
        gdf = point_dataset_preprocess(self.point_dataset, self.options)
        result_dict = process_background_value_method(gdf)
        result_dict["gdf"] = gdf
        self.result_ready.emit(result_dict)
        self.finished_signal.emit()


class anomaly_identification_worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, result_dict, final_boundarys):
        super().__init__()
        self.data = result_dict
        self.final_boundarys = final_boundarys

    def run(self):
        result_dict = calculate_backgroundValue(self.data, self.final_boundarys)
        self.result_ready.emit(result_dict)
        self.finished_signal.emit()


class Attribute_Window_BackgroundValue(Attribute_Window):

    def __init__(self, point_dataset, outline_dataset, method):
        super().__init__(
            point_dataset=point_dataset,
            outline_dataset=outline_dataset,
            method=method,
        )
        self.point_dataset = point_dataset
        self.outline_dataset = outline_dataset
        self.updateUI()

    def updateUI(self):
        self.other_contaminants = []
        self.other_contaminants_text = QPlainTextEdit()
        self.other_contaminants_text.setReadOnly(True)
        self.form_layout.addRow("Other contaminants:", self.other_contaminants_text)
        options = read_file_columns(self.point_dataset)
        self.Detect_other_contaminants(options)

    def Detect_other_contaminants(self, options):
        import json

        all_indicators = set()
        with open("./resources/Monitoring_pollution.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for key, value in data.items():
            all_indicators.update(value.get("指标", []))

        # 转换为列表并排序
        unique_indicators = sorted(all_indicators)
        for i, data in enumerate(unique_indicators):
            if data in options:
                self.other_contaminants.append(data)
                self.other_contaminants_text.appendPlainText(f"{data};")

    def on_next_clicked(self):
        contents = self.get_combos_content()
        self.loading_window = LoadingWindow()
        self.loading_window.show()
        self.worker = backgroundValue_worker(self.point_dataset, contents)
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)
    def on_worker_result_ready(self, result_dict):
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
        result_dict["outline_dataset"] = self.outline_dataset
        result_dict["other_contaminants"] = self.other_contaminants
        self.background_value_win = background_value_input_manual(
            result_dict=result_dict
        )
        self.background_value_win.show()
        self.close()


class indicator_background_value_input(QWidget):
    def __init__(self, indicator, result_dict, value_range=100):
        super().__init__()
        self.indicator = indicator
        self.result = result_dict.get(indicator)
        self.status = True
        if self.result.kmeans_boundary is None:
            self.status = False
        self.label = QLabel(f"{indicator.value.label}:")
        self.unit_label = QLabel(indicator.value.unit)
        self.background_value_input = background_value_input_doublespinbox(
            range=value_range
        )
        self.ecdf_btn = QPushButton("ECDF")
        self.kmeans_btn = QPushButton("Clustering")
        self.ecdf_btn.clicked.connect(self.plot_ECDF)
        self.kmeans_btn.clicked.connect(self.plot_kemans_boundary)
        self.set_status()
        self.set_value()
        self.set_UI()

    def set_UI(self):
        layout = QHBoxLayout()
        layout.addWidget(self.label, stretch=1)
        self.label.setMinimumSize(60, 30)
        layout.addWidget(self.background_value_input, stretch=2)
        self.background_value_input.setMinimumSize(80, 30)
        layout.addWidget(self.unit_label, stretch=1)
        self.unit_label.setMinimumSize(40, 30)
        layout.addWidget(self.ecdf_btn, stretch=1)
        layout.addWidget(self.kmeans_btn, stretch=1)
        layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(layout)
        for btn in [self.ecdf_btn, self.kmeans_btn]:
            btn.setFixedWidth(80)
            btn.setFixedHeight(30)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #e8e8e8;
                    border:1px solid #c5c5c5;
                    padding: 6px; 
                }
                QPushButton:hover {
                    background-color: soild darkgray;
                }
            """
            )

    def plot_kemans_boundary(self):
        # fig = deepcopy(self.result.kmeans_fig)
        fig = self.result.kmeans_fig
        if fig is None:
            return QMessageBox.warning(self, "Warning", "No data available")
        show_multiple_plots(fig)

    def plot_ECDF(self):
        # fig = deepcopy(self.result.ecdf_fig)
        fig = self.result.ecdf_fig
        if fig is None:
            return QMessageBox.warning(self, "Warning", "No data available")
        show_multiple_plots(fig)

    def set_value(self):
        if self.status:
            self.background_value_input.setValue(self.result.kmeans_boundary)

    def set_status(self):
        self.background_value_input.setEnabled(self.status)
        self.ecdf_btn.setEnabled(self.status)
        self.kmeans_btn.setEnabled(self.status)

    @property
    def get_final_boundary(self):
        if self.status:
            return (self.indicator, self.background_value_input.value())
        else:
            return (self.indicator, None)


class background_value_input_manual(QWidget):

    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.initUI()

    def initUI(self):
        self.setWindowIcon(AppStyle.icon())
        self.setWindowTitle(self.tr("Background value manual input"))
        self.resize(500, 300)
        self.setMinimumSize(500, 300)

        self.radon_background_value = indicator_background_value_input(
            MIM_indicators.Radon, self.result_dict, value_range=999999
        )
        self.VOCs_background_value = indicator_background_value_input(
            MIM_indicators.VOCs, self.result_dict, value_range=999999
        )
        self.CO2_background_value = indicator_background_value_input(
            MIM_indicators.CO2, self.result_dict, value_range=999999
        )
        self.O2_background_value = indicator_background_value_input(
            MIM_indicators.O2, self.result_dict, value_range=100
        )
        self.CH4_background_value = indicator_background_value_input(
            MIM_indicators.CH4, self.result_dict, value_range=100
        )
        self.gene_background_value = indicator_background_value_input(
            MIM_indicators.FG, self.result_dict, value_range=999999
        )
        self.value_layout = QVBoxLayout()
        self.value_layout.setSpacing(5)
        self.value_layout.setContentsMargins(5, 5, 5, 5)
        self.value_layout.addWidget(self.radon_background_value)
        self.value_layout.addWidget(self.VOCs_background_value)
        self.value_layout.addWidget(self.CO2_background_value)
        self.value_layout.addWidget(self.O2_background_value)
        self.value_layout.addWidget(self.CH4_background_value)
        self.value_layout.addWidget(self.gene_background_value)

        #
        self.bottom_buttons = bottom_buttons()
        self.bottom_buttons.next_btn_clicked.connect(self.on_next_clicked)
        self.bottom_buttons.help_btn_clicked.connect(self.on_help_clicked)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 10, 5)
        main_layout.setSpacing(0)
        main_layout.addLayout(self.value_layout)
        main_layout.addWidget(self.bottom_buttons)
        self.setLayout(main_layout)
        center_window(self)

    def get_boundaries(self, widget):
        if isinstance(widget, indicator_background_value_input):
            return widget.get_final_boundary
        else:
            print("Not a indicator_background_value_input")

    @property
    def get_final_boundarys(self):
        return dict(traverse_layout(self.value_layout, self.get_boundaries))

    def on_next_clicked(self):
        final_boundarys = self.get_final_boundarys
        self.loading_window = LoadingWindow()
        self.loading_window.show()
        self.worker = anomaly_identification_worker(self.result_dict, final_boundarys)
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)
    def on_worker_result_ready(self, result_dict):
        self.hide()
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
        self.function_win = function_win(result_dict=result_dict)
        self.function_win.show()
        self.close()

    def on_help_clicked(self):
        QMessageBox.information(
            self,
            "Help",
            "This page is used to manually input the background values of various indicators. "
            "If you are not sure about the background values of the indicators, "
            "you can use the 'Indicator Data Analysis' button to analyze the data and automatically determine the background values. "
            "The 'ECDF' button can be used to draw the ECDF diagram of the indicator data. "
            "After inputting the background values, click the 'Next' button to go to the next step.",
        )


class function_win(QWidget):

    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.gdf = result_dict.get("gdf")
        self.other_contaminants = result_dict.get("other_contaminants")
        self.final_boundarys = result_dict.get("final_boundarys")
        self.initUI()

    def initUI(self):
        # header = [
        #     "点位",
        #     "氡气异常低",
        #     "VOCs异常高",
        #     "CO2异常高",
        #     "O2异常低",
        #     "CH4异常高",
        #     "功能基因异常高",
        # ]
        header = [
            "Point ID",
            "Abnormally Low Radon",
            "Abnormally High VOCs",
            "Abnormally High CO2",
            "Abnormally Low O2",
            "Abnormally High CH4",
            "Abnormally High Functional Genes",
        ]
        # 创建表格视图
        self.table_view = QTableView()
        self.table_model = GeoDataFrameModel(self.gdf, header)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

        # 调整窗口大小以适应表格内容
        self.adjustSize()
        # 创建导出按钮
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)

        # 创建绘图按钮
        self.plot_button = QPushButton("Plot results")
        self.plot_button.clicked.connect(self.plot_data)

        # 创建导出Shapefile按钮
        self.export_shp_button = QPushButton("Export to GeoPackage")
        self.export_shp_button.clicked.connect(self.export_to_gpkg)

        # 创见自动报告按钮
        self.auto_report_button = QPushButton("Auto report")
        self.auto_report_button.clicked.connect(self.auto_report)
        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.table_view)
        layout.addWidget(self.export_button)
        layout.addWidget(self.export_shp_button)  # 添加导出Shapefile按钮
        layout.addWidget(self.plot_button)
        layout.addWidget(self.auto_report_button)
        self.setLayout(layout)
        self.resize(800, 600)
        self.setWindowIcon(AppStyle.icon())
        self.setWindowTitle("Results")
        center_window(self)

    def export_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save", "", "Form document (*.xlsx)"
        )
        if file_path:
            try:
                self.gdf.to_excel(file_path, index=False)
                QMessageBox.information(
                    self,
                    "Success!",
                    "The form file has been saved locally and can be opened with Excel.",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error!",
                    f"The form file failed to be saved, the reason for the failure was {str(e)}",
                )

    def export_to_gpkg(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save",
            "",
            "GeoPackage Files (*.gpkg)",
        )
        if file_path:
            try:
                self.gdf.to_file(file_path, driver="GPKG")
                QMessageBox.information(
                    self,
                    "Success!",
                    "The vector files have been saved locally and can be opened using QGIS or ArcGIS.",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error!",
                    f"The vector file failed to be saved, the reason for the failure is: {str(e)}",
                )

    def plot_data(self):
        from app.Pyside6Functions import show_multiple_plots

        figs = []
        for indicator, fig in self.result_dict.get("anomaly_figs"):
            if fig is not None:
                figs.append(fig)
        show_multiple_plots(figs)

    def auto_report(self):
        doc = auto_report(
            self.gdf, background_file=None, final_boundarys=self.final_boundarys
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export report",
            "",
            "Reporting documents (*.docx)",
        )
        if file_path:
            try:
                doc.save(file_path)
                QMessageBox.information(
                    self,
                    "succeed",
                    "The report has been saved locally and can be opened using WPS or Word!",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "failed", f"The report failed to be saved due to:{str(e)}"
                )


class GeoDataFrameModel(QAbstractTableModel):
    def __init__(self, gdf, columns_to_display):
        super().__init__()

        self._gdf = gdf
        self._columns_to_display = columns_to_display

    def rowCount(self, parent=None):
        return len(self._gdf)

    def columnCount(self, parent=None):
        return len(self._columns_to_display)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            column_name = self._columns_to_display[index.column()]
            return str(self._gdf.iloc[index.row()][column_name])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._columns_to_display[section]
            if orientation == Qt.Vertical:
                return str(self._gdf.index[section])
        return None
