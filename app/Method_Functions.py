import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from app.PredefinedData import MIM_indicators, Drawing_specifications

# matplotlib.use("TkAgg")


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


# * Experience Value Method
# Monitoring_indicators = [
#     "Radon",
#     "VOCs",
#     "CO2",
#     "O2",
#     "CH4",
#     "H2",
#     "H2S",
# ]  # 氡气 VOCs CO2 O2 CH4 H2 H2S
# 评分区间严格升序排列；得分数量=区间分界值数量+1；使用bool控制该分界值在左区间的开闭状态
Radon_score = {
    "breakpoint": [(15, True), (150, True), (1500, True)],
    "score": [11, 3, 1, 0],
}  # unit:Bq/m3
VOCs_score = {
    "breakpoint": [(0.1, False), (1, False), (10, False), (100, False)],
    "score": [0, 1, 2, 6, 22],
}  # unit:ppm
CO2_score = {
    "breakpoint": [(0.01, False), (0.05, False), (0.1, False)],
    "score": [0, 2, 6, 22],
}  # unit:%
O2_score = {
    "breakpoint": [(0.01, True), (0.1, True), (0.19, True)],
    "score": [11, 3, 1, 0],
}  # unit:%
CH4_score = {
    "breakpoint": [(0.0001, False), (0.0025, False), (0.01, False), (0.05, False)],
    "score": [0, 1, 2, 6, 22],
}  # unit:%
H2_score = {
    "breakpoint": [(100, False), (500, False), (1000, False)],
    "score": [0, 1, 3, 11],
}  # unit:ppm
H2S_score = {
    "breakpoint": [(1, False), (5, False), (10, False)],
    "score": [0, 1, 3, 11],
}  # unit:ppm
abnormal_score_config = dict(
    zip(
        [indicator.value.name for indicator in MIM_indicators],
        [
            Radon_score,
            VOCs_score,
            CO2_score,
            O2_score,
            CH4_score,
            H2S_score,
            H2_score,
        ],
    )
)


def calculate_score(
    sample_data: dict, abnormal_score_config: dict = abnormal_score_config
):
    """
    计算采样点总得分并返回详细得分报告

    参数:
    sample_data (dict): 采样点数据，格式{'指标名': 数值}

    返回:
    dict: 包含各指标得分缺失数据为None和总得分的字典
    """
    result = {}
    other_soil_gas = [
        MIM_indicators.VOCs.value.name,
        MIM_indicators.CO2.value.name,
        MIM_indicators.O2.value.name,
        MIM_indicators.CH4.value.name,
        MIM_indicators.H2.value.name,
        MIM_indicators.H2S.value.name,
    ]
    other_soil_gas_scores = 0

    # 遍历所有配置的指标
    for indicator in abnormal_score_config:
        # 处理缺失数据
        if indicator not in sample_data:
            result[f"{indicator}_Score"] = None
            continue

        value = sample_data[indicator]
        config = abnormal_score_config[indicator]
        breakpoints = config["breakpoint"]
        scores = config["score"]

        # 区间判断逻辑
        index = None
        for i, (bp, left_incl) in enumerate(breakpoints):
            if (value < bp) or (value == bp and not left_incl):
                index = i
                break
        else:
            index = len(breakpoints)

        # 记录得分
        score = scores[index]
        result[f"{indicator}_Score"] = score
    # 计算其他土壤气得分
    for indicator in other_soil_gas:
        if result[f"{indicator}_Score"] is not None:
            other_soil_gas_scores += result[f"{indicator}_Score"]
    result["The_other_soil_gas_scores"] = other_soil_gas_scores

    # 计算总体得分;只有其他土壤气得分大于等于≥6的点位才会测量Radon指标，进而计算所有指标得分，进而划分污染源区、疑似污染源区
    if result["The_other_soil_gas_scores"] >= 6 and result["Radon_Score"] is not None:
        result["All_indicators_Scores"] = (
            result["The_other_soil_gas_scores"] + result["Radon_Score"]
        )
    return result


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


