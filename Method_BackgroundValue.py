import sys
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QThread, Slot
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QTableView,
    QLabel,
    QWidget,
    QComboBox,
    QPushButton,
    QRadioButton,
    QDoubleSpinBox,
    QPlainTextEdit,
    QLineEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
)
from Method_Functions import (
    read_file_columns,
    point_dataset_preprocess,
    绘制污染点位分布V2,
    process_background_value_method,
)
from PredefinedData import Software_info, MIM_indicators
from CustomControl import (
    background_value_input_doublespinbox,
    WrapButton,
    bottom_buttons,
    LoadingWindow,
    PlotWindow,
)
from Pyside6Functions import center_window
from Method_ExperienceValue import Attribute_Window
from auto_report_CN import auto_report


class backgroundValue_worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, point_dataset, options):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options

    def run(self):
        gdf = point_dataset_preprocess(self.point_dataset, self.options)
        # columns = [indicator.value.name for indicator in MIM_indicators]
        # process_background_value_method(gdf, columns)
        # results[col] = (ecdf_fig, kmeans_boundary, kmeans_fig)
        result_dict = process_background_value_method(gdf)
        # 返回ECDF绘图对象
        # 返回Kmeans绘图对象和边界值
        # 返回预处理的gdf
        # 返回异常点位绘图对象
        self.result_ready.emit(result_dict)
        self.finished_signal.emit()


class anomaly_identification_worker(QThread):
    finished_signal = Signal()
    result_ready = Signal(object)

    def __init__(self, point_dataset, options, final_boundarys):
        super().__init__()
        self.point_dataset = point_dataset
        self.options = options
        self.final_boundarys = final_boundarys

    def run(self):
        self.result_ready.emit()
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
        with open("./static/Monitoring_pollution.json", "r", encoding="utf-8") as f:
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
        self.background_value_win = background_value_input_manual(
            result_dict=result_dict,
            outline_dataset=self.outline_dataset,
        )
        self.background_value_win.show()
        self.close()


