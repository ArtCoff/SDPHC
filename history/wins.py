# #初始版本

# import sys
# from PySide6.QtCore import Qt, QAbstractTableModel
# from PySide6.QtGui import QFont
# from PySide6.QtWidgets import (
#     QApplication,
#     QMessageBox,
#     QTableView,
#     QLabel,
#     QWidget,
#     QComboBox,
#     QPushButton,
#     QLineEdit,
#     QFileDialog,
#     QVBoxLayout,
#     QHBoxLayout,
#     QFormLayout,
#     QGridLayout,
# )
# from draw import (
#     plot_boundary,
#     read_file_columns,
#     前处理,
#     计算单个指标得分,
#     计算其他土壤气得分,
#     计算总体得分,
#     绘制污染源区图,
#     计算污染范围,
#     绘制污染范围,
#     绘制超标点位,
#     污染等级识别,
# )


# class file_line_edit(QLineEdit):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setReadOnly(True)
#         self.setPlaceholderText("单击选择文件位置")
#         self.mousePressEvent = self.open_file_dialog
#         self.setStyleSheet("QLineEdit:hover {border:1px ridge black}")

#     def open_file_dialog(self, event):
#         file_dialog = QFileDialog(self)
#         file_dialog.setNameFilter(
#             "GPKG File(*.gpkg);;SHP File (*.shp);",
#         )
#         if file_dialog.exec():
#             file_path = file_dialog.selectedFiles()[0]
#             self.setText(file_path)


# class next_btn(QPushButton):
#     def __init__(self):
#         super().__init__()
#         self.setFixedSize(90, 30)
#         self.setText("Next ⏩")
#         self.setFont(QFont("Segoe UI", 12))
#         self.setStyleSheet(
#             """
#             QPushButton{
#                 border: 1px solid #8f8f91;
#                 border-radius: 1px;
#                 background-color: #dbdbdb;
#             }
#             QPushButton:hover {
#                 background-color: soild darkgray;
#             }
#             QPushButton:pressed {
#                 background-color: #3e8e41;
#             }
#             """
#         )


# class help_btn(QPushButton):
#     def __init__(self):
#         super().__init__()
#         self.setFixedSize(90, 30)
#         self.setText("Help ❓")
#         self.setFont(QFont("Segoe UI", 12))
#         self.setStyleSheet(
#             """
#             QPushButton{
#                 border: 1px solid #8f8f91;
#                 border-radius: 1px;
#                 background-color: #dbdbdb;
#             }"""
#         )


# class CustomComboBox(QComboBox):
#     def __init__(self, options, index, parent=None):
#         super().__init__(parent)
#         self.addItems(options)
#         self.index = index


# class Start_Window(QWidget):
#     def __init__(self, parent=None):
#         super(Start_Window, self).__init__(parent)
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle("微扰动污染识别辅助功能软件")
#         self.setGeometry(100, 100, 400, 200)
#         form_layout = QFormLayout()
#         self.outline_shp = file_line_edit()
#         self.point_shp = file_line_edit()
#         self.help_btn = help_btn()
#         self.next_btn = next_btn()
#         form_layout.addRow("输入场地范围文件:", self.outline_shp)
#         form_layout.addRow("输入调查点位文件:", self.point_shp)
#         btn_layout = QHBoxLayout()
#         btn_layout.addStretch(90)  # 添加一个拉伸元素，使按钮靠右对齐
#         btn_layout.addWidget(self.help_btn, alignment=Qt.AlignRight)
#         btn_layout.addStretch(2)
#         btn_layout.addWidget(self.next_btn, alignment=Qt.AlignRight)
#         btn_layout.addStretch(8)
#         self.help_btn.clicked.connect(self.on_help_clicked)
#         self.next_btn.clicked.connect(self.on_next_clicked)
#         # 总体布局
#         v_layput = QVBoxLayout()
#         v_layput.addLayout(form_layout)
#         v_layput.addLayout(btn_layout)
#         self.setLayout(v_layput)
#         self.center_window()

#     def on_help_clicked(self):
#         msg_box = QMessageBox(self)
#         msg_box.setIcon(QMessageBox.Information)  # 设置图标为提示信息
#         msg_box.setWindowTitle("帮助")  # 设置标题
#         msg_box.setText(
#             "单击输入框以打开资源管理器选择输入\n\n支持输入GPKG和SHP文件\n\n场地范围应为封闭多边形\n\n调查点位应为点文件,并在属性表包含各监测指标\n\n输入文件会被转为EPSG:4547投影坐标系"
#         )
#         msg_box.setStandardButtons(QMessageBox.Ok)  # 添加一个“OK”按钮

#         # 显示消息框
#         msg_box.exec_()