def calculate_ExperienceValueMethod_scores(
    gdf, options, boundary_file, abnormal_score_config: dict = abnormal_score_config
):
    new_gdf = point_dataset_preprocess(gdf, options)
    boundary_gdf = boundary_file_preprocess(boundary_file)
    # 确定需要处理的指标列
    indicators = list(abnormal_score_config.keys())
    subset = safe_remove(indicators.copy(), "Radon")
    new_gdf = new_gdf.dropna(subset=subset)
    # * 数据单位转换(针对测试数据)
    new_gdf["VOCs"] = new_gdf["VOCs"].apply(lambda x: x / 1000)
    new_gdf["CO2"] = new_gdf["CO2"].apply(lambda x: x / 1000000)

    # *
    # 定义行处理函数
    def process_row(row):
        # 提取当前行的指标数据
        sample_data = row[indicators].dropna().to_dict()  # 自动处理NaN值
        # 计算得分
        result = calculate_score(sample_data)
        return pd.Series(result)

    # 执行计算并合并结果
    new_gdf = new_gdf.join(new_gdf.apply(process_row, axis=1))
    new_gdf["Contamination_type"] = new_gdf.apply(
        Distinguishing_type_of_contamination, axis=1
    )
    new_gdf["Scope_of_contamination"] = new_gdf.apply(
        Distinguishing_scope_of_contamination, axis=1
    )

    result_dict = {}
    result_dict["gdf"] = new_gdf
    result_dict["outline_dataset"] = boundary_gdf
    fig_dict = experienceValue_anomaly_fig(new_gdf, boundary_gdf)
    result_dict.update(fig_dict)
    return result_dict


def experienceValue_anomaly_fig(
    gdf,
    boundary_gdf,
):
    result_dict = {}
    result_dict["source_fig"] = Plot_source_zone(gdf, boundary_gdf)
    result_dict["scope_fig"] = Plot_scope_of_contamination(gdf, boundary_gdf)
    result_dict["exceed_fig"] = Plot_anomaly_point(
        gdf[gdf["The_other_soil_gas_scores"] >= 6], boundary_gdf
    )
    result_dict["pollution_level_fig"] = Score_interpolation(gdf, boundary_gdf)
    return result_dict


def Distinguishing_scope_of_contamination(row):
    if row["The_other_soil_gas_scores"] >= 1:
        return 1
    else:
        return 0


def Distinguishing_type_of_contamination(row):
    if row["All_indicators_Scores"] >= 17 and row["Radon_Score"] >= 1:
        return "Source_of_contamination"
    elif row["All_indicators_Scores"] >= 6 and row["VOCs_Score"] >= 1:
        return "Suspected_source_of_contamination"
    else:
        return "Scores<6"


def Plot_source_zone(gdf, boundary_gdf):
    import matplotlib
    from matplotlib.lines import Line2D

    fig = Figure(figsize=(10, 8), dpi=90)
    ax = fig.add_subplot(111)
    matplotlib.rcParams["font.family"] = "Times New Roman"
    # 设置颜色映射，按 'Category' 分配颜色
    colors = {
        "Source_of_contamination": "red",
        "Suspected_source_of_contamination": "orange",
        "Scores<6": "green",
    }
    size_map = {"red": 50, "orange": 40, "green": 30}
    gdf_plot = gdf.copy()
    gdf_plot["color"] = gdf_plot["Contamination_type"].map(colors).fillna("gray")
    gdf_plot["size"] = gdf_plot["color"].map(size_map).fillna(0)
    boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="red")
    ax.scatter(
        gdf_plot.geometry.x,
        gdf_plot.geometry.y,
        marker="o",
        s=gdf_plot["size"],
        color=gdf_plot["color"],
    )
    # gdf.plot(ax=ax, color=gdf["color"], markersize=30)
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            # label="Total Scores≥17,Radon Score≥1",
            label="Critical Risk Point",
            markerfacecolor="red",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            # label="Total Scores≥6,VOCs Score≥1",
            label="Significant Risk Point",
            markerfacecolor="orange",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            # label="Total Scores<6",
            label="Marginal Risk Point",
            markerfacecolor="green",
            markersize=10,
        ),
    ]
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.tight_layout()

    # *添加注记(为论文准备)
    # ax.annotate(
    #     "(a)",
    #     xy=(0.03, 0.92),
    #     xycoords="axes fraction",
    #     ha="left",
    #     va="bottom",
    #     fontsize=20,
    #     bbox=dict(
    #         boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0
    #     ),
    # )
    #
    import os

    os.makedirs(os.path.dirname("./auto_report_cache"), exist_ok=True)
    fig.savefig(
        "./auto_report_cache/source_fig.png",
        dpi=900,
        bbox_inches="tight",
        pad_inches=0.1,
    )

    # 关闭图形防止内存泄漏
    plt.close(fig)
    return fig


def Plot_scope_of_contamination(gdf, boundary_gdf):
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig = Figure(figsize=(10, 8), dpi=90)
    ax = fig.add_subplot(111)
    matplotlib.rcParams["font.family"] = "Times New Roman"
    colors = {1: "orange", 0: "green"}
    gdf["color"] = gdf["Scope_of_contamination"].map(colors)
    boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="red")
    ax.scatter(gdf.geometry.x, gdf.geometry.y, marker="^", s=30, color=gdf["color"])
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    # 添加自定义图例
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="^",
            color="w",
            # label="Scores≥1",
            label="Anomaly Point",
            markerfacecolor="orange",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="^",
            color="w",
            # label="Scores<1",
            label="Normal Point",
            markerfacecolor="green",
            markersize=10,
        ),
    ]

    # 添加图例到右下角
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.tight_layout()
    # *添加注记(为论文准备)
    # ax.annotate(
    #     "(b)",
    #     xy=(0.03, 0.92),
    #     xycoords="axes fraction",
    #     ha="left",
    #     va="bottom",
    #     fontsize=20,
    #     bbox=dict(
    #         boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0
    #     ),
    # )
    import os

    os.makedirs(os.path.dirname("./auto_report_cache"), exist_ok=True)
    fig.savefig(
        "./auto_report_cache/scope_fig.png",
        dpi=900,
        bbox_inches="tight",
        pad_inches=0.1,
    )

    # 关闭图形防止内存泄漏
    plt.close(fig)
    return fig


