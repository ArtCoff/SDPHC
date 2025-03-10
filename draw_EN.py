import pandas as pd
from PredefinedData import EPSG_code

Monitoring_indicators = [
    "Radon",
    "VOCs",
    "CO2",
    "O2",
    "CH4",
    "H2",
    "H2S",
]  # 氡气 VOCs CO2 O2 CH4 H2 H2S
Less_indicators = [
    "VOCs",
    "CO2",
    "O2",
    "CH4",
    "H2",
    "H2S",
]  #  VOCs CO2 O2 CH4 H2 H2S

abnormal_indicators_values = {
    "A": [15, 100, 0.1, 0.01, 0.05, 1000, 10],
    "B": [150, 10, 0.05, 0.1, 0.01, 500, 5],
    "C": [1500, 1, 0.01, 0.19, 0.0025, 100, 1],
    "D": [3000, 0.1, 0.001, 0.2, 0.0001, 10, 0.1],
}  # 极度异常	高度异常	异常	轻微异常

abnormal_score = {
    "A": [11, 22, 22, 11, 22, 11, 11],
    "B": [3, 6, 6, 3, 6, 3, 3],
    "C": [1, 2, 2, 1, 2, 1, 1],
    "D": [0, 1, 0, 0, 1, 0, 0],
}  # 极度异常	高度异常	异常	轻微异常
Anomaly_value_Scale = pd.DataFrame(
    data=abnormal_indicators_values, index=Monitoring_indicators
)
Anomaly_Rating_Scale = pd.DataFrame(data=abnormal_score, index=Monitoring_indicators)


# 添加指北针 (North Arrow)
def add_north_arrow(ax, x=0.1, y=0.9, size=20):
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - 0.1),
        arrowprops=dict(facecolor="black", width=3, headwidth=15),
        ha="center",
        va="center",
        fontsize=size,
        xycoords="axes fraction",
    )


# def add_north_arrow(ax):
#     """Add a north arrow to the plot."""
#     x, y, arrow_length = 0.95, 0.95, 0.1
#     ax.annotate(
#         "N",
#         xy=(x, y),
#         xytext=(x, y - arrow_length),
#         arrowprops=dict(arrowstyle="->"),
#         ha="center",
#         va="center",
#         fontsize=12,
#         xycoords=ax.transAxes,
#     )


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


def plot_basic_info(point_dataset, outline_dataset, epsg_code=EPSG_code):
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    import matplotlib

    # print(outline_polygon_shp)
    if outline_dataset == "" or point_dataset == "":
        return

    matplotlib.rcParams["font.family"] = "Times New Roman"
    point_dataset_gdf = gpd.read_file(point_dataset).to_crs(epsg=epsg_code)
    boundary_polygon_gdf = gpd.read_file(outline_dataset).to_crs(epsg=epsg_code)
    ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")
    point_dataset_gdf.plot(
        ax=ax, color="blue", markersize=10, label="Monitoring Points"
    )
    add_north_arrow(ax)
    add_scalebar(ax)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()
    ax.autoscale()
    plt.subplots_adjust(bottom=0.2)
    plt.show()


def get_gdf_options(datapoints_shp):
    import geopandas as gpd

    gdf = gpd.read_file(datapoints_shp, chunksize=1)
    options = gdf.columns.tolist()
    return options


def calculate_single_indicator_score(value, indicator):
    score = 0
    if indicator in ["VOCs", "CO2", "CH4", "H2", "H2S"]:  # 高值异常
        if value >= Anomaly_value_Scale.loc[indicator, "A"]:
            score = Anomaly_Rating_Scale.loc[indicator, "A"]
        elif value >= Anomaly_value_Scale.loc[indicator, "B"]:
            score = Anomaly_Rating_Scale.loc[indicator, "B"]
        elif value >= Anomaly_value_Scale.loc[indicator, "C"]:
            score = Anomaly_Rating_Scale.loc[indicator, "C"]
        elif value >= Anomaly_value_Scale.loc[indicator, "D"]:
            score = Anomaly_Rating_Scale.loc[indicator, "D"]
    elif indicator in ["O2", "Radon"]:  # 低值异常
        if value <= Anomaly_value_Scale.loc[indicator, "A"]:
            score = Anomaly_Rating_Scale.loc[indicator, "A"]
        elif value <= Anomaly_value_Scale.loc[indicator, "B"]:
            score = Anomaly_Rating_Scale.loc[indicator, "B"]
        elif value <= Anomaly_value_Scale.loc[indicator, "C"]:
            score = Anomaly_Rating_Scale.loc[indicator, "C"]
        elif value <= Anomaly_value_Scale.loc[indicator, "D"]:
            score = Anomaly_Rating_Scale.loc[indicator, "D"]
    return score


