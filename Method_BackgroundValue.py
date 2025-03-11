import sys
from PySide6.QtCore import Qt, QAbstractTableModel, Signal
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
from draw_EN import (
    plot_basic_info,
    read_file_columns,
    point_dataset_preprocess,
    绘制污染点位分布V2,
)
from PredefinedData import software_name
from CustomControl import (
    next_btn,
    file_line_edit,
    help_btn,
    CustomComboBox,
    WrapButton,
    bottom_buttons,
    PlotWindow,
)
from Pyside6Functions import center_window
from Method_ExperienceValue import Attribute_Window
from CustomControl import LoadingWindow
from auto_report_CN import auto_report


class Attribute_Window_BackgroundValue(Attribute_Window):

    def __init__(self, point_dataset, outline_dataset):
        super().__init__(
            point_dataset=point_dataset,
            outline_dataset=outline_dataset,
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
        with open("./ref/Monitoring_pollution.json", "r", encoding="utf-8") as f:
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
        self.background_value_win = background_value_input_manual(
            options=contents,
            points_dataset=self.point_dataset,
            outline_dataset=self.outline_dataset,
            other_contaminants=self.other_contaminants,
        )
        self.background_value_win.show()
        self.close()


class background_value_input_doublespinbox(QDoubleSpinBox):
    def __init__(self, range):
        super().__init__()
        self.setRange(0.0, range)
        self.setDecimals(4)


class background_value_input_manual(QWidget):
    def __init__(
        self, options, points_dataset, outline_dataset, other_contaminants=None
    ):
        super().__init__()
        self.initUI(options=options, gpkg_file=points_dataset)
        self.outline_dataset = outline_dataset
        self.other_contaminants = other_contaminants
        # print(options)

    def initUI(self, options, gpkg_file):
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.setWindowTitle(self.tr("Background value determination"))
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
            QLabel("Bq/m³"),
            QLabel("ppb"),
            QLabel("ppm"),
            QLabel("%"),
            QLabel("%"),
            QLabel("copies/g"),
        )
        kmeans_btn1, kmeans_btn2, kmeans_btn3, kmeans_btn4, kmeans_btn5, kmeans_btn6 = (
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
            QPushButton(self.tr("Clustering")),
        )
        kmeans_btn1.clicked.connect(lambda: self.plot_kemans_boundary("Radon", "Bq/m³"))
        kmeans_btn2.clicked.connect(lambda: self.plot_kemans_boundary("VOCs", "ppb"))
        kmeans_btn3.clicked.connect(lambda: self.plot_kemans_boundary("CO2", "ppm"))
        kmeans_btn4.clicked.connect(lambda: self.plot_kemans_boundary("O2", "%"))
        kmeans_btn5.clicked.connect(lambda: self.plot_kemans_boundary("CH4", "%"))
        kmeans_btn6.clicked.connect(
            lambda: self.plot_kemans_boundary(self.tr("Functional genes"), "copies/g")
        )
        ECDF_btn1, ECDF_btn2, ECDF_btn3, ECDF_btn4, ECDF_btn5, ECDF_btn6 = (
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
            QPushButton(self.tr("ECDF")),
        )
        ECDF_btn1.clicked.connect(lambda: self.plot_ECDF("Radon", "Bq/m³"))
        ECDF_btn2.clicked.connect(lambda: self.plot_ECDF("VOCs", "ppb"))
        ECDF_btn3.clicked.connect(lambda: self.plot_ECDF("CO2", "ppm"))
        ECDF_btn4.clicked.connect(lambda: self.plot_ECDF("O2", "%"))
        ECDF_btn5.clicked.connect(lambda: self.plot_ECDF("CH4", "%"))
        ECDF_btn6.clicked.connect(
            lambda: self.plot_ECDF(self.tr("Functional genes"), "copies/g")
        )

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
        self.bottom_buttons.next_btn_clicked.connect(self.next_step)
        self.bottom_buttons.help_btn_clicked.connect(self.on_help_clicked)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.addLayout(Gridlayout)
        main_layout.addWidget(self.bottom_buttons)
        self.setLayout(main_layout)
        center_window(self)

    def do(self):
        pass
        indices = [
            i
            for i, value in enumerate(options)
            # if value == "" or value == "No data available"
            if value == "No data available"
        ]
        print(indices)
        for i in indices:
            if i == 1:
                self.radon_background_value.setEnabled(False),
                kmeans_btn1.setEnabled(False)
                kmeans_btn1.setText(self.tr("No Data"))
            elif i == 2:
                self.VOCs_background_value.setEnabled(False),
                kmeans_btn2.setEnabled(False)
                kmeans_btn2.setText(self.tr("No Data"))
            elif i == 3:
                self.CO2_background_value.setEnabled(False),
                kmeans_btn3.setText(self.tr("No Data"))
                kmeans_btn3.setEnabled(False)
            elif i == 4:
                self.O2_background_value.setEnabled(False),
                kmeans_btn4.setText(self.tr("No Data"))
                kmeans_btn4.setEnabled(False)
            elif i == 5:
                self.CH4_background_value.setEnabled(False),
                kmeans_btn5.setText(self.tr("No Data"))
                kmeans_btn5.setEnabled(False)
            elif i == 6:
                self.gene_background_value.setEnabled(False),
                kmeans_btn6.setText(self.tr("No Data"))
                kmeans_btn6.setEnabled(False)
        kemans_boundarys = self.init_kemans(gpkg_file, options)
        self.radon_background_value.setValue(kemans_boundarys[0])
        self.VOCs_background_value.setValue(kemans_boundarys[1])
        self.CO2_background_value.setValue(kemans_boundarys[2])
        self.O2_background_value.setValue(kemans_boundarys[3])
        self.CH4_background_value.setValue(kemans_boundarys[4])
        self.gene_background_value.setValue(kemans_boundarys[5])

    def init_kemans(self, gpkg_file, options):
        # options = ["点位", "无数据", "VOCs", "CO2", "O2", "CH4", ""]
        self.gdf = point_dataset_preprocess(gpkg_file, options)
        from draw_EN import get_kemans_boundary, plot_kemans_boundary

        kmeans_indicator = ["Radon", "VOCs", "CO2", "O2", "CH4", "Functional_genes"]
        units = ["Bq/m³", "ppb", "ppm", "%", "%", "copies/g"]
        kmeans_boundary_radon = get_kemans_boundary(self.gdf, "Radon")
        kmeans_boundary_VOCs = get_kemans_boundary(self.gdf, "VOCs")
        kmeans_boundary_CO2 = get_kemans_boundary(self.gdf, "CO2")
        kmeans_boundary_O2 = get_kemans_boundary(self.gdf, "O2")
        kmeans_boundary_CH4 = get_kemans_boundary(self.gdf, "CH4")
        kmeans_boundary_gene = get_kemans_boundary(self.gdf, "Functional genes")

        # 将kmeans_boundarys保存到文件提供给报告
        # for i, indicator in enumerate(kmeans_indicator):
        #     plot_kemans_boundary(
        #         self.gdf[indicator].dropna(), indicator, units[i], save=True
        #     )
        return [
            kmeans_boundary_radon,
            kmeans_boundary_VOCs,
            kmeans_boundary_CO2,
            kmeans_boundary_O2,
            kmeans_boundary_CH4,
            kmeans_boundary_gene,
        ]

    @property
    def get_final_boundarys(self):
        key = ["radon", "VOCs", "CO2", "O2", "CH4", "Functional_gene"]
        value = [
            self.radon_background_value.value(),
            self.VOCs_background_value.value(),
            self.CO2_background_value.value(),
            self.O2_background_value.value(),
            self.CH4_background_value.value(),
            self.gene_background_value.value(),
        ]
        return dict(zip(key, value))

    def anomaly_identification(self):
        header = [
            "氡气异常低",
            "VOCs异常高",
            "CO2异常高",
            "O2异常低",
            "CH4异常高",
            "功能基因异常高",
        ]
        boundarys = self.get_final_boundarys
        print(boundarys)
        self.gdf["氡气异常低"] = self.gdf["Radon"].apply(
            lambda x: (
                "×"
                if x is not None and x > boundarys.get("radon")  # 大于阈值时赋值为 1
                else (
                    "√"
                    if x is not None and x <= boundarys[0]  # 小于或等于阈值时赋值为 0
                    else "⚪"
                )
            )
        )
        self.gdf["VOCs异常高"] = self.gdf["VOCs"].apply(
            lambda x: (
                "√"
                if x is not None and x > boundarys.get("VOCs")  # 大于阈值时赋值为 1
                else (
                    "×"
                    if x is not None and x <= boundarys[1]  # 小于或等于阈值时赋值为 0
                    else "⚪"
                )
            )
        )
        self.gdf["O2异常低"] = self.gdf["O2"].apply(
            lambda x: (
                "×"
                if x is not None and x > boundarys.get("O2")  # 大于阈值时赋值为 1
                else (
                    "√"
                    if x is not None
                    and x <= boundarys.get("O2")  # 小于或等于阈值时赋值为 0
                    else "⚪"
                )
            )
        )
        self.gdf["CO2异常高"] = self.gdf["CO2"].apply(
            lambda x: (
                "√"
                if x is not None and x >= boundarys[2]  # 大于阈值时赋值为 1
                else (
                    "×"
                    if x is not None and x < boundarys[2]  # 小于或等于阈值时赋值为 0
                    else "⚪"
                )
            )
        )
        self.gdf["CH4异常高"] = self.gdf["CH4"].apply(
            lambda x: (
                "√"
                if x is not None and x >= boundarys[4]  # 大于阈值时赋值为 1
                else (
                    "×"
                    if x is not None and x < boundarys[4]  # 小于或等于阈值时赋值为 0
                    else "⚪"
                )
            )
        )
        self.gdf["功能基因异常高"] = self.gdf["功能基因"].apply(
            lambda x: (
                "√"
                if x is not None and x >= boundarys[5]  # 大于阈值时赋值为 1
                else (
                    "×"
                    if x is not None and x < boundarys[5]  # 小于或等于阈值时赋值为 0
                    else "⚪"
                )
            )
        )
        return self.gdf

    def next_step(self):
        self.hide()
        new_gdf = self.anomaly_identification()
        header = [
            "氡气异常低",
            "VOCs异常高",
            "CO2异常高",
            "O2异常低",
            "CH4异常高",
            "功能基因异常高",
        ]
        # print(new_gdf)
        self.result_win = analyse_win(
            gdf=new_gdf,
            outline_polygon_file=self.outline_polygon_shp,
            other_contaminants=self.other_contaminants,
            final_boundarys=self.get_final_boundarys(),
        )
        self.result_win.show()

    def plot_kemans_boundary(self, indicator, unit):
        from draw_EN import plot_kemans_boundary

        plot_kemans_boundary(self.gdf[indicator].dropna(), indicator, unit)

    def plot_ECDF(self, indicator, unit):
        pass
        # from draw_EN import plot_ECDF

        # plot_ECDF(self.gdf[indicator].dropna(), indicator, unit)

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


class analyse_win(QWidget):

    def __init__(
        self, gdf, outline_polygon_file, other_contaminants=None, final_boundarys=None
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
        self.setWindowTitle(software_name)
        self.exit_btn = QPushButton("退出")
        self.function1_btn = WrapButton("污染点位判定矩阵")
        self.function2_btn = WrapButton("异常点位分布图")
        self.function4_btn = WrapButton("所有点位报告")
        self.function5_btn = WrapButton("调查报告生成")