def Plot_anomaly_point(gdf, boundary_gdf):
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig = Figure(figsize=(10, 8), dpi=90)
    ax = fig.add_subplot(111)
    matplotlib.rcParams["font.family"] = "Times New Roman"
    boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="red")
    gdf.plot(
        ax=ax,
        color="orange",
        markersize=30,
    )
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    # 添加自定义图例
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            # label="Scores≥6",
            label="Exceedance point",
            markerfacecolor="orange",
            markersize=10,
        )
    ]

    # 添加图例到右下角
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.tight_layout()
    # 保存图像（DPI=300，防裁剪）
    import os

    os.makedirs(os.path.dirname("./auto_report_cache"), exist_ok=True)
    fig.savefig(
        "./auto_report_cache/exceed_fig.png",
        dpi=900,
        bbox_inches="tight",
        pad_inches=0.1,
    )

    # 关闭图形防止内存泄漏
    plt.close(fig)
    return fig


# 将掩膜后的数据导出为 GeoTIFF 文件
# def export_to_geotiff(filename, data, transform, crs):
#     from rasterio import Affine, MemoryFile
#     from rasterio.enums import Resampling
#     from rasterio.transform import from_origin
#     from rasterio.plot import show
#     from rasterio.io import MemoryFile

#     with MemoryFile() as memfile:
#         with memfile.open(
#             driver="GTiff",
#             height=data.shape[0],
#             width=data.shape[1],
#             count=1,
#             dtype="float32",
#             crs=crs,
#             transform=transform,
#         ) as dataset:
#             dataset.write(data, 1)
#             dataset.flush()
#             # 保存到文件
#             with open(filename, "wb") as f:
#                 f.write(memfile.read())


def mask_with_polygon(grid_x, grid_y, grid_z, polygon):
    from shapely.geometry import Point
    import numpy as np

    # 创建掩膜
    mask = np.zeros_like(grid_z, dtype=bool)
    for i in range(grid_z.shape[0]):
        for j in range(grid_z.shape[1]):
            point = Point(grid_x[i, j], grid_y[i, j])
            if polygon.contains(point):
                mask[i, j] = True

    # 应用掩膜
    masked_grid_z = np.where(mask, grid_z, np.nan)
    return masked_grid_z


import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from shapely.ops import unary_union


def Score_interpolation(gdf, boundary_gdf, method="linear"):
    try:
        # 数据预处理
        gdf.to_csv("gdf.csv")
        boundary = boundary_gdf.copy()
        if gdf.crs != boundary.crs:
            gdf = gdf.to_crs(boundary.crs)

        # 生成插值网格
        min_x, min_y, max_x, max_y = boundary.total_bounds
        grid_x, grid_y = np.mgrid[min_x:max_x:300j, min_y:max_y:300j]
        points = np.column_stack((gdf.geometry.x, gdf.geometry.y))
        values = gdf["All_indicators_Scores"].fillna(gdf["The_other_soil_gas_scores"])
        grid_z = griddata(points, values, (grid_x, grid_y), method=method)

        # 应用掩膜
        masked_z = mask_with_polygon(
            grid_x, grid_y, grid_z, unary_union(boundary.geometry)
        )

        # 可视化
        fig, ax = plt.subplots(figsize=(10, 8), dpi=90)
        im = ax.imshow(
            masked_z.T,
            extent=(min_x, max_x, min_y, max_y),
            origin="lower",
            cmap="viridis",
            interpolation="none",
        )
        add_north_arrow(ax)
        add_scalebar(ax, location="lower left")
        ax.scatter(points[:, 0], points[:, 1], c="red", s=4, label="Data Points")

        # 颜色条优化
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Contamination risk", rotation=270, labelpad=20)
        cbar.ax.text(
            0.5, 1.02, "High", ha="center", va="bottom", transform=cbar.ax.transAxes
        )
        cbar.ax.text(
            0.5, -0.02, "Low", ha="center", va="top", transform=cbar.ax.transAxes
        )

        # 边界绘制（使用geopandas高效渲染）
        boundary.boundary.plot(ax=ax, color="red", lw=1, label="Boundary")
        ax.legend()
        return fig
    except Exception as e:
        raise RuntimeError(f"Processing failed: {str(e)}")