def point_dataset_preprocess(point_dataset, options):
    import geopandas as gpd

    # 字段-索引映射配置表（可扩展）
    FIELD_MAPPING = [
        ("Point_Code", 0, ["点位"]),  # (目标字段, 默认索引, 兼容别名)
        ("Radon", 1, ["氡"]),
        ("VOCs", 2, ["挥发性有机物"]),
        ("CO2", 3, ["二氧化碳"]),
        ("O2", 4, ["氧气"]),
        ("CH4", 5, ["甲烷"]),
        ("H2", 6, ["氢气"]),
        ("H2S", 7, ["硫化氢"]),
        ("Functional_genes", 8, ["功能基因"]),
    ]

    # 读取数据并转换坐标系
    gdf = gpd.read_file(point_dataset).to_crs(epsg=EPSG_code)

    # 构建无效索引集（空值或'无数据'）
    invalid_indices = {i for i, v in enumerate(options) if v in ("", "No_data")}

    for target_field, default_idx, aliases in FIELD_MAPPING:
        # 动态查找有效列索引
        found_idx = None
        valid_options = [opt for opt in options if opt and opt != "No_data"]

        # 优先匹配别名
        for alias in aliases:
            if alias in valid_options:
                found_idx = options.index(alias)
                break

        # 未找到别名时回退默认索引
        idx = found_idx if found_idx is not None else default_idx

        # 索引有效性验证
        if idx >= len(options) or idx in invalid_indices:
            gdf[target_field] = None
        else:
            src_column = options[idx]
            # 带容错的数据赋值
            gdf[target_field] = gdf[src_column] if src_column in gdf.columns else None
    print("preprocess done")
    return gdf


def 计算单个指标得分(gdf):
    for indicator in Less_indicators:
        score_column_name = f"{indicator}_Score"
        gdf[score_column_name] = gdf[indicator].apply(
            lambda x: calculate_single_indicator_score(x, indicator)
        )
    return gdf


def 计算其他土壤气得分(row):
    Score_without_Radon = 0
    for indicator_score in [f"{indicator}_Score" for indicator in Less_indicators]:
        Score_without_Radon += row[indicator_score]
    return Score_without_Radon


def 指示污染超标范围点位(gdf):
    gdf = 计算单个指标得分(gdf)
    gdf["The_other_soil_gas_scores"] = gdf.apply(计算其他土壤气得分, axis=1)
    return gdf


# 只有其他土壤气得分大于等于≥6的点位才会测量Radon指标，进而计算所有指标得分，进而划分污染源区、疑似污染源区
def 计算所有指标得分(row):
    Score = 0
    Score += row["The_other_soil_gas_scores"]
    if row["The_other_soil_gas_scores"] >= 6:
        Score += row["Radon_Score"]
    return Score


def 计算总体得分(gdf):
    gdf = 指示污染超标范围点位(gdf)  # 计算其他土壤气得分
    # gdf = gdf[gdf["The_Other_soil_gas_scores"] >= 6]  # 筛选出大于等于6的点位
    gdf["Radon_Score"] = gdf["Radon"].apply(
        lambda x: calculate_single_indicator_score(x, "Radon")
    )  # 计算氡气赋分
    gdf["All_indicators_Scores"] = gdf.apply(计算所有指标得分, axis=1)
    gdf["Contamination_type"] = gdf.apply(计算单个污染类型, axis=1)
    return gdf