#     def on_next_clicked(self):
#         if self.outline_shp.text() == "" or self.point_shp.text() == "":
#             QMessageBox.critical(self, "Error", "请输入数据!")
#             return
#         self.hide()
#         self.attribute_window = Attribute_Window(
#             data_points_shp=self.point_shp.text(),
#             outline_polygon_shp=self.outline_shp.text(),
#         )
#         self.attribute_window.show()

#     def center_window(self):
#         # 获取屏幕的中心位置
#         screen_geometry = QApplication.primaryScreen().availableGeometry()
#         screen_center = screen_geometry.center()

#         # 获取窗口的几何形状
#         window_geometry = self.frameGeometry()

#         # 将窗口移动到屏幕的中心位置
#         window_geometry.moveCenter(screen_center)
#         self.move(window_geometry.topLeft())


# class Attribute_Window(QWidget):

#     def __init__(self, data_points_shp, outline_polygon_shp):
#         super().__init__()
#         self.data_points_shp = data_points_shp
#         self.outline_polygon_shp = outline_polygon_shp
#         self.combos = []
#         self.initUI(options=read_file_columns(data_points_shp))

#     def initUI(self, options):
#         self.setWindowTitle("微扰动污染识别辅助功能软件")
#         self.setGeometry(100, 100, 400, 200)
#         self.outline_polygon_display_btn = QPushButton("显示场地范围")
#         self.outline_polygon_display_btn.clicked.connect(self.plot_boundary)
#         self.help_btn = help_btn()
#         self.next_btn = next_btn()
#         form_layout = QFormLayout()
#         btn_layout = QHBoxLayout()
#         btn_layout.addStretch(90)  # 添加一个拉伸元素，使按钮靠右对齐
#         btn_layout.addWidget(self.help_btn, alignment=Qt.AlignRight)
#         btn_layout.addStretch(2)
#         btn_layout.addWidget(self.next_btn, alignment=Qt.AlignRight)
#         btn_layout.addStretch(8)
#         self.help_btn.clicked.connect(self.on_help_clicked)
#         self.next_btn.clicked.connect(self.on_next_clicked)

#         total_layout = QVBoxLayout()
#         total_layout.addWidget(self.outline_polygon_display_btn)
#         total_layout.addLayout(form_layout)
#         total_layout.addLayout(btn_layout)

#         self.Monitoring_indicators = [
#             "点位编号",
#             "Radon",
#             "VOCs",
#             "CO2",
#             "O2",
#             "CH4",
#             "H2",
#             "H2S",
#         ]
#         for i in range(8):
#             combo = CustomComboBox(options, i)
#             form_layout.addRow(
#                 f"{self.Monitoring_indicators[i]}:", combo
#             )  # 添加七行监测指标
#             self.combos.append(combo)
#         self.set_initial_selections(options)
#         self.setLayout(total_layout)
#         self.center_window()

#     def set_initial_selections(self, options):
#         for i, data in enumerate(self.Monitoring_indicators):
#             if data in options:
#                 index = options.index(data)
#                 self.combos[i].setCurrentIndex(index)
#             else:
#                 self.combos[i].setCurrentIndex(-1)

#     def on_help_clicked(self):
#         msg_box = QMessageBox(self)
#         msg_box.setIcon(QMessageBox.Information)  # 设置图标为提示信息
#         msg_box.setWindowTitle("帮助")  # 设置标题
#         msg_box.setText(
#             "单击<显示场地范围>以绘制场地范围\n\n在下拉框中选择监测指标对应的字段\n\n"
#         )
#         msg_box.setStandardButtons(QMessageBox.Ok)  # 添加一个“OK”按钮

#         # 显示消息框
#         msg_box.exec_()

#     def on_next_clicked(self):
#         self.hide()
#         contents = self.get_combos_content()
#         self.Contamination_identification_win = Contamination_identification_win(
#             options=contents,
#             data_points_shp=self.data_points_shp,
#             outline_polygon_shp=self.outline_polygon_shp,
#         )
#         self.Contamination_identification_win.show()

#     def plot_boundary(self):
#         plot_boundary(self.outline_polygon_shp)

#     def get_combos_content(self):
#         return [combo.currentText() for combo in self.combos]

#     def center_window(self):
#         # 获取屏幕的中心位置
#         screen_geometry = QApplication.primaryScreen().availableGeometry()
#         screen_center = screen_geometry.center()

#         # 获取窗口的几何形状
#         window_geometry = self.frameGeometry()

#         # 将窗口移动到屏幕的中心位置
#         window_geometry.moveCenter(screen_center)
#         self.move(window_geometry.topLeft())


# class WrapButton(QPushButton):
#     def __init__(self, text, parent=None):
#         super().__init__(parent)

#         # 创建一个 QLabel 来承载按钮的文本
#         label = QLabel(text)
#         label.setWordWrap(True)
#         label.setAlignment(Qt.AlignCenter)