# def 污染等级识别(gdf, boundary_polygon_file):
#     import numpy as np
#     import geopandas as gpd
#     import matplotlib.pyplot as plt
#     from scipy.interpolate import griddata
#     from shapely.ops import unary_union
#     from rasterio.transform import from_origin

#     fig = Figure(figsize=(10, 8), dpi=90)
#     ax = fig.add_subplot(111)
#     boundary_polygon = gpd.read_file(boundary_polygon_file).to_crs(
#         epsg=Drawing_specifications.EPSG_code
#     )
#     # 提取坐标
#     points = np.array([[p.x, p.y] for p in gdf.geometry])

#     # 根据是否存在总体得分属性，决定使用 total_score 还是 score
#     values = np.where(
#         gdf["All_indicators_Scores"].notna(),
#         gdf["All_indicators_Scores"],
#         gdf["The_other_soil_gas_scores"],
#     )
#     min_x, min_y, max_x, max_y = boundary_polygon.total_bounds
#     # 生成插值网格（100x100）
#     grid_x, grid_y = np.mgrid[min_x:max_x:300j, min_y:max_y:300j]
#     grid_z = griddata(points, values, (grid_x, grid_y), method="linear")

#     # 获取边界多边形（假设为单个多边形）
#     boundary_poly = unary_union(boundary_polygon.geometry)

#     # 应用掩膜
#     masked_grid_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_poly)

#     # 计算地理坐标系转换
#     transform = from_origin(
#         min_x,
#         max_y,
#         (max_x - min_x) / grid_x.shape[0],
#         (max_y - min_y) / grid_y.shape[1],
#     )

#     # 可视化掩膜后的插值结果
#     import matplotlib

#     matplotlib.rcParams["font.family"] = "Times New Roman"
#     im = ax.imshow(
#         masked_grid_z.T,
#         extent=(
#             min_x,
#             max_x,
#             min_y,
#             max_y,
#         ),
#         origin="lower",
#         cmap="viridis",
#         interpolation="none",
#     )
#     add_north_arrow(ax)
#     add_scalebar(ax, location="lower left")
#     ax.set_xlabel("X")
#     ax.set_ylabel("Y")
#     ax.scatter(points[:, 0], points[:, 1], c="red", label="Data Points", s=4)
#     cbar = plt.colorbar(im, ax=ax)
#     cbar.set_label("Contamination risk", rotation=270, labelpad=20)
#     # 在colorbar顶部添加文字说明
#     cbar.ax.text(
#         1.4, 0.95, "High", ha="right", va="bottom", transform=cbar.ax.transAxes
#     )

#     # 在colorbar底部添加文字说明
#     cbar.ax.text(1.4, 0.05, "Low", ha="right", va="top", transform=cbar.ax.transAxes)

#     boundary_coords = np.array(boundary_poly.exterior.coords)
#     ax.plot(boundary_coords[:, 0], boundary_coords[:, 1], "r-", lw=1, label="Boundary")
#     return fig


# * Background Value Method #######################
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

    for col in [indicator for indicator in MIM_indicators]:
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


#! 原始代码
# 根据标签划分数据
# labels = kmeans.labels_
# lower_part = data[labels == np.argmin(centers)].flatten()
# upper_part = data[labels == np.argmax(centers)].flatten()

# 统计数据点的出现次数
# data_counts = Counter(data.flatten())
# 设置全局字体
# plt.rcParams["font.family"] = "Times New Roman"  # 仿宋
# plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号
# # 绘制结果图像
# plt.figure(figsize=(8, 6), dpi=90)

# for point, count in data_counts.items():
#     # 分别绘制 lower_part 和 upper_part 的数据点
#     if point in lower_part:
#         plt.scatter(
#             point,
#             0,
#             color="blue",
#             s=50,
#             label="Part Ⅰ" if point == lower_part[0] else "",
#         )
#     if point in upper_part:
#         plt.scatter(
#             point,
#             0,
#             color="orange",
#             s=50,
#             label="Part Ⅱ" if point == upper_part[0] else "",
#         )

#     # 如果数据点重复，标注数量
#     if count > 1:
#         plt.text(
#             point,
#             0.005,
#             f"{count}",
#             ha="center",
#             color="black",
#             fontsize=10,
#             va="top",
#         )


