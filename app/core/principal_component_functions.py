import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from utils import (
    idw_interpolation,
    kriging_interpolation,
    scipy_interpolation,
)

matplotlib.use("QtAgg")
from .function_utils import (
    point_dataset_preprocess,
    boundary_file_preprocess,
    safe_remove,
    add_north_arrow,
    add_scalebar,
)
from .empirical_threshold_functions import mask_with_polygon
from shapely.ops import unary_union

# * PCA Method


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
        ax.text(
            x * 1.1,
            y * 1.1,
            variable,
            color=colors[i],
            fontsize=12,
            # fontweight="bold",
            ha="center",
            va="center",
        )

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
    import matplotlib as mpl
    from mpl_toolkits.axes_grid1 import make_axes_locatable

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
