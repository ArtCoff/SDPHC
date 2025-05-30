import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib

matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from utils.predefined_data import Drawing_specifications


# 添加指北针 (North Arrow)
def add_north_arrow(ax):
    x, y, arrow_length = 0.95, 0.95, 0.1
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - arrow_length),
        arrowprops=dict(arrowstyle="->"),
        ha="center",
        va="center",
        fontsize=12,
        xycoords=ax.transAxes,
    )


# 添加比例尺 (Scale Bar)
def add_scalebar(ax, location="lower left"):
    from matplotlib_scalebar.scalebar import ScaleBar

    scalebar = ScaleBar(
        dx=10,
        units="m",
        dimension="si-length",
        length_fraction=0.1,
        location=location,
        scale_loc="top",
        box_alpha=0,
    )
    ax.add_artist(scalebar)


def plot_basic_info(
    point_dataset, outline_dataset, epsg_code=Drawing_specifications.EPSG_code
):
    import geopandas as gpd
    from matplotlib import ticker, rcParams

    # 创建 matplotlib Figure 对象
    fig = Figure()
    ax = fig.add_subplot(111)
    fig.set_tight_layout(True)
    rcParams["font.family"] = "Times New Roman"
    try:
        # 读取数据
        point_gdf = gpd.read_file(point_dataset).to_crs(epsg=epsg_code)
        boundary_gdf = gpd.read_file(outline_dataset).to_crs(epsg=epsg_code)

        # 绘制图形
        boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="red", label="Boundary")
        point_gdf.plot(ax=ax, color="blue", markersize=10, label="Monitoring Points")

        # 添加辅助元素
        add_north_arrow(ax)
        add_scalebar(ax)
        ax.set_xlabel("X Coordinate", fontsize=12)
        ax.set_ylabel("Y Coordinate", fontsize=12)
        ax.legend(loc="lower right", fontsize=10)
        ax.tick_params(axis="both", labelsize=10)
        ax.autoscale()

        return fig
    except Exception as e:
        print(f"Plot Error: {str(e)}")
        return None


def read_file_columns(datapoints_shp):
    import geopandas as gpd

    gdf = gpd.read_file(datapoints_shp, chunksize=1)
    options = gdf.columns.tolist()
    return options


def point_dataset_preprocess(point_dataset, options):

    # 读取数据
    gdf = gpd.read_file(point_dataset).to_crs(epsg=Drawing_specifications.EPSG_code)
    # Key的类型为枚举类型，无法直接使用
    for key, value in options.items():
        if value in gdf.columns:
            gdf[key] = gdf[value]
        else:
            gdf[key] = None
    return gdf


def boundary_file_preprocess(boundary_file):
    # 读取数据
    boundary_gdf = gpd.read_file(boundary_file).to_crs(
        epsg=Drawing_specifications.EPSG_code
    )
    return boundary_gdf


def safe_remove(lst, item):
    try:
        lst.remove(item)
    except ValueError:
        pass
    return lst


def export_to_word(doc, parent):
    from PySide6.QtWidgets import QMessageBox, QFileDialog

    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Export report",
        "",
        "Reporting documents (*.docx)",
    )
    if file_path:
        try:
            doc.save(file_path)
            QMessageBox.information(
                parent,
                parent.tr("succeed"),
                parent.tr(
                    "The report has been saved locally and can be opened using Word!"
                ),
            )
        except Exception as e:
            QMessageBox.critical(
                parent, "failed", f"The report failed to be saved due to:{str(e)}"
            )


def export_to_table(gdf, parent):
    from PySide6.QtWidgets import QMessageBox, QFileDialog

    # 设置文件对话框，允许选择保存路径和文件类型
    file_path, selected_filter = QFileDialog.getSaveFileName(
        parent,
        "Save File",
        "",
        "Excel Files (*.xlsx);;CSV Files (*.csv)",
        options=QFileDialog.Options(),
    )

    if file_path:
        try:
            if selected_filter == "Excel Files (*.xlsx)":
                gdf.to_excel(file_path, index=False)
            elif selected_filter == "CSV Files (*.csv)":
                gdf.to_csv(file_path, index=False)

            QMessageBox.information(
                parent, "Success", "File has been exported successfully!"
            )
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to export file: {str(e)}")


def export_to_vector_file(gdf, parent):
    from PySide6.QtWidgets import QMessageBox, QFileDialog

    file_path, selected_filter = QFileDialog.getSaveFileName(
        parent,
        "Export Vector File",
        "",
        "GeoPackage Files (*.gpkg);;Shapefile Files (*.shp)",
        options=QFileDialog.Options(),
    )

    if file_path:
        try:
            if selected_filter == "GeoPackage Files (*.gpkg)":
                gdf.to_file(file_path, driver="GPKG")
            elif selected_filter == "Shapefile Files (*.shp)":
                gdf.to_file(file_path, driver="ESRI Shapefile")

            QMessageBox.information(
                parent, "Success", "File has been exported successfully!"
            )
        except Exception as e:
            QMessageBox.critical(
                parent, "Error", f"Failed to export vector file: {str(e)}"
            )


if __name__ == "__main__":
    ...
