import sys
from PySide6.QtCore import Qt, QAbstractTableModel, Signal
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
from draw_EN import (
    plot_basic_info,
    read_file_columns,
    point_dataset_preprocess,
    计算单个指标得分,
    计算其他土壤气得分,
    计算总体得分,
    绘制污染源区图,
    计算污染范围,
    绘制污染范围,
    绘制超标点位,
    污染等级识别,
)
from PredefinedData import software_name
from CustomControl import (
    next_btn,
    help_btn,
    CustomComboBox,
    WrapButton,
    WrapButton_EN,
    GeoDataFrameModel,
)
from Pyside6Functions import center_window


class Attribute_Window(QWidget):

    def __init__(self, point_dataset, outline_dataset):
        super().__init__()
        self.point_dataset = point_dataset
        self.outline_dataset = outline_dataset
        self.combos = []
        self.initUI(options=read_file_columns(point_dataset))

    def initUI(self, options):
        self.setWindowTitle(software_name)
        self.setMinimumSize(400, 300)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.plot_dataset_info_btn = QPushButton(
            self.tr("Displays an overview of the data")
        )
        self.plot_dataset_info_btn.clicked.connect(self.plot_dataset_info)
        self.help_btn = help_btn()
        self.next_btn = next_btn()
        self.form_layout = QFormLayout()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(90)  # 添加一个拉伸元素，使按钮靠右对齐
        btn_layout.addWidget(self.help_btn, alignment=Qt.AlignRight)
        btn_layout.addStretch(2)
        btn_layout.addWidget(self.next_btn, alignment=Qt.AlignRight)
        btn_layout.addStretch(8)
        self.help_btn.clicked.connect(self.on_help_clicked)
        self.next_btn.clicked.connect(self.on_next_clicked)

        total_layout = QVBoxLayout()
        total_layout.addWidget(self.plot_dataset_info_btn)
        total_layout.addLayout(self.form_layout)
        total_layout.addLayout(btn_layout)

        self.Monitoring_indicators = [
            self.tr("Point number"),
            self.tr("Radon"),
            "VOCs",
            "CO2",
            "O2",
            "CH4",
            "H2",
            "H2S",
            self.tr("Functional genes"),
        ]
        for i in range(9):
            combo = CustomComboBox(options, i)
            self.form_layout.addRow(f"{self.Monitoring_indicators[i]}:", combo)
            self.combos.append(combo)
        self.set_initial_selections(options)
        self.setLayout(total_layout)
        center_window(self)

    def set_initial_selections(self, options):
        for i, data in enumerate(self.Monitoring_indicators):
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
        self.hide()
        contents = self.get_combos_content()
        self.Contamination_identification_win = Contamination_identification_win(
            options=contents,
            point_dataset=self.point_dataset,
            outline_dataset=self.outline_dataset,
        )
        self.Contamination_identification_win.show()

    def plot_dataset_info(self):
        plot_basic_info(
            point_dataset=self.point_dataset, outline_dataset=self.outline_dataset
        )

    def get_combos_content(self):
        return [combo.currentText() for combo in self.combos]