def 计算单个污染类型(row):
    if row["All_indicators_Scores"] >= 17 and row["Radon_Score"] >= 1:
        return "Source_of_contamination"
    elif row["All_indicators_Scores"] >= 6 and row["VOCs_Score"] >= 1:
        return "Suspected_source_of_contamination"
    else:
        return "Scores＜6"


# 读取gpkg或者shp文件的列名
def read_file_columns(file_path):
    import geopandas as gpd

    gdf = gpd.read_file(file_path)
    return gdf.columns.tolist()


def 绘制污染源区图(gdf, boundary_polygon_file):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.rcParams["font.family"] = "SimSun"
    # 设置颜色映射，按 'Category' 分配颜色
    colors = {
        "Source_of_contamination": "red",
        "Suspected_source_of_contamination": "yellow",
        "Scores＜6": "green",
    }
    gdf["color"] = gdf["Contamination_type"].map(colors)
    if boundary_polygon_file != "":
        boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(
            epsg=EPSG_code
        )
        ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")

    gdf.plot(ax=ax, color=gdf["color"], markersize=30)
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect("auto")
    # 创建自定义图例并设置其位置为右下角
    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Total Scores≥17,Radon Score≥1",
            markerfacecolor="red",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Total Scores≥6,VOCs Score≥1",
            markerfacecolor="yellow",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Total Scores<6",
            markerfacecolor="green",
            markersize=10,
        ),
    ]
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.show()


def 判断污染范围(row):
    if row["The_other_soil_gas_scores"] >= 1:
        return 1
    else:
        return 0


def 计算污染范围(file_path, options):
    gdf = point_dataset_preprocess(file_path, options)
    gdf = 指示污染超标范围点位(gdf)
    gdf = 计算总体得分(gdf)
    gdf["Scope_of_contamination"] = gdf.apply(判断污染范围, axis=1)
    return gdf


def 绘制污染范围(gdf, boundary_polygon_file, epsg_code=EPSG_code):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    from matplotlib.lines import Line2D

    matplotlib.rcParams["font.family"] = "Times New Roman"
    boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=EPSG_code)
    colors = {1: "orange", 0: "green"}
    gdf["color"] = gdf["Scope_of_contamination"].map(colors)
    ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")
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
            label="Scores≥1",
            markerfacecolor="orange",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="^",
            color="w",
            label="Scores<1",
            markerfacecolor="green",
            markersize=10,
        ),
    ]

    # 添加图例到右下角
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.tight_layout()
    plt.show()


def 绘制超标点位(gdf, boundary_polygon_file, epsg_code=EPSG_code):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    matplotlib.rcParams["font.family"] = "Times New Roman"
    boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=EPSG_code)
    ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")
    gdf.plot(
        ax=ax,
        color="red",
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
            label="Scores≥6",
            markerfacecolor="red",
            markersize=10,
        )
    ]

    # 添加图例到右下角
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.tight_layout()
    plt.show()


# 将掩膜后的数据导出为 GeoTIFF 文件
def export_to_geotiff(filename, data, transform, crs):
    from rasterio import Affine, MemoryFile
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.plot import show
    from rasterio.io import MemoryFile

    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
        ) as dataset:
            dataset.write(data, 1)
            dataset.flush()
            # 保存到文件
            with open(filename, "wb") as f:
                f.write(memfile.read())


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


