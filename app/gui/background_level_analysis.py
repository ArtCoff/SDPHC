import logging
from PySide6.QtWidgets import (
    QMessageBox,
    QTableView,
    QLabel,
    QWidget,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QThread, Slot
from core import (
    read_file_columns,
    point_dataset_preprocess,
    process_background_value_method,
    calculate_backgroundLevel,
    export_to_vector_file,
    export_to_word,
    export_to_table,
)
from utils import (
    AppStyle,
    NIS_indicators,
    center_window,
    traverse_layout,
    show_multiple_plots,
    report_test as auto_report,
)

from .custom_controls import (
    background_level_input_doublespinbox,
    bottom_buttons,
    LoadingWindow,
)
from .empirical_threshold_analysis import Attribute_Window


class backgroundLevel_worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, point_dataset, options):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options

    def run(self):
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
        result_dict = calculate_backgroundLevel(self.data, self.final_boundarys)
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
        self.form_layout.addRow(
            self.tr("Other contaminants:"), self.other_contaminants_text
        )
        options = read_file_columns(self.point_dataset)
        self.Detect_other_contaminants(options)

    def Detect_other_contaminants(self, options):
        import json

        all_indicators = set()
        from pathlib import Path

        current_dir = Path(__file__).parent
        json_path = (
            current_dir.parent / "assets" / "database" / "monitoring_pollution.json"
        )
        with open(json_path, "r", encoding="utf-8") as f:
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
        self.worker = backgroundLevel_worker(self.point_dataset, contents)
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)  # type: ignore
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
        self.background_value_input = background_level_input_doublespinbox(
            range=value_range
        )
        self.ecdf_btn = QPushButton("ECDF")
        self.kmeans_btn = QPushButton(self.tr("Clustering"))
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
        fig = self.result.kmeans_fig
        if fig is None:
            return QMessageBox.warning(self, "Warning", self.tr("No data available"))
        show_multiple_plots(fig)

    def plot_ECDF(self):
        fig = self.result.ecdf_fig
        if fig is None:
            return QMessageBox.warning(self, "Warning", self.tr("No data available"))
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
            NIS_indicators.Radon, self.result_dict, value_range=999999
        )
        self.VOCs_background_value = indicator_background_value_input(
            NIS_indicators.VOCs, self.result_dict, value_range=999999
        )
        self.CO2_background_value = indicator_background_value_input(
            NIS_indicators.CO2, self.result_dict, value_range=999999
        )
        self.O2_background_value = indicator_background_value_input(
            NIS_indicators.O2, self.result_dict, value_range=100
        )
        self.CH4_background_value = indicator_background_value_input(
            NIS_indicators.CH4, self.result_dict, value_range=100
        )
        self.gene_background_value = indicator_background_value_input(
            NIS_indicators.FG, self.result_dict, value_range=999999
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
            logging.warning("Not a indicator_background_value_input")

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

    @Slot(object)  # type: ignore
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
            self.tr(
                "This page is used to manually input the background values of various indicators. "
                "If you are not sure about the background values of the indicators, "
                "you can use the 'Indicator Data Analysis' button to analyze the data and automatically determine the background values. "
                "The 'ECDF' button can be used to draw the ECDF diagram of the indicator data. "
                "After inputting the background values, click the 'Next' button to go to the next step."
            ),
        )  # type: ignore


class function_win(QWidget):

    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.gdf = result_dict.get("gdf")
        self.other_contaminants = result_dict.get("other_contaminants")
        self.final_boundarys = result_dict.get("final_boundarys")
        self.initUI()

    def initUI(self):
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
        self.adjustSize()
        self.export_button = QPushButton("Export to TableFile")
        self.export_button.clicked.connect(self.export_to_excel)
        self.plot_button = QPushButton("Plot results")
        self.plot_button.clicked.connect(self.plot_data)
        self.export_shp_button = QPushButton("Export to Spatial vector data")
        self.export_shp_button.clicked.connect(self.export_to_gpkg)
        self.auto_report_button = QPushButton("Auto report")
        self.auto_report_button.clicked.connect(self.auto_report)
        # Set the layout
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
        export_to_table(self.gdf, self)  # type: ignore

    def export_to_gpkg(self):
        export_to_vector_file(self.gdf, self)  # type: ignore

    def plot_data(self):
        from utils.pyside6_utils import show_multiple_plots

        figs = []
        for indicator, fig in self.result_dict.get("anomaly_figs"):
            if fig is not None:
                figs.append(fig)
        show_multiple_plots(figs)

    def auto_report(self):
        doc = auto_report()
        export_to_word(doc, self)  # type: ignore


class GeoDataFrameModel(QAbstractTableModel):
    def __init__(self, gdf, columns_to_display):
        super().__init__()

        self._gdf = gdf
        self._columns_to_display = columns_to_display

    def rowCount(self, parent=None):
        return len(self._gdf)

    def columnCount(self, parent=None):
        return len(self._columns_to_display)

    def data(self, index, role=Qt.DisplayRole):  # type: ignore
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


if __name__ == "__main__":
    ...
