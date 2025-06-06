import logging
from enum import Enum
from PySide6.QtCore import Signal, Slot, QThread
from PySide6.QtWidgets import (
    QMessageBox,
    QTableView,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
)

from core import (
    calculate_ExperienceValueMethod_scores,
    plot_basic_info,
    read_file_columns,
    export_to_word,
    export_to_table,
    export_to_vector_file,
)
from utils import (
    Software_info,
    NIS_indicators,
    Methods,
    AppStyle,
    Secondary_Functions_of_ETA,
    center_window,
    show_multiple_plots,
)
from report_templates import auto_report_for_empirical_threshold_analysis
from .custom_controls import (
    next_btn,
    help_btn,
    WrapButton,
    CustomComboBox,
    GeoDataFrameModel,
    bottom_buttons,
    LoadingWindow,
)


class worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, point_dataset, options, outline_dataset):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options
        self.outline_dataset = outline_dataset

    def run(self):
        result_dict = calculate_ExperienceValueMethod_scores(
            self.point_dataset, self.options, self.outline_dataset
        )
        self.result_ready.emit(result_dict)
        self.finished_signal.emit()


class Attribute_Window(QWidget):

    def __init__(self, point_dataset, outline_dataset, method: Enum):
        super().__init__()
        self.method = method
        self.point_dataset = point_dataset
        self.outline_dataset = outline_dataset

        self.initUI(options=read_file_columns(self.point_dataset))

    def initUI(self, options):
        self.setWindowTitle(Software_info.software_name.value)
        self.resize(500, 300)
        self.setMinimumSize(400, 300)
        self.setWindowIcon(AppStyle.icon())
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
        # * add combox
        self.combos = []
        self.combos.append(CustomComboBox(options, attribute="Point_ID"))
        self.form_layout.addRow("Point ID:", self.combos[0])
        for indicator in NIS_indicators:
            combo = CustomComboBox(options, attribute=indicator.value.name)
            self.form_layout.addRow(f"{indicator.value.label}:", combo)
            self.combos.append(combo)
        self.method_control_combos(self.method)
        self.setLayout(total_layout)
        center_window(self)

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
        self.worker = worker(
            self.point_dataset, contents, outline_dataset=self.outline_dataset
        )
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)
    def on_worker_result_ready(self, result_dict):
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
        self.Contamination_identification_win = Contamination_identification_win(
            result_dict=result_dict
        )
        self.Contamination_identification_win.show()
        self.close()

    def plot_dataset_info(self):
        fig = plot_basic_info(
            point_dataset=self.point_dataset, outline_dataset=self.outline_dataset
        )
        show_multiple_plots(fig)

    def get_combos_content(self):
        combo1_content = lambda: (
            None
            if self.combos[0].currentText() == "No data available"
            else self.combos[0].currentText()
        )
        final_combos = {
            "Point_ID": combo1_content(),
        }

        for combo in self.combos[1:]:
            if combo.currentText() == "No data available":
                final_combos[combo.attribute] = None
            else:
                final_combos[combo.attribute] = combo.currentText()
        print(final_combos)
        return final_combos

    def method_control_combos(self, method):
        if method == Methods.Empirical_Threshold_Analysis:
            self.combos[-1].setEnabled(False)