# # 标注簇中心
# plt.scatter(
#     centers, [0, 0], color="red", s=100, marker="x", label="Cluster center"
# )
# # 标注分界线
# plt.axvline(boundary, color="green", linestyle="--", label="Cut-off value")
# plt.text(
#     boundary, -0.05, f"{boundary:.2f}", ha="right", color="green", fontsize=20
# )
# # 添加图例和标签
# plt.legend(fontsize=10, ncol=2)
# plt.xticks(fontsize=15)
# plt.yticks([])
# plt.xlabel(f"{value}({unit})", fontsize=15)
# if save:
#     plt.savefig(f"./ref/KMEANS-{value}.png")
#     return
# else:
#     plt.show()
def calculate_backgroundValue(data, boundarys):
    new_data = data.copy()
    gdf = new_data.get("gdf")
    result_gdf = anomaly_identification(gdf, boundarys)
    anomaly_figs = []
    # header = [
    #     "Point ID",
    #     "Abnormally Low Radon",
    #     "Abnormally High VOCs",
    #     "Abnormally High CO2",
    #     "Abnormally Low O2",
    #     "Abnormally High CH4",
    #     "Abnormally High Functional Genes",
    # ]
    headers = [
        ("Abnormally Low Radon", MIM_indicators.Radon),
        ("Abnormally High VOCs", MIM_indicators.VOCs),
        ("Abnormally High CO2", MIM_indicators.CO2),
        ("Abnormally Low O2", MIM_indicators.O2),
        ("Abnormally High CH4", MIM_indicators.CH4),
        ("Abnormally High Functional Genes", MIM_indicators.FG),
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
    # result_gdf["点位"] = result_gdf["Point_ID"]
    result_gdf["Point ID"] = result_gdf["Point_ID"]
    new_data["gdf"] = result_gdf
    new_data["anomaly_figs"] = anomaly_figs
    return new_data
    # pass


def anomaly_identification(gdf, boundarys):

    # gdf["氡气异常低"] =
    gdf["Abnormally Low Radon"] = gdf[MIM_indicators.Radon.value.name].apply(
        lambda x: (
            "×"
            if x is not None
            and x > boundarys.get(MIM_indicators.Radon)  # 大于阈值时赋值为 1
            else (
                "√"
                if x is not None
                and x <= boundarys.get(MIM_indicators.Radon)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    # gdf["VOCs异常高"]
    gdf["Abnormally High VOCs"] = gdf[MIM_indicators.VOCs.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x > boundarys.get(MIM_indicators.VOCs)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x <= boundarys.get(MIM_indicators.VOCs)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    # gdf["O2异常低"]
    gdf["Abnormally Low O2"] = gdf[MIM_indicators.O2.value.name].apply(
        lambda x: (
            "×"
            if x is not None
            and x > boundarys.get(MIM_indicators.O2)  # 大于阈值时赋值为 1
            else (
                "√"
                if x is not None
                and x <= boundarys.get(MIM_indicators.O2)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    # gdf["CO2异常高"]
    gdf["Abnormally High CO2"] = gdf[MIM_indicators.CO2.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x >= boundarys.get(MIM_indicators.CO2)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x < boundarys.get(MIM_indicators.CO2)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    # gdf["CH4异常高"]
    gdf["Abnormally High CH4"] = gdf[MIM_indicators.CH4.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x >= boundarys.get(MIM_indicators.CH4)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x < boundarys.get(MIM_indicators.CH4)  # 小于或等于阈值时赋值为 0
                else "⚪"
            )
        )
    )
    # gdf["功能基因异常高"]
    gdf["Abnormally High Functional Genes"] = gdf[MIM_indicators.FG.value.name].apply(
        lambda x: (
            "√"
            if x is not None
            and x >= boundarys.get(MIM_indicators.FG)  # 大于阈值时赋值为 1
            else (
                "×"
                if x is not None
                and x < boundarys.get(MIM_indicators.FG)  # 小于或等于阈值时赋值为 0
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
    #
    # fig.savefig(
    #     Path("./auto_report_cache") / f"{label}.png",
    #     dpi=300,
    #     bbox_inches="tight",
    #     pad_inches=0.1,
    # )
    #
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
    plt.savefig("./ref/监测点位分布图.png")


# * PCA Method  ####################################

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def return_PCA_results(point_dataset, options, outline_dataset):
    gdf = point_dataset_preprocess(point_dataset=point_dataset, options=options)
    boundary_gdf = boundary_file_preprocess(outline_dataset)
    pca_results, pca_loadings, pca_var_ratio, pca_gdf = process_PCA(
        gdf=gdf, options=options
    )
    PC1_score_fig = plot_PC1_score(pca_gdf, boundary_gdf, column="PC1")
    PCA_variance_contribution_fig = plot_PCA_variance_contribution(pca_var_ratio)
    PCA_loading_plot_fig = plot_PCA_loading_plot(pca_loadings, pca_var_ratio)
    PCA_Biplot_fig = plot_PCA_Biplot(pca_results, pca_loadings, pca_var_ratio)
    PC1_interpolation_figs = {}
    interpolation_methods = ["Nearest", "Cubic", "IDW", "Kriging"]
    for interpolation_method in interpolation_methods:
        fig = plot_PC1_interpolation(
            boundary_gdf=boundary_gdf,
            points_gdf=pca_gdf,
            interpolation_method=interpolation_method,
        )
        PC1_interpolation_figs[interpolation_method] = fig
    return {
        "gdf": pca_gdf,
        "boundary_gdf": boundary_gdf,
        "PC1_score_fig": PC1_score_fig,
        "PCA_variance_contribution_fig": PCA_variance_contribution_fig,
        "PCA_loading_plot_fig": PCA_loading_plot_fig,
        "PCA_Biplot_fig": PCA_Biplot_fig,
        "PC1_interpolation_figs": PC1_interpolation_figs,
    }


def process_PCA(gdf, options):
    pca_columns = []
    for key, value in options.items():
        if value != None and type(value) == str and key != "Point_ID":
            pca_columns.append(value)
    print("columns for PCA:{pca_columns}")
    data_pca_analysis = gdf[pca_columns].dropna()
    scaler_pca = StandardScaler()
    data_pca_scaled = scaler_pca.fit_transform(data_pca_analysis)
    pca_analysis = PCA(n_components=3)
    pca_results = pca_analysis.fit_transform(data_pca_scaled)
    # 计算 PCA 载荷矩阵
    pca_loadings = pd.DataFrame(
        pca_analysis.components_.T, columns=["PC1", "PC2", "PC3"], index=pca_columns
    )
    # 计算 PCA 方差贡献率
    pca_var_ratio = pca_analysis.explained_variance_ratio_
    pca_scores = pd.DataFrame(pca_results, columns=["PC1", "PC2", "PC3"])
    pca_data = data_pca_analysis.reset_index(drop=True)

    # 合并原始数据与主成分得分
    complete_pca_df = pd.concat([pca_data, pca_scores], axis=1)

    # 添加ID和几何信息
    if options.get("Point_ID") is not None:
        complete_pca_df["ID"] = gdf.loc[
            data_pca_analysis.index, options.get("Point_ID")
        ].values
    complete_pca_df["geometry"] = gdf.loc[data_pca_analysis.index, "geometry"].values
    pca_gdf = gpd.GeoDataFrame(complete_pca_df, geometry="geometry")
    print("pca_gdf:", pca_gdf.head())
    return pca_results, pca_loadings, pca_var_ratio, pca_gdf


def plot_PCA_variance_contribution(pca_var_ratioa):
    # 绘制 PCA 方差贡献率图
    fig = plt.figure(figsize=(6, 4))
    plt.bar(range(1, 4), pca_var_ratioa * 100, tick_label=["PC1", "PC2", "PC3"])
    plt.ylabel("Variance contribution rate(%)", fontsize=10)
    plt.xlabel("Principal component", fontsize=10)
    plt.title("PCA Variance Contribution", fontsize=10)
    # plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    return fig


def plot_PCA_loading_plot(pca_loadings, pca_var_ratio):
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = sns.color_palette("hls", n_colors=len(pca_loadings.index))
    for i, variable in enumerate(pca_loadings.index):
        x = pca_loadings.loc[variable, "PC1"]
        y = pca_loadings.loc[variable, "PC2"]

        # 绘制箭头
        ax.arrow(
            0,
            0,
            x,
            y,
            color=colors[i],
            alpha=0.8,
            linewidth=2,
            head_width=0.02,  # 箭头头部宽度
            head_length=0.03,  # 箭头头部长度
            length_includes_head=True,
        )

        # 在箭头末端附近添加文字标签
        ax.text(
            x * 0.9,
            y * 0.9,  # 乘以 1.1 让文字稍微远离箭头
            variable,
            color="black",
            fontsize=8,
            # fontweight="bold",
            ha="center",
            va="center",
        )

    # 设置坐标轴标签，显示各主成分解释的方差百分比
    ax.set_xlabel(f"PC1 ({pca_var_ratio[0]*100:.2f}%)", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca_var_ratio[1]*100:.2f}%)", fontsize=10)

    # 设置标题
    ax.set_title(
        "PCA Loading Plot",
        fontsize=10,
    )

    # 在 x=0 和 y=0 处添加参考线（虚线）
    ax.axhline(0, color="gray", linewidth=1, linestyle="--")
    ax.axvline(0, color="gray", linewidth=1, linestyle="--")

    # 去除右侧与上侧边框，让图更简洁
    # sns.despine()

    # 调整边距，防止文字被裁剪
    plt.tight_layout()
    return fig


def plot_PCA_Biplot(pca_results, pca_loadings, pca_var_ratio, dpi=100):
    pca_scores = pd.DataFrame(pca_results, columns=["PC1", "PC2", "PC3"])
    # sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(6, 4), dpi=dpi)
    ax.scatter(
        pca_scores["PC1"],
        pca_scores["PC2"],
        s=10,  # 点的大小
        alpha=0.7,  # 透明度
        color="gray",  # 颜色
        label="Samples",  # 用于图例
    )
    # 绘制载荷向量（变量箭头）
    arrow_scale = 10  # 缩放系数，可根据实际数据分布进行调整

    colors = sns.color_palette("hls", n_colors=len(pca_loadings.index))

    for i, variable in enumerate(pca_loadings.index):
        # 缩放后的坐标
        x = pca_loadings.loc[variable, "PC1"] * arrow_scale
        y = pca_loadings.loc[variable, "PC2"] * arrow_scale

        # 绘制箭头
        ax.arrow(
            0,
            0,
            x,
            y,
            color=colors[i],
            alpha=0.8,
            linewidth=2,
            head_width=0.2,  # 箭头头部宽度
            head_length=0.3,  # 箭头头部长度
            length_includes_head=True,
        )

        # 在箭头末端附近添加文字标签
        # ax.text(
        #     x * 1.1,
        #     y * 1.1,
        #     variable,
        #     color=colors[i],
        #     fontsize=12,
        #     # fontweight="bold",
        #     ha="center",
        #     va="center",
        # )

    # 5. 设置坐标轴标签与标题
    ax.set_xlabel(f"PC1 ({pca_var_ratio[0]*100:.2f}%)", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca_var_ratio[1]*100:.2f}%)", fontsize=10)
    ax.set_title("PCA Biplot", fontsize=10)

    # 6. 添加参考线与美化
    ax.axhline(0, color="gray", linewidth=1, linestyle="--")
    ax.axvline(0, color="gray", linewidth=1, linestyle="--")

    # 去除右侧与上侧边框，让图更简洁
    # sns.despine()

    # 7. 显示图例并调整布局
    ax.legend()
    plt.tight_layout()
    return fig


import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from pykrige.ok import OrdinaryKriging
import scipy.interpolate as spi


# 定义克里金插值函数
def kriging_interpolation(
    x,
    y,
    z,
    grid_x,
    grid_y,
    variogram_model="spherical",
    variogram_parameters=None,
    nlag=6,
    weight=False,
):
    """
    使用 Ordinary Kriging 进行插值
    :param x: 数据点的X坐标
    :param y: 数据点的Y坐标
    :param z: 数据点的值（对应的Z值）
    :param grid_x: 插值网格的X坐标
    :param grid_y: 插值网格的Y坐标
    :param variogram_model: 变异函数模型，默认为 "spherical"
    :param variogram_parameters: 变异函数的参数，依据所选模型不同
    :param nlag: 半变异函数的平均区间数，默认为6
    :param weight: 是否加权处理小的滞后距离，默认为False
    :return: 插值后的结果
    """
    # return np.zeros(grid_x.shape)  # 返回全零结果
    OK = OrdinaryKriging(
        x,
        y,
        z,
        variogram_model=variogram_model,
        variogram_parameters=variogram_parameters,
        nlags=nlag,
        weight=weight,
        verbose=False,
        enable_plotting=False,
    )

    # 执行插值，grid_x 和 grid_y 需要传入二维网格
    grid_z_kriging, ss = OK.execute("grid", grid_x, grid_y)

    return grid_z_kriging  # 返回插值结果


# 定义基于 scipy 的插值函数
def scipy_interpolation(x, y, z, grid_x, grid_y, method="nearest"):
    """
    使用 scipy 进行插值（最近邻、立方插值）
    :param x: 数据点的X坐标
    :param y: 数据点的Y坐标
    :param z: 数据点的值（对应的Z值）
    :param grid_x: 插值网格的X坐标
    :param grid_y: 插值网格的Y坐标
    :param method: 插值方法，默认为 'nearest'
    :return: 插值后的结果
    """
    return spi.griddata((x, y), z, (grid_x, grid_y), method=method)


# 定义IDW插值函数（反距离加权）
def idw_interpolation(x, y, z, grid_x, grid_y, power=2):
    """
    使用反距离加权（IDW）进行插值
    :param x: 数据点的X坐标
    :param y: 数据点的Y坐标
    :param z: 数据点的值（对应的Z值）
    :param grid_x: 插值网格的X坐标
    :param grid_y: 插值网格的Y坐标
    :param power: 权重幂次，默认为2
    :return: 插值后的结果
    """
    grid_z = np.zeros(grid_x.shape)

    for i in range(grid_x.shape[0]):
        for j in range(grid_x.shape[1]):
            dist = np.sqrt((x - grid_x[i, j]) ** 2 + (y - grid_y[i, j]) ** 2)
            dist[dist == 0] = 1e-10  # 防止出现零距离
            weights = 1 / dist**power  # 计算距离权重
            grid_z[i, j] = np.sum(weights * z) / np.sum(weights)  # 加权平均

    return grid_z


def add_common_elements(ax, boundary_gdf, points_gdf):
    boundary_gdf.plot(
        ax=ax, color="none", edgecolor="black", linewidth=2, label="Boundary"
    )
    ax.scatter(
        points_gdf.geometry.x,
        points_gdf.geometry.y,
        c="black",
        marker=".",
        s=2,
        label="Monitoring Points",
    )
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(fontsize=10)


def plot_PC1_score(
    gdf: gpd.GeoDataFrame,
    boundary_gdf: gpd.GeoDataFrame,
    column: str,
    cmap="viridis",
    figsize=(8, 6),
    dpi=150,
    fontsize=12,
    labelpad=15,
) -> Figure:
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    import numpy as np

    # 设置全局样式
    mpl.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": fontsize,
            "axes.linewidth": 0.8,
            "axes.labelweight": "bold",
            "savefig.dpi": dpi,
            "figure.facecolor": "white",
        }
    )
    values = gdf[column].values
    # 创建画布
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)

    # 绘制点图
    norm = mpl.colors.Normalize(vmin=np.nanmin(values), vmax=np.nanmax(values))
    default_style = {"marker": "o", "edgecolor": "black", "linewidth": 0.5}

    gdf.plot(
        ax=ax,
        column=column,
        cmap=cmap,
        markersize=20,
        norm=norm,
        legend=True,
        cax=cax,
        legend_kwds={"label": f"{column}", "orientation": "vertical"},
        **default_style,  # 默认样式
    )

    # 绘制边界
    boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.2)
    # 坐标轴美化
    ax.tick_params(axis="both", which="major", labelsize=fontsize - 2, direction="in")
    ax.set_xlabel("X", labelpad=labelpad)
    ax.set_ylabel("Y", labelpad=labelpad)
    return fig


def plot_PC1_interpolation(
    boundary_gdf,
    points_gdf,
    interpolation_method,
) -> Figure:
    # 提取插值点坐标
    x = points_gdf.geometry.x
    y = points_gdf.geometry.y
    z = points_gdf["PC1"].values
    # "gist_rainbow"
    # 创建网格
    grid_x, grid_y = np.mgrid[
        min(x) - 0.001 : max(x) + 0.001 : 100j, min(y) - 0.001 : max(y) + 0.001 : 100j
    ]

    # 合并边界多边形
    boundary_polygon = unary_union(boundary_gdf.geometry)

    # 创建图形
    fig = Figure(figsize=(8, 6), dpi=150)
    ax = fig.add_subplot(111)

    if interpolation_method == "Nearest":
        from scipy.interpolate import griddata

        grid_z = griddata((x, y), z, (grid_x, grid_y), method="nearest")
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)

        contour = ax.contourf(grid_x, grid_y, masked_z, cmap="jet", levels=10)
        fig.colorbar(contour, ax=ax, label="PC1(Nearest)")
        # ax.set_title("Nearest Neighbor Interpolation")

    elif interpolation_method == "Cubic":
        from scipy.interpolate import griddata

        grid_z = griddata((x, y), z, (grid_x, grid_y), method="cubic")
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)

        contour = ax.contourf(grid_x, grid_y, masked_z, cmap="jet", levels=10)
        fig.colorbar(contour, ax=ax, label="PC1(Cubic)")
        # ax.set_title("Cubic Interpolation")

    elif interpolation_method == "IDW":
        grid_z = idw_interpolation(x, y, z, grid_x, grid_y, power=2)
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)

        contour = ax.contourf(grid_x, grid_y, masked_z, cmap="jet", levels=10)
        fig.colorbar(contour, ax=ax, label="PC1(IDW)")
        # ax.set_title("Inverse Distance Weighting Interpolation")

    elif interpolation_method == "Kriging":
        # grid_z = kriging_interpolation(x, y, z, grid_x, grid_y)
        grid_z = kriging_interpolation(
            x,
            y,
            z,
            np.linspace(min(x) - 0.001, max(x) + 0.001, 100),
            np.linspace(min(y) - 0.001, max(y) + 0.001, 100),
        )
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)

        contour = ax.contourf(grid_x, grid_y, masked_z, cmap="jet", levels=10)
        fig.colorbar(contour, ax=ax, label="PC1(Kriging)")
        # ax.set_title("Kriging Interpolation")

    # 添加公共元素
    add_common_elements(ax, boundary_gdf, points_gdf)
    fig.savefig(
        f"./auto_report_cache/{interpolation_method}.png",
        dpi=900,
        bbox_inches="tight",
        pad_inches=0.1,
    )

    return fig


if __name__ == "__main__":
    # for key in abnormal_score_config.keys():
    #     print(key)
    #     print(abnormal_score_config.get(key))
    #     print("")
    pass
