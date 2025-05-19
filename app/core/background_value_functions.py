import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

matplotlib.use("QtAgg")

from utils.predefined_data import NIS_indicators, Drawing_specifications
from core.function_utils import (
    add_north_arrow,
    add_scalebar,
)


# * Background Value Method
def compute_ecdf(data):
    sorted_data = np.sort(data)
    n = len(sorted_data)
    cum_prob = np.arange(1, n + 1) / n  # y = i/n
    return sorted_data, cum_prob


def draw_ECDF(
    data,
    param_name="",
    unit="",
):
    fig = Figure(figsize=(10, 5))  # 创建一个 Figure 对象
    ax = fig.add_subplot(111)

    sorted_data, cum_prob = compute_ecdf(data)
    ax.step(sorted_data, cum_prob, where="post")
    ax.scatter(sorted_data, cum_prob, s=2, color="red", zorder=2, label="Points")
    ax.set_xlabel(f"{param_name} ({unit})" if unit else param_name)
    ax.set_ylabel("ECDF")
    ax.set_title(f"{param_name} ECDF Analysis")
    ax.grid(True)
    ax.legend()
    return fig


def draw_KMeans_cluster(data, param_name="", unit="", random_state=0):
    import numpy as np
    from sklearn.cluster import KMeans
    import geopandas as gpd

    """
    对输入的一组数据进行 KMeans 聚类，返回分界点和绘图对象。

    :param data: 输入的一组数据（列表、NumPy 数组等）
    :param param_name: 参数名称（用于显示）
    :param unit: 单位（用于坐标轴标签）
    :param random_state: KMeans 随机种子
    :return: (boundary, FigureCanvas)
    """
    # 将数据转换为二维数组
    data = np.array(data).reshape(-1, 1)
    if len(data) == 0:
        raise ValueError("输入数据不能为空")

    # KMeans 聚类
    kmeans = KMeans(n_clusters=2, random_state=random_state).fit(data)
    centers = kmeans.cluster_centers_.flatten()
    boundary = np.mean(centers)  # 使用聚类中心的均值作为分界点

    # 创建绘图对象
    fig = Figure(figsize=(8, 6), dpi=90)
    ax = fig.add_subplot(111)

    # 绘制数据点
    from collections import Counter

    data_counts = Counter(data.flatten())
    for point, count in data_counts.items():
        # 根据所属聚类分配颜色
        color = "blue" if point <= boundary else "orange"
        label = (
            "Part Ⅰ"
            if (point == min(data)) and color == "blue"
            else "Part Ⅱ" if (point == max(data)) and color == "orange" else ""
        )

        ax.scatter(point, 0, color=color, s=50, label=label)

        # 显示重复点计数
        if count > 1:
            ax.text(point, 0.005, f"{count}", ha="center", va="bottom", fontsize=10)

    # 绘制中心点和分界线
    ax.scatter(
        centers,
        [0] * len(centers),
        color="red",
        s=100,
        marker="x",
        label="Cluster Center",
    )
    ax.axvline(boundary, color="green", linestyle="--", label="Cut-off Value")
    ax.text(boundary, -0.05, f"{boundary:.2f}", ha="right", color="green", fontsize=12)

    # 设置图表属性
    ax.set_title(
        f"{param_name} KMeans cluster analysis"
        if param_name
        else "KMeans cluster analysis"
    )
    ax.set_xlabel(f"{param_name} ({unit})" if unit else param_name)
    ax.set_yticks([])
    ax.grid(axis="x", linestyle="--")
    ax.legend(ncol=2, fontsize=10)
    return boundary, fig


class BackgroundResult:
    def __init__(self, ecdf_fig=None, kmeans_boundary=None, kmeans_fig=None):
        self.ecdf_fig = ecdf_fig
        self.kmeans_boundary = kmeans_boundary
        self.kmeans_fig = kmeans_fig


def process_background_value_method(gdf):
    results = {}

    for col in [indicator for indicator in NIS_indicators]:
        print(f"Processing {col.value.name}...")
        unit = col.value.unit
        # 处理数据
        data = gdf[col.value.name].dropna().values  # .reshape(-1, 1)
        if data.size == 0:
            results[col] = BackgroundResult()
            continue

        # 生成图表
        try:
            ecdf_fig = draw_ECDF(data, param_name=col.value.name, unit=unit)
        except Exception as e:
            ecdf_fig = None
            print(f"ECDF生成失败({col}): {str(e)}")

        try:
            kmeans_boundary, kmeans_fig = draw_KMeans_cluster(
                data, param_name=col.value.name, unit=unit
            )
        except Exception as e:
            kmeans_boundary = None
            kmeans_fig = None
            print(f"KMeans分析失败({col}): {str(e)}")

        # 保存结果
        results[col] = BackgroundResult(
            ecdf_fig=ecdf_fig,
            kmeans_boundary=kmeans_boundary,
            kmeans_fig=kmeans_fig,
        )

    return results


def calculate_backgroundValue(data, boundarys):
    new_data = data.copy()
    gdf = new_data.get("gdf")
    result_gdf = anomaly_identification(gdf, boundarys)
    anomaly_figs = []
    headers = [
        ("Abnormally Low Radon", NIS_indicators.Radon),
        ("Abnormally High VOCs", NIS_indicators.VOCs),
        ("Abnormally High CO2", NIS_indicators.CO2),
        ("Abnormally Low O2", NIS_indicators.O2),
        ("Abnormally High CH4", NIS_indicators.CH4),
        ("Abnormally High Functional Genes", NIS_indicators.FG),
    ]
    for column, indicator in headers:
        anomaly_figs.append(
            (
                indicator,
                backgroundValue_anomaly_fig(
                    gdf=gdf,
                    column=column,
                    label=indicator.value.name,
                    boundary_polygon_file=new_data.get("outline_dataset"),
                ),
            ),
        )
    result_gdf["Point ID"] = result_gdf["Point_ID"]
    new_data["gdf"] = result_gdf
    new_data["anomaly_figs"] = anomaly_figs
    return new_data