class Contamination_identification_win(QWidget):

    def __init__(self, result_dict):
        super().__init__()
        self.result_dict = result_dict
        self.result_gdf = result_dict["gdf"]
        self.initUI()

    def initUI(self):
        self.setWindowTitle(Software_info.software_name.value)
        self.setWindowIcon(AppStyle.icon())
        self.resize(500, 300)
        self.setMinimumSize(400, 200)

        self.function1_btn = WrapButton(
            self.tr("Contamination exceedance points (except radon gas)")
        )
        self.function2_btn = WrapButton(
            self.tr("Contamination source zone and suspected source zone")
        )
        self.function4_btn = WrapButton(self.tr("Scope of contamination"))
        self.function5_btn = WrapButton(self.tr("Contamination level identification"))
        self.auto_report_btn = WrapButton(self.tr("Auto report"))

        # function connections
        self.function1_btn.clicked.connect(self.function_PCP)
        self.function2_btn.clicked.connect(self.function_PSA)
        self.function4_btn.clicked.connect(self.function_SOC)
        self.function5_btn.clicked.connect(self.function_PLI)
        self.auto_report_btn.clicked.connect(self.auto_report)
        # Layout
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self.function1_btn)
        btn_layout.addWidget(self.function2_btn)
        btn_layout.addWidget(self.function4_btn)
        btn_layout.addWidget(self.function5_btn)
        btn_layout.addWidget(self.auto_report_btn)

        self.setLayout(btn_layout)
        center_window(self)

    def function_PCP(self):
        display_gdf = self.result_gdf[self.result_gdf["The_other_soil_gas_scores"] >= 6]
        self.result_win1 = function_win(
            result_dict=self.result_dict,
            display_gdf=display_gdf,
            columns_to_display=[
                "Point_ID",
                "VOCs_Score",
                "CO2_Score",
                "H2_Score",
                "O2_Score",
                "CH4_Score",
                "H2S_Score",
                "The_other_soil_gas_scores",
            ],
            funtion_name=Secondary_Functions_of_ETA.function_PCP,
        )
        self.result_win1.show()

    def function_PSA(self):
        dis_play_gdf = self.result_gdf[
            self.result_gdf["The_other_soil_gas_scores"] >= 6
        ]
        self.result_win2 = function_win(
            result_dict=self.result_dict,
            display_gdf=dis_play_gdf,
            columns_to_display=[
                "Point_ID",
                "The_other_soil_gas_scores",
                "Radon_Score",
                "All_indicators_Scores",
            ],
            funtion_name=Secondary_Functions_of_ETA.function_PSA,
        )
        self.result_win2.show()

    def function_SOC(self):
        self.result_win4 = function_win(
            result_dict=self.result_dict,
            display_gdf=self.result_gdf,
            columns_to_display=[
                "Point_ID",
                "The_other_soil_gas_scores",
                "Scope_of_contamination",
            ],
            funtion_name=Secondary_Functions_of_ETA.function_SOC,
        )
        self.result_win4.show()

    def function_PLI(self):
        show_multiple_plots(self.result_dict.get("pollution_level_fig"))

    def auto_report(self):

        doc = auto_report_for_empirical_threshold_analysis(self.result_dict["gdf"])
        export_to_word(doc, self)


class function_win(QWidget):

    def __init__(
        self,
        result_dict,
        display_gdf,
        columns_to_display,
        funtion_name,
    ):
        super().__init__()
        self.setWindowIcon(AppStyle.icon())
        self.result_dict = result_dict
        self.all_gdf = result_dict["gdf"]
        self.gdf = display_gdf[columns_to_display]  #
        self.function_name = funtion_name
        self.table_view = QTableView()
        self.table_model = GeoDataFrameModel(self.gdf, columns_to_display)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()
        self.adjustSize()
        self.resize(800, 600)
        # plot button
        self.plot_button = QPushButton(self.tr("Display plot"))
        self.plot_button.clicked.connect(self.plot_data)
        # Export Buttons
        self.export_table_button = QPushButton(self.tr("Export to Table File"))
        self.export_table_button.clicked.connect(self.export_to_table)
        self.export_vector_button = QPushButton(self.tr("Export to Vector File"))
        self.export_vector_button.clicked.connect(self.export_to_gpkg)

        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.table_view)
        layout.addWidget(self.export_table_button)
        layout.addWidget(self.export_vector_button)
        layout.addWidget(self.plot_button)
        self.setLayout(layout)

        self.setWindowTitle("Result Viewer")
        center_window(self)

    def export_to_table(self):
        export_to_table(self.gdf, self)

    def export_to_gpkg(self):
        export_to_vector_file(self.all_gdf, self)

    def plot_data(self):
        if self.function_name == Secondary_Functions_of_ETA.function_PSA:
            try:
                show_multiple_plots(self.result_dict.get("source_fig"))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == Secondary_Functions_of_ETA.function_SOC:
            try:
                show_multiple_plots(self.result_dict.get("scope_fig"))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == Secondary_Functions_of_ETA.function_PCP:
            try:
                show_multiple_plots(self.result_dict.get("exceed_fig"))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