def 污染等级识别(gdf, boundary_polygon_file):
    import numpy as np
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from scipy.interpolate import griddata
    from shapely.ops import unary_union
    from rasterio import Affine, MemoryFile
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.plot import show
    from rasterio.io import MemoryFile

    boundary_polygon = gpd.read_file(boundary_polygon_file).to_crs(epsg=EPSG_code)
    # 提取坐标
    points = np.array([[p.x, p.y] for p in gdf.geometry])

    # 根据是否存在总体得分属性，决定使用 total_score 还是 score
    values = np.where(
        gdf["Score for all indicators"].notna(),
        gdf["Score for all indicators"],
        gdf["The_Other_soil_gas_scores"],
    )
    min_x, min_y, max_x, max_y = boundary_polygon.total_bounds
    # 生成插值网格（100x100）
    grid_x, grid_y = np.mgrid[min_x:max_x:300j, min_y:max_y:300j]
    # 使用反距离权重法 (IDW) 进行插值
    grid_z = griddata(points, values, (grid_x, grid_y), method="linear")

    # 获取边界多边形（假设为单个多边形）
    boundary_poly = unary_union(boundary_polygon.geometry)

    # 应用掩膜
    masked_grid_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_poly)

    # 计算地理坐标系转换
    transform = from_origin(
        min_x,
        max_y,
        (max_x - min_x) / grid_x.shape[0],
        (max_y - min_y) / grid_y.shape[1],
    )

    # 可视化掩膜后的插值结果
    import matplotlib

    matplotlib.rcParams["font.family"] = "Times New Roman"
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(
        masked_grid_z.T,
        extent=(
            min_x,
            max_x,
            min_y,
            max_y,
        ),
        origin="lower",
        cmap="viridis",
        interpolation="none",
    )
    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    # plt.scatter(points[:, 0], points[:, 1], c="red", label="Data Points")
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Contamination risk", rotation=270, labelpad=20)
    # 在colorbar顶部添加文字说明
    cbar.ax.text(
        1.4, 0.95, "High", ha="center", va="bottom", transform=cbar.ax.transAxes
    )

    # 在colorbar底部添加文字说明
    cbar.ax.text(1.4, 0.05, "Low", ha="center", va="top", transform=cbar.ax.transAxes)

    # boundary_coords = np.array(boundary_poly.exterior.coords)
    # plt.plot(boundary_coords[:, 0], boundary_coords[:, 1], "r-", lw=1, label="Boundary")
    plt.show()


# * Background Value Method #######################
def get_kemans_boundary(gdf, column):
    import numpy as np
    from sklearn.cluster import KMeans
    import geopandas as gpd

    data = gdf[column].dropna().tolist()
    # 将数据转换为二维数组
    data = np.array(data).reshape(-1, 1)
    if data.size == 0:
        return 0.00
    # KMeans 聚类，设定为 2 类
    kmeans = KMeans(n_clusters=2, random_state=0).fit(data)

    # 获取聚类中心
    centers = kmeans.cluster_centers_.flatten()
    # 找到第一类（较小的类）的标签
    first_class_label = np.argmin(centers)
    # 选择第一类的数据，并取其最大值作为分界点
    labels = kmeans.labels_
    boundary = data[labels == first_class_label].max()
    boundary = np.mean(centers)  # 用聚类中心的中值作为分界点
    return boundary


def plot_kemans_boundary(data, value, unit, save=False):
    import numpy as np
    from collections import Counter
    from sklearn.cluster import KMeans
    import matplotlib.pyplot as plt

    if data.size == 0:
        return
    # 将数据转换为二维数组
    data = np.array(data).reshape(-1, 1)

    # KMeans 聚类，设定为 2 类
    kmeans = KMeans(n_clusters=2, random_state=0).fit(data)

    # 获取聚类中心
    centers = kmeans.cluster_centers_.flatten()
    boundary = np.mean(centers)  # 用聚类中心的中值作为分界点

    # 根据标签划分数据
    labels = kmeans.labels_
    lower_part = data[labels == np.argmin(centers)].flatten()
    upper_part = data[labels == np.argmax(centers)].flatten()

    # 统计数据点的出现次数
    data_counts = Counter(data.flatten())
    # 设置全局字体
    plt.rcParams["font.family"] = "Times New Roman"  # 仿宋
    plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号
    # 绘制结果图像
    plt.figure(figsize=(8, 6), dpi=90)
    for point, count in data_counts.items():
        # 分别绘制 lower_part 和 upper_part 的数据点
        if point in lower_part:
            plt.scatter(
                point,
                0,
                color="blue",
                s=50,
                label="Part Ⅰ" if point == lower_part[0] else "",
            )
        if point in upper_part:
            plt.scatter(
                point,
                0,
                color="orange",
                s=50,
                label="Part Ⅱ" if point == upper_part[0] else "",
            )

        # 如果数据点重复，标注数量
        if count > 1:
            plt.text(
                point,
                0.005,
                f"{count}",
                ha="center",
                color="black",
                fontsize=10,
                va="top",
            )

    # 标注簇中心
    plt.scatter(centers, [0, 0], color="red", s=100, marker="x", label="Cluster center")
    # 标注分界线
    plt.axvline(boundary, color="green", linestyle="--", label="Cut-off value")
    plt.text(boundary, -0.05, f"{boundary:.2f}", ha="right", color="green", fontsize=20)
    # 添加图例和标签
    plt.legend(fontsize=10, ncol=2)
    plt.xticks(fontsize=15)
    plt.yticks([])
    plt.xlabel(f"{value}({unit})", fontsize=15)
    if save:
        plt.savefig(f"./ref/KMEANS-{value}.png")
        return
    else:
        plt.show()