#         # 创建一个布局来放置 QLabel
#         layout = QVBoxLayout(self)
#         layout.addWidget(label)
#         layout.setContentsMargins(0, 0, 0, 0)


# class Contamination_identification_win(QWidget):

#     def __init__(self, options, data_points_shp, outline_polygon_shp):
#         super().__init__()
#         self.data_points_shp = data_points_shp
#         self.outline_polygon_shp = outline_polygon_shp
#         self.options = options
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle("微扰动污染识别辅助功能软件")
#         self.exit_btn = QPushButton("退出")
#         self.function1_btn = WrapButton("指示污染超标范围点位（除氡气）")
#         self.function2_btn = WrapButton("污染源区与疑似污染源区")
#         self.function4_btn = WrapButton("污染范围")
#         self.function5_btn = WrapButton("污染等级识别(Experimental)")
#         self.function1_btn.setFixedSize(130, 50)
#         self.function2_btn.setFixedSize(130, 50)
#         self.function4_btn.setFixedSize(130, 50)
#         self.function5_btn.setFixedSize(130, 50)

#         # 功能连接
#         self.exit_btn.clicked.connect(self.close)
#         self.function1_btn.clicked.connect(self.function1)
#         self.function2_btn.clicked.connect(self.function2)
#         self.function4_btn.clicked.connect(self.function4)
#         self.function5_btn.clicked.connect(self.function5)
#         # 布局
#         btn_layout = QGridLayout()
#         btn_layout.addWidget(self.function1_btn, 1, 1)
#         btn_layout.addWidget(self.function2_btn, 1, 2)
#         btn_layout.addWidget(self.function4_btn, 2, 1)
#         btn_layout.addWidget(self.function5_btn, 2, 2)
#         h4_layout = QHBoxLayout()
#         v_layout = QVBoxLayout()
#         h4_layout.addWidget(self.exit_btn)
#         v_layout.addLayout(btn_layout)
#         v_layout.addLayout(h4_layout)
#         self.setLayout(v_layout)
#         self.center_window()

#     def function1(self):
#         gdf = 前处理(self.data_points_shp, self.options)
#         gdf = 计算单个指标得分(gdf)
#         gdf["得分"] = gdf.apply(计算其他土壤气得分, axis=1)
#         display_gdf = gdf[gdf["得分"] >= 6]
#         self.result_win1 = function_win(
#             display_gdf,
#             [
#                 "点位编号",
#                 "VOCs赋分",
#                 "CO2赋分",
#                 "H2赋分",
#                 "O2赋分",
#                 "CH4赋分",
#                 "H2S赋分",
#                 "得分",
#             ],
#             all_gdf=display_gdf,
#             outline_polygon_file=self.outline_polygon_shp,
#             funtion_name="指示污染超标范围点位（除氡气）",
#         )
#         self.result_win1.show()

#     def function2(self):
#         gdf = 前处理(self.data_points_shp, self.options)
#         gdf = 计算总体得分(gdf)
#         dis_play_gdf = gdf[gdf["其他土壤气得分"] >= 6]
#         self.result_win2 = function_win(
#             dis_play_gdf,
#             ["点位编号", "其他土壤气得分", "氡气赋分", "所有指标得分"],
#             all_gdf=gdf,
#             outline_polygon_file=self.outline_polygon_shp,
#             funtion_name="污染源区与疑似污染源区",
#         )
#         self.result_win2.show()

#     def function4(self):
#         gdf = 计算污染范围(self.data_points_shp, self.options)
#         self.result_win4 = function_win(
#             gdf=gdf,
#             columns_to_display=["点位编号", "其他土壤气得分", "得分≥1"],
#             all_gdf=gdf,
#             outline_polygon_file=self.outline_polygon_shp,
#             funtion_name="污染范围",
#         )
#         self.result_win4.show()

#     def function5(self):
#         gdf = 前处理(
#             self.data_points_shp,
#             self.options,
#         )

#         gdf = 计算总体得分(gdf)
#         污染等级识别(
#             gdf,
#             self.outline_polygon_shp,
#         )

#     def center_window(self):
#         # 获取屏幕的中心位置
#         screen_geometry = QApplication.primaryScreen().availableGeometry()
#         screen_center = screen_geometry.center()

#         # 获取窗口的几何形状
#         window_geometry = self.frameGeometry()

#         # 将窗口移动到屏幕的中心位置
#         window_geometry.moveCenter(screen_center)
#         self.move(window_geometry.topLeft())


# class GeoDataFrameModel(QAbstractTableModel):
#     def __init__(self, gdf, columns_to_display):
#         super().__init__()

#         self._gdf = gdf
#         self._columns_to_display = columns_to_display

#     def rowCount(self, parent=None):
#         return len(self._gdf)

