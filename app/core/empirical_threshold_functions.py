import pandas as pd
import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

matplotlib.use("QtAgg")
from utils import NIS_indicators, Drawing_specifications
from .function_utils import (
    point_dataset_preprocess,
    boundary_file_preprocess,
    safe_remove,
    add_north_arrow,
    add_scalebar,
)


# * Experience Value Method
# NIS_indicators = [
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
        [indicator.value.name for indicator in NIS_indicators],
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
        NIS_indicators.VOCs.value.name,
        NIS_indicators.CO2.value.name,
        NIS_indicators.O2.value.name,
        NIS_indicators.CH4.value.name,
        NIS_indicators.H2.value.name,
        NIS_indicators.H2S.value.name,
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
    else:
        result["All_indicators_Scores"] = None
    return result


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
    # * Setting up color mapping, assigning colors by 'Category'
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

    # Close graphics to prevent memory leaks
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
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1, 0))
    plt.tight_layout()
    plt.close(fig)
    return fig


def mask_with_polygon(grid_x, grid_y, grid_z, polygon):
    from shapely.geometry import Point
    import numpy as np

    # Create a mask
    mask = np.zeros_like(grid_z, dtype=bool)
    for i in range(grid_z.shape[0]):
        for j in range(grid_z.shape[1]):
            point = Point(grid_x[i, j], grid_y[i, j])
            if polygon.contains(point):
                mask[i, j] = True

    # Apply the mask
    masked_grid_z = np.where(mask, grid_z, np.nan)
    return masked_grid_z


import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from shapely.ops import unary_union


def Score_interpolation(gdf, boundary_gdf, method="linear"):
    try:
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

        # Boundary drawing (efficient rendering with geopandas)
        boundary.boundary.plot(ax=ax, color="red", lw=1, label="Boundary")
        ax.legend()
        return fig
    except Exception as e:
        raise RuntimeError(f"Processing failed: {str(e)}")