class background_value_input_manual(QWidget):

    def __init__(self, result_dict, outline_dataset, other_contaminants=None):
        super().__init__()
        self.result_dict = result_dict
        self.outline_dataset = outline_dataset
        self.other_contaminants = other_contaminants
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setWindowTitle(self.tr("Background value manual input"))
        self.setGeometry(100, 100, 500, 300)
        self.setMinimumSize(500, 300)
        # 创建一个网格布局
        Gridlayout = QGridLayout()
        Gridlayout.setSpacing(10)
        # 设置列的拉伸因子
        Gridlayout.setColumnStretch(0, 1)  # 标签列
        Gridlayout.setColumnStretch(1, 2)  # 输入框列
        Gridlayout.setColumnStretch(2, 1)  # 单位列
        Gridlayout.setColumnStretch(3, 1)  # 聚类按钮列
        Gridlayout.setColumnStretch(4, 1)  # ECDF按钮列
        (
            self.radon_background_value,
            self.VOCs_background_value,
            self.CO2_background_value,
            self.O2_background_value,
            self.CH4_background_value,
            self.gene_background_value,
        ) = (
            background_value_input_doublespinbox(range=999999),
            background_value_input_doublespinbox(range=999999),
            background_value_input_doublespinbox(range=999999),
            background_value_input_doublespinbox(range=100),
            background_value_input_doublespinbox(range=100),
            background_value_input_doublespinbox(range=999999),
        )
        unit_label1, unit_label2, unit_label3, unit_label4, unit_label5, unit_label6 = (
            QLabel(MIM_indicators.Radon.value.unit),
            QLabel(MIM_indicators.VOCs.value.unit),
            QLabel(MIM_indicators.CO2.value.unit),
            QLabel(MIM_indicators.O2.value.unit),
            QLabel(MIM_indicators.CH4.value.unit),
            QLabel(MIM_indicators.FG.value.unit),
        )
        kmeans_btn1, kmeans_btn2, kmeans_btn3, kmeans_btn4, kmeans_btn5, kmeans_btn6 = (
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
        )
        kmeans_btn1.clicked.connect(
            lambda: self.plot_kemans_boundary(MIM_indicators.Radon)
        )
        kmeans_btn2.clicked.connect(
            lambda: self.plot_kemans_boundary(MIM_indicators.VOCs)
        )
        kmeans_btn3.clicked.connect(
            lambda: self.plot_kemans_boundary(MIM_indicators.CO2)
        )
        kmeans_btn4.clicked.connect(
            lambda: self.plot_kemans_boundary(MIM_indicators.O2)
        )
        kmeans_btn5.clicked.connect(
            lambda: self.plot_kemans_boundary(MIM_indicators.CH4)
        )
        kmeans_btn6.clicked.connect(
            lambda: self.plot_kemans_boundary(MIM_indicators.FG)
        )
        ECDF_btn1, ECDF_btn2, ECDF_btn3, ECDF_btn4, ECDF_btn5, ECDF_btn6 = (
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
        )
        ECDF_btn1.clicked.connect(lambda: self.plot_ECDF(MIM_indicators.Radon))
        ECDF_btn2.clicked.connect(lambda: self.plot_ECDF(MIM_indicators.VOCs))
        ECDF_btn3.clicked.connect(lambda: self.plot_ECDF(MIM_indicators.CO2))
        ECDF_btn4.clicked.connect(lambda: self.plot_ECDF(MIM_indicators.O2))
        ECDF_btn5.clicked.connect(lambda: self.plot_ECDF(MIM_indicators.CH4))
        ECDF_btn6.clicked.connect(lambda: self.plot_ECDF(MIM_indicators.FG))

        # 统一设置按钮属性
        for btn in [
            kmeans_btn1,
            kmeans_btn2,
            kmeans_btn3,
            kmeans_btn4,
            kmeans_btn5,
            kmeans_btn6,
            ECDF_btn1,
            ECDF_btn2,
            ECDF_btn3,
            ECDF_btn4,
            ECDF_btn5,
            ECDF_btn6,
        ]:
            btn.setFixedWidth(100)
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
        # 添加行（保持原有行添加逻辑，但补充缺失的ECDF按钮）
        rows = [
            (
                "Radon:",
                self.radon_background_value,
                unit_label1,
                kmeans_btn1,
                ECDF_btn1,
            ),
            ("VOCs:", self.VOCs_background_value, unit_label2, kmeans_btn2, ECDF_btn2),
            (
                "CO<sub>2</sub>:",
                self.CO2_background_value,
                unit_label3,
                kmeans_btn3,
                ECDF_btn3,
            ),
            (
                "O<sub>2</sub>:",
                self.O2_background_value,
                unit_label4,
                kmeans_btn4,
                ECDF_btn4,
            ),
            (
                "CH<sub>4</sub>:",
                self.CH4_background_value,
                unit_label5,
                kmeans_btn5,
                ECDF_btn5,
            ),
            (
                self.tr("Functional genes:"),
                self.gene_background_value,
                unit_label6,
                kmeans_btn6,
                ECDF_btn6,
            ),
        ]

        for row_idx, (label, spinbox, unit, kmeans_btn, ecdf_btn) in enumerate(rows):
            # 设置标签右对齐
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 添加行内容
            Gridlayout.addWidget(lbl, row_idx, 0)
            Gridlayout.addWidget(spinbox, row_idx, 1)
            Gridlayout.addWidget(unit, row_idx, 2)
            Gridlayout.addWidget(kmeans_btn, row_idx, 3)
            Gridlayout.addWidget(ecdf_btn, row_idx, 4)

        #
        self.bottom_buttons = bottom_buttons()
        self.bottom_buttons.next_btn_clicked.connect(self.on_next_clicked)
        self.bottom_buttons.help_btn_clicked.connect(self.on_help_clicked)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.addLayout(Gridlayout)
        main_layout.addWidget(self.bottom_buttons)
        self.setLayout(main_layout)
        self.initKmeans()
        center_window(self)

    def initKmeans(self):
        # indices = [
        #     i
        #     for i, value in enumerate(self.result_dict)
        #     if value == "No data available"
        # ]
        #             self.radon_background_value.setEnabled(False),
        #             kmeans_btn1.setEnabled(False)
        #             kmeans_btn1.setText(self.tr("No Data"))
        self.radon_background_value.setValue(self.result_dict["Radon"].kmeans_boundary)
        self.VOCs_background_value.setValue(self.result_dict["VOCs"].kmeans_boundary)
        self.CO2_background_value.setValue(self.result_dict["CO2"].kmeans_boundary)
        self.O2_background_value.setValue(self.result_dict["O2"].kmeans_boundary)
        self.CH4_background_value.setValue(self.result_dict["CH4"].kmeans_boundary)
        self.gene_background_value.setValue(
            self.result_dict["Functional_gene"].kmeans_boundary
        )

    def plot_kemans_boundary(self, indicator):
        print(self.result_dict.keys())
        print(self.result_dict.get("O2"))
        # 确保结果存在
        if indicator not in self.result_dict:
            return QMessageBox.warning(self, "Warning", "未找到该指标的分析结果")
        fig = self.result_dict[indicator].kmeans_fig
        self.plot_window = PlotWindow(fig)
        self.plot_window.show()

    def plot_ECDF(self, indicator):
        if indicator not in self.result_dict:
            return QMessageBox.warning(self, "Warning", "未找到该指标的分析结果")
        fig = self.result_dict[indicator].ecdf_fig
        plot_window = PlotWindow(fig)
        plot_window.show()
        plot_window.exec()

    @property
    def get_final_boundarys(self):
        key = [indicator for indicator in MIM_indicators]
        value = [
            self.radon_background_value.value(),
            self.VOCs_background_value.value(),
            self.CO2_background_value.value(),
            self.O2_background_value.value(),
            self.CH4_background_value.value(),
            self.gene_background_value.value(),
        ]
        return dict(zip(key, value))

    def on_next_clicked(self):
        final_boundarys = self.get_final_boundarys
        self.loading_window = LoadingWindow()
        self.loading_window.show()
        self.worker = backgroundValue_worker(self.point_dataset, final_boundarys)
        self.worker.result_ready.connect(self.on_worker_result_ready)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(object)
    def on_worker_result_ready(self, result):
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
        self.function_win = function_win(
            result=result,
            outline_polygon_file=self.outline_polygon_shp,
        )
        self.background_value_win.show()
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

    def __init__(
        self,
        result,
        gdf,
        outline_polygon_file,
        other_contaminants=None,
        final_boundarys=None,
    ):
        super().__init__()
        self.other_contaminants = other_contaminants
        self.final_boundarys = final_boundarys
        self.gdf = self.Contamination_identification(gdf)
        header = [
            "点位",
            "氡气异常低",
            "VOCs异常高",
            "CO2异常高",
            "O2异常低",
            "CH4异常高",
            "功能基因异常高",
        ]
        self.outline_polygon_file = outline_polygon_file
        # 创建表格视图
        self.table_view = QTableView()
        self.table_model = GeoDataFrameModel(self.gdf, header)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()

        # 调整窗口大小以适应表格内容
        self.adjustSize()
        self.resize(800, 600)
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
        绘制污染点位分布V2(self.gdf)

    def Contamination_identification(self, gdf):
        import numpy as np

        # 直接利用布尔条件
        gdf["污染类型"] = "正常"  # 先默认设置
        # 判断污染羽
        conditions = [
            gdf["VOCs异常高"] == "√",
            (gdf["CO2异常高"] == "√") | (gdf["O2异常低"] == "√"),
            gdf["CH4异常高"] == "√",
            gdf["功能基因异常高"] == "√",
        ]
        gdf["满足辅助条件数目"] = np.sum(conditions, axis=0)
        gdf["污染类型"] = gdf["满足辅助条件数目"].apply(
            lambda x: "污染羽" if x >= 3 else "正常"
        )

        gdf["检出其他污染物数目"] = 0
        for i in self.other_contaminants:
            gdf["检出其他污染物数目"] += gdf[i].apply(lambda x: 1 if x >= 0 else 0)
        gdf["污染类型"] = gdf.apply(
            lambda row: "污染羽" if row["检出其他污染物数目"] >= 1 else row["污染类型"],
            axis=1,
        )
        # if "氡气异常低" in gdf.columns:
        gdf["污染类型"] = gdf.apply(
            lambda row: (
                "污染源"
                if (row["满足辅助条件数目"] >= 4) & (row["氡气异常低"] == "√")
                else row["污染类型"]
            ),
            axis=1,
        )
        return gdf

    def auto_report(self):
        import docx

        doc = auto_report(
            self.gdf, background_file=None, final_boundarys=self.final_boundarys
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出报告",
            "",
            "报告文件 (*.docx)",
        )
        if file_path:
            try:
                doc.save(file_path)
                QMessageBox.information(
                    self, "成功", "报告已经保存至本地，可以使用WPS或Word打开!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "错误！", f"报告保存失败，失败原因为: {str(e)}"
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


class Contamination_identification_on_background_value(QWidget):
    def __init__(self, gdf, outline_polygon_shp=None):
        super().__init__()
        self.gdf = gdf
        self.outline_polygon_shp = outline_polygon_shp
        self.initUI()

    def initUI(self):
        self.setWindowTitle(Software_info.software_name.value)
        self.exit_btn = QPushButton("退出")
        self.function1_btn = WrapButton("污染点位判定矩阵")
        self.function2_btn = WrapButton("异常点位分布图")
        self.function4_btn = WrapButton("所有点位报告")
        self.function5_btn = WrapButton("调查报告生成")