#     def columnCount(self, parent=None):
#         return len(self._columns_to_display)

#     def data(self, index, role=Qt.DisplayRole):
#         if role == Qt.DisplayRole:
#             column_name = self._columns_to_display[index.column()]
#             return str(self._gdf.iloc[index.row()][column_name])
#         return None

#     def headerData(self, section, orientation, role=Qt.DisplayRole):
#         if role == Qt.DisplayRole:
#             if orientation == Qt.Horizontal:
#                 return self._columns_to_display[section]
#             if orientation == Qt.Vertical:
#                 return str(self._gdf.index[section])
#         return None


# class function_win(QWidget):

#     def __init__(
#         self, gdf, columns_to_display, all_gdf, outline_polygon_file, funtion_name
#     ):
#         super().__init__()
#         self.gdf = gdf[columns_to_display]  #
#         self.all_gdf = all_gdf
#         self.outline_polygon_file = outline_polygon_file
#         self.function_name = funtion_name
#         # 创建表格视图
#         self.table_view = QTableView()
#         self.table_model = GeoDataFrameModel(self.gdf, columns_to_display)
#         self.table_view.setModel(self.table_model)
#         self.table_view.resizeColumnsToContents()
#         self.table_view.resizeRowsToContents()

#         # 调整窗口大小以适应表格内容
#         self.adjustSize()
#         self.resize(800, 600)
#         # 创建导出按钮
#         self.export_button = QPushButton("导出为Excel")
#         self.export_button.clicked.connect(self.export_to_excel)

#         # 创建绘图按钮
#         self.plot_button = QPushButton("绘制图形")
#         self.plot_button.clicked.connect(self.plot_data)

#         # 创建导出Shapefile按钮
#         self.export_shp_button = QPushButton("导出为GeoPackage")
#         self.export_shp_button.clicked.connect(self.export_to_gpkg)

#         # 创建布局
#         layout = QVBoxLayout()
#         layout.addWidget(self.table_view)
#         layout.addWidget(self.export_button)
#         layout.addWidget(self.export_shp_button)  # 添加导出Shapefile按钮
#         layout.addWidget(self.plot_button)
#         self.setLayout(layout)

#         self.setWindowTitle("GeoDataFrame Viewer")

#     def export_to_excel(self):
#         file_path, _ = QFileDialog.getSaveFileName(
#             self, "Save File", "", "Excel Files (*.xlsx)"
#         )
#         if file_path:
#             try:
#                 self.gdf.to_excel(file_path, index=False)
#                 QMessageBox.information(
#                     self, "Success", "File has been exported successfully!"
#                 )
#             except Exception as e:
#                 QMessageBox.critical(self, "Error", f"Failed to export file: {str(e)}")

#     def export_to_gpkg(self):
#         file_path, _ = QFileDialog.getSaveFileName(
#             self,
#             "Save File",
#             "",
#             "GeoPackage Files (*.gpkg)",
#         )
#         if file_path:
#             try:
#                 self.all_gdf.to_file(file_path, driver="GPKG")
#                 QMessageBox.information(
#                     self, "Success", "GeoPackage has been exported successfully!"
#                 )
#             except Exception as e:
#                 QMessageBox.critical(
#                     self, "Error", f"Failed to export GeoPackage: {str(e)}"
#                 )

#     def plot_data(self):
#         if self.function_name == "污染源区与疑似污染源区":
#             try:
#                 绘制污染源区图(self.all_gdf, self.outline_polygon_file)
#             except Exception as e:
#                 QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
#         elif self.function_name == "污染范围":
#             绘制污染范围(self.all_gdf, self.outline_polygon_file)
#         else:
#             绘制超标点位(self.all_gdf, self.outline_polygon_file)
#             # msg_box = QMessageBox(self)
#             # msg_box.setIcon(QMessageBox.Information)  # 设置图标为提示信息
#             # msg_box.setWindowTitle("提示")  # 设置标题
#             # msg_box.setText("这项功能是指示污染超标范围点位，不需要绘图\n\n")
#             # msg_box.setStandardButtons(QMessageBox.Ok)  # 添加一个“OK”按钮

#             # # 显示消息框
#             # msg_box.exec_()

#     def Contamination_identification(self):
#         if self.function_name == "污染源区与疑似污染源区":
#             try:
#                 绘制污染源区图(self.all_gdf, self.outline_polygon_file)
#             except Exception as e:
#                 QMessageBox.critical(self, "Error", f"Failed to plot data: {str(e)}")
#         elif self.function_name == "污染范围":
#             绘制污染范围(self.all_gdf, self.outline_polygon_file)
#         else:
#             绘制超标点位(self.all_gdf, self.outline_polygon_file)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     main = Start_Window()
#     main.show()
#     sys.exit(app.exec())