def anomaly_identification(gdf, boundarys):
    gdf["Abnormally Low Radon"] = gdf[NIS_indicators.Radon.value.name].apply(
        lambda x: (
            "×"
            if x is not None
            and x > boundarys.get(NIS_indicators.Radon)  # 大于阈值时赋值为 1
            else (
                "√"
                if x is not None
                and x <= boundarys.get(NIS_indicators.Radon)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    gdf["Abnormally High VOCs"] = gdf[NIS_indicators.VOCs.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x > boundarys.get(NIS_indicators.VOCs)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x <= boundarys.get(NIS_indicators.VOCs)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    gdf["Abnormally Low O2"] = gdf[NIS_indicators.O2.value.name].apply(
        lambda x: (
            "×"
            if x is not None
            and x > boundarys.get(NIS_indicators.O2)  # 大于阈值时赋值为 1
            else (
                "√"
                if x is not None
                and x <= boundarys.get(NIS_indicators.O2)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    gdf["Abnormally High CO2"] = gdf[NIS_indicators.CO2.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x >= boundarys.get(NIS_indicators.CO2)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x < boundarys.get(NIS_indicators.CO2)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    gdf["Abnormally High CH4"] = gdf[NIS_indicators.CH4.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x >= boundarys.get(NIS_indicators.CH4)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x < boundarys.get(NIS_indicators.CH4)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    gdf["Abnormally High Functional Genes"] = gdf[NIS_indicators.FG.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x >= boundarys.get(NIS_indicators.FG)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x < boundarys.get(NIS_indicators.FG)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    return gdf


def backgroundValue_anomaly_fig(
    gdf,
    column,
    label,
    boundary_polygon_file=None,
):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from pathlib import Path

    matplotlib.rcParams["font.family"] = "Times New Roman"
    fig = Figure(figsize=(8, 6), dpi=90)
    ax = fig.add_subplot(111)

    boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=4547)
    boundary_polygon_gdf.plot(ax=ax, facecolor="none", edgecolor="red")
    colors = {"√": "red", "×": "green", "⚪": "white"}
    gdf["color"] = gdf[column].map(colors)
    all_null = (gdf["color"] == "white").all()
    if all_null:
        return None
    mask = gdf["color"] != "white"
    ax.scatter(
        gdf[mask].geometry.x,
        gdf[mask].geometry.y,
        marker="o",
        s=30,
        color=gdf[mask]["color"],
    )
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    legend_elements = []
    legend_elements.append(
        Line2D(
            [0],
            [0],  # x 和 y 数据
            color="none",  # 无色，只显示文字
            label=label,  # 图例标签
            markersize=0,  # 不显示标记
        )
    )
    legend_elements.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Normal point",
            markerfacecolor="green",
            markersize=10,
        )
    )
    legend_elements.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Anomalous point",
            markerfacecolor="red",
            markersize=10,
        )
    )

    ax.legend(
        handles=legend_elements,
    )
    return fig


def backgroundValue_anomaly_fig______(gdf, boundary_polygon_file=None, save=False):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    from matplotlib.lines import Line2D

    fig = Figure(figsize=(8, 6), dpi=90)
    ax = fig.add_subplot(111)
    matplotlib.rcParams["font.family"] = "Times New Roman"
    boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=4547)
    ax = boundary_polygon_gdf.plot(ax=ax, facecolor="none", edgecolor="red")
    colors = {"√": "red", "污染羽": "orange", "×": "green"}
    gdf["color"] = gdf["污染类型"].map(colors)
    ax.scatter(gdf.geometry.x, gdf.geometry.y, marker="o", s=30, color=gdf["color"])

    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    # 添加自定义图例
    legend_elements = []
    if "污染源" in gdf["污染类型"].unique():
        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Source Area",
                markerfacecolor="red",
                markersize=10,
            )
        )
    if "污染羽" in gdf["污染类型"].unique():
        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Plume",
                markerfacecolor="orange",
                markersize=10,
            )
        )
    if "正常" in gdf["污染类型"].unique():
        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Normal point",
                markerfacecolor="green",
                markersize=10,
            )
        )
    # 添加图例到右下角
    ax.legend(
        handles=legend_elements,
        # loc="lower right", bbox_to_anchor=(1, 0)
    )
    plt.tight_layout()
    return fig


# * 用于报告生成的函数
def 绘制点位分布(gdf, boundary_polygon_file=None):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    from matplotlib.lines import Line2D

    matplotlib.rcParams["font.family"] = "SimSun"
    if boundary_polygon_file is not None:
        boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=4547)
        ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")
    else:
        fig, ax = plt.subplots()

        # 将 GeoDataFrame 的绘图环境绑定到 ax，但不绘制内容
        gdf.plot(ax=ax, visible=False)
    ax.scatter(gdf.geometry.x, gdf.geometry.y, marker="o", s=30, color="green")

    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X 投影坐标 (米)")
    ax.set_ylabel("Y 投影坐标 (米)")
    # 添加自定义图例
    legend_elements = []
    legend_elements.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color="green",
            label="监测点位",
            markerfacecolor="green",
            markersize=10,
        )
    )
    plt.tight_layout()
    # plt.savefig("./ref/监测点位分布图.png")