class Contamination_identification_win(QWidget):

    def __init__(self, options, point_dataset, outline_dataset):
        super().__init__()
        self.point_dataset = point_dataset
        self.outline_dataset = outline_dataset
        self.options = options
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.tr(software_name))
        self.setGeometry(100, 100, 400, 200)
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        center_window(self)
        self.exit_btn = QPushButton(self.tr("Quit"))
        # self.function1_btn = WrapButton(self.tr("指示污染超标范围点位（除氡气）"))
        # self.function2_btn = WrapButton(self.tr("污染源区与疑似污染源区"))
        # self.function4_btn = WrapButton(self.tr("污染范围"))
        # self.function5_btn = WrapButton(self.tr("污染等级识别"))
        self.function1_btn = WrapButton_EN(
            self.tr("Pollution exceedance points (except radon gas)")
        )
        self.function2_btn = WrapButton_EN(
            self.tr("Pollution source area and suspected pollution source area")
        )
        self.function4_btn = WrapButton_EN(self.tr("Scope of contamination"))
        self.function5_btn = WrapButton_EN(self.tr("Pollution level identification"))
        # self.function1_btn.setFixedSize(150, 60)
        # self.function2_btn.setFixedSize(150, 60)
        # self.function4_btn.setFixedSize(150, 60)
        # self.function5_btn.setFixedSize(150, 60)

        # 功能连接
        self.exit_btn.clicked.connect(self.close)
        self.function1_btn.clicked.connect(self.function1)
        self.function2_btn.clicked.connect(self.function2)
        self.function4_btn.clicked.connect(self.function4)
        self.function5_btn.clicked.connect(self.function5)
        # 布局
        # CN Layput
        # btn_layout = QGridLayout()
        # btn_layout.addWidget(self.function1_btn, 1, 1)
        # btn_layout.addWidget(self.function2_btn, 1, 2)
        # btn_layout.addWidget(self.function4_btn, 2, 1)
        # btn_layout.addWidget(self.function5_btn, 2, 2)
        # EN Layout
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

    def function1(self):
        gdf = point_dataset_preprocess(self.point_dataset, self.options)
        gdf = 计算单个指标得分(gdf)
        gdf["The_Other_soil_gas_scores"] = gdf.apply(计算其他土壤气得分, axis=1)
        display_gdf = gdf[gdf["The_Other_soil_gas_scores"] >= 6]
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
                "The_Other_soil_gas_scores",
            ],
            all_gdf=display_gdf,
            outline_polygon_file=self.outline_dataset,
            funtion_name="指示污染超标范围点位（除氡气）",
        )
        self.result_win1.show()

    def function2(self):
        gdf = point_dataset_preprocess(self.point_dataset, self.options)
        gdf = 计算总体得分(gdf)
        dis_play_gdf = gdf[gdf["其他土壤气得分"] >= 6]
        self.result_win2 = function_win(
            dis_play_gdf,
            ["点位编号", "其他土壤气得分", "氡气赋分", "所有指标得分"],
            all_gdf=gdf,
            outline_polygon_file=self.outline_dataset,
            funtion_name="污染源区与疑似污染源区",
        )
        self.result_win2.show()

    def function4(self):
        gdf = 计算污染范围(self.point_dataset, self.options)
        self.result_win4 = function_win(
            gdf=gdf,
            columns_to_display=["点位编号", "其他土壤气得分", "得分≥1"],
            all_gdf=gdf,
            outline_polygon_file=self.outline_dataset,
            funtion_name="污染范围",
        )
        self.result_win4.show()

    def function5(self):
        gdf = point_dataset_preprocess(
            self.point_dataset,
            self.options,
        )

        gdf = 计算总体得分(gdf)
        污染等级识别(
            gdf,
            self.outline_dataset,
        )


class function_win(QWidget):

    def __init__(
        self, gdf, columns_to_display, all_gdf, outline_polygon_file, funtion_name
    ):
        super().__init__()
        self.setWindowIcon(QIcon(r"./static/icon.ico"))
        self.gdf = gdf[columns_to_display]  #
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
        if self.function_name == "污染源区与疑似污染源区":
            try:
                绘制污染源区图(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == "污染范围":
            绘制污染范围(self.all_gdf, self.outline_polygon_file)
        else:
            绘制超标点位(self.all_gdf, self.outline_polygon_file)

    def Contamination_identification(self):
        if self.function_name == "污染源区与疑似污染源区":
            try:
                绘制污染源区图(self.all_gdf, self.outline_polygon_file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
        elif self.function_name == "污染范围":
            绘制污染范围(self.all_gdf, self.outline_polygon_file)
        else:
            绘制超标点位(self.all_gdf, self.outline_polygon_file)