def 绘制保存异常点位(
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
    if boundary_polygon_file is not None:
        boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=4547)
        ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")
    else:
        fig, ax = plt.subplots()

        # 将 GeoDataFrame 的绘图环境绑定到 ax，但不绘制内容
        gdf.plot(ax=ax, visible=False)
    colors = {"√": "red", "×": "green", "⚪": "white"}
    gdf["color"] = gdf[column].map(colors)
    all_null = (gdf["color"] == "white").all()
    if all_null:
        return
    ax.scatter(gdf.geometry.x, gdf.geometry.y, marker="o", s=30, color=gdf["color"])
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
    Path("./pic").mkdir(parents=True, exist_ok=True)
    plt.savefig(f"./pic/{label}.png")


def 绘制污染点位分布V2(gdf, boundary_polygon_file=None, save=False):
    import geopandas as gpd
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    from matplotlib.lines import Line2D

    matplotlib.rcParams["font.family"] = "Times New Roman"
    if boundary_polygon_file is not None:
        boundary_polygon_gdf = gpd.read_file(boundary_polygon_file).to_crs(epsg=4547)
        ax = boundary_polygon_gdf.plot(facecolor="none", edgecolor="red")
    else:
        fig, ax = plt.subplots()

        # 将 GeoDataFrame 的绘图环境绑定到 ax，但不绘制内容
        gdf.plot(ax=ax, visible=False)
    colors = {"污染源": "red", "污染羽": "orange", "正常": "green"}
    gdf["color"] = gdf["污染类型"].map(colors)
    ax.scatter(gdf.geometry.x, gdf.geometry.y, marker="o", s=30, color=gdf["color"])

    add_north_arrow(ax)
    add_scalebar(ax, location="lower left")
    ax.set_xlabel("X 投影坐标 (米)")
    ax.set_ylabel("Y 投影坐标 (米)")
    # 添加自定义图例
    legend_elements = []
    if "污染源" in gdf["污染类型"].unique():
        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="污染源",
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
                label="污染羽",
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
                label="正常",
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

    if save:
        plt.savefig("./ref/污染点位分布图.png")
    else:
        plt.show()


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


def process_PCA(dataset, pca_columns):
    dataset = gpd.read_file(dataset)
    dataset = dataset[pca_columns].dropna()
    scaler_pca = StandardScaler()
    data_pca_scaled = scaler_pca.fit_transform(dataset)
    pca_analysis = PCA(n_components=3)
    pca_results = pca_analysis.fit_transform(data_pca_scaled)
    # 计算 PCA 载荷矩阵
    pca_loadings = pd.DataFrame(
        pca_analysis.components_.T, columns=["PC1", "PC2", "PC3"], index=pca_columns
    )
    # 计算 PCA 方差贡献率
    pca_var_ratio = pca_analysis.explained_variance_ratio_
    pca_scores = pd.DataFrame(pca_results, columns=["PC1", "PC2", "PC3"])
    return pca_results, pca_loadings, pca_var_ratio, pca_scores


def plot_PCA_variance_contribution(pca_var_ratioa):
    # 绘制 PCA 方差贡献率图
    fig = plt.figure(figsize=(4, 4))
    plt.bar(range(1, 4), pca_var_ratioa * 100, tick_label=["PC1", "PC2", "PC3"])
    plt.ylabel("Variance contribution rate(%)", fontsize=10)
    plt.xlabel("Principal component", fontsize=10)
    plt.title("PCA Variance Contribution", fontsize=10)
    # plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    return fig


def plot_PCA_loading_plot(pca_loadings, pca_var_ratio):
    fig, ax = plt.subplots(figsize=(4, 4))
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
    fig, ax = plt.subplots(figsize=(4, 4), dpi=dpi)
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
    boundary_gdf.plot(ax=ax, color="none", edgecolor="red", linewidth=2)
    ax.scatter(points_gdf.geometry.x, points_gdf.geometry.y, c="black", marker="x")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


# 定义绘图函数
def plot_PC1_interpolation(
    boundary_file,
    points_gdf,
    interpolation_method,
    pca_scores,
):

    boundary = gpd.read_file(boundary_file)

    # 提取插值点坐标
    x = points_gdf.geometry.x
    y = points_gdf.geometry.y
    z = pca_scores["PC1"].values  # PCA得分
    grid_x, grid_y = np.mgrid[
        min(x) - 0.001 : max(x) + 0.001 : 100j, min(y) - 0.001 : max(y) + 0.001 : 100j
    ]
    fig, ax = plt.subplots(figsize=(10, 8))

    if interpolation_method == "Nearest":

        cmap = "gist_rainbow"
        grid_z_nearest = scipy_interpolation(x, y, z, grid_x, grid_y, method="nearest")
        # 绘制最近邻插值结果
        contour_nearest = ax.contourf(
            grid_x, grid_y, grid_z_nearest, cmap="coolwarm", levels=10
        )
        fig.colorbar(
            contour_nearest,
            ax=ax,
            label="PC1(Nearest)",
        )
        ax.set_title("Spatial distribution of contamination(Nearest interpolation)")
        add_common_elements(ax, boundary, points_gdf)
        return fig

    elif interpolation_method == "Cubic":
        # 绘制立方插值结果
        add_common_elements(ax, boundary, points_gdf)
        grid_z_cubic = scipy_interpolation(x, y, z, grid_x, grid_y, method="cubic")
        # 绘制最近邻插值结果
        contour_cubic = ax.contourf(
            grid_x, grid_y, grid_z_cubic, cmap="coolwarm", levels=10
        )
        fig.colorbar(contour_cubic, ax=ax, label="PC1(Cubic)")
        ax.set_title("Spatial distribution of contamination(Cubic interpolation)")
        add_common_elements(ax, boundary, points_gdf)
        return fig
    elif interpolation_method == "IDW":
        add_common_elements(ax, boundary, points_gdf)
        grid_z_idw = idw_interpolation(
            x, y, z, grid_x, grid_y, power=2
        )  # 使用默认幂次2进行IDW插值
        contour_idw = ax.contourf(grid_x, grid_y, grid_z_idw, cmap="jet", levels=10)
        fig.colorbar(contour_idw, ax=ax, label="PC1(IDW)")
        ax.set_title("Spatial distribution of contamination(IDW interpolation)")
        add_common_elements(ax, boundary, points_gdf)
        return fig

    elif interpolation_method == "Kriging":
        add_common_elements(ax, boundary, points_gdf)
        # 绘制克里金插值结果
        grid_z_kriging = kriging_interpolation(
            x,
            y,
            z,
            np.linspace(min(x) - 0.001, max(x) + 0.001, 100),
            np.linspace(min(y) - 0.001, max(y) + 0.001, 100),
        )
        contour_kriging = ax.contourf(
            grid_x, grid_y, grid_z_kriging, cmap="gist_rainbow", levels=10
        )
        fig.colorbar(contour_kriging, ax=ax, label="PC1(Kriging)")
        ax.set_title("Spatial distribution of contamination(Kriging interpolation)")
        add_common_elements(ax, boundary, points_gdf)
        return fig


if __name__ == "__main__":
    pass
