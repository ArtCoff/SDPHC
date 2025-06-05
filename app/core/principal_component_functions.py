import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from shapely.ops import unary_union


from utils import (
    idw_interpolation,
    kriging_interpolation,
    scipy_interpolation,
)


from .function_utils import (
    point_dataset_preprocess,
    boundary_file_preprocess,
    safe_remove,
    add_north_arrow,
    add_scalebar,
)
from .empirical_threshold_functions import mask_with_polygon

matplotlib.use("QtAgg")

# * PCA Method


def return_PCA_results(point_dataset, options, outline_dataset):
    gdf = point_dataset_preprocess(point_dataset=point_dataset, options=options)
    boundary_gdf = boundary_file_preprocess(outline_dataset)
    pca_results, pca_loadings, pca_var_ratio, pca_gdf = process_PCA(
        gdf=gdf, options=options
    )
    PC1_score_fig = plot_PC_score(pca_gdf, boundary_gdf, column="PC1")
    PCA_variance_contribution_fig = plot_PCA_variance_contribution(pca_var_ratio)
    PCA_loading_plot_fig = plot_PCA_loading_plot(pca_loadings, pca_var_ratio)
    PCA_Biplot_fig = plot_PCA_Biplot(pca_results, pca_loadings, pca_var_ratio)
    PC1_interpolation_figs = {}
    interpolation_methods = ["Nearest", "Cubic", "IDW", "Kriging"]
    for interpolation_method in interpolation_methods:
        fig = plot_PC_interpolation(
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
    # Calculate PCA Load Matrix
    pca_loadings = pd.DataFrame(
        pca_analysis.components_.T, columns=["PC1", "PC2", "PC3"], index=pca_columns
    )
    # Calculate the PCA variance contribution ratio
    pca_var_ratio = pca_analysis.explained_variance_ratio_
    pca_scores = pd.DataFrame(pca_results, columns=["PC1", "PC2", "PC3"])
    pca_data = data_pca_analysis.reset_index(drop=True)

    # Combining raw data with principal component scores
    complete_pca_df = pd.concat([pca_data, pca_scores], axis=1)

    # Add ID and geometry information
    if options.get("Point_ID") is not None:
        complete_pca_df["ID"] = gdf.loc[
            data_pca_analysis.index, options.get("Point_ID")
        ].values
    complete_pca_df["geometry"] = gdf.loc[data_pca_analysis.index, "geometry"].values
    pca_gdf = gpd.GeoDataFrame(complete_pca_df, geometry="geometry")
    print("pca_gdf:", pca_gdf.head())
    return pca_results, pca_loadings, pca_var_ratio, pca_gdf


def plot_PCA_variance_contribution(pca_var_ratioa):
    # Plotting the PCA variance contribution
    fig = plt.figure(figsize=(6, 4))
    bars = plt.bar(range(1, 4), pca_var_ratioa * 100, tick_label=["PC1", "PC2", "PC3"])
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.1,
            f"{height:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    plt.ylabel("Variance contribution rate(%)", fontsize=10)
    plt.xlabel("Principal component", fontsize=10)
    plt.title("PCA Variance Contribution", fontsize=10)
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
    ax.set_xlabel(f"PC1 ({pca_var_ratio[0]*100:.2f}%)", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca_var_ratio[1]*100:.2f}%)", fontsize=10)
    ax.set_title(
        "PCA Loading Plot",
        fontsize=10,
    )

    # Add reference lines at x=0 and y=0 (dashed lines)
    ax.axhline(0, color="gray", linewidth=1, linestyle="--")
    ax.axvline(0, color="gray", linewidth=1, linestyle="--")
    plt.tight_layout()
    return fig


def plot_PCA_Biplot(pca_results, pca_loadings, pca_var_ratio, dpi=150):
    pca_scores = pd.DataFrame(pca_results, columns=["PC1", "PC2", "PC3"])
    # sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(6, 4), dpi=dpi)
    ax.scatter(
        pca_scores["PC1"],
        pca_scores["PC2"],
        s=10,
        alpha=0.7,
        color="gray",
        label="Samples",
    )
    # Plotting load vectors (variable arrows)
    arrow_scale = 10  # Scaling factor

    colors = sns.color_palette("hls", n_colors=len(pca_loadings.index))

    for i, variable in enumerate(pca_loadings.index):
        # Scaled coordinates
        x = pca_loadings.loc[variable, "PC1"] * arrow_scale
        y = pca_loadings.loc[variable, "PC2"] * arrow_scale

        # Drawing Arrows
        ax.arrow(
            0,
            0,
            x,
            y,
            color=colors[i],
            alpha=0.8,
            linewidth=2,
            head_width=0.2,  # Arrow head width
            head_length=0.3,  # Arrow head length
            length_includes_head=True,
        )

        # Add a text label near the end of the arrow
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

    ax.set_xlabel(f"PC1 ({pca_var_ratio[0]*100:.2f}%)", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca_var_ratio[1]*100:.2f}%)", fontsize=10)
    ax.set_title("PCA Biplot", fontsize=10)
    ax.axhline(0, color="gray", linewidth=1, linestyle="--")
    ax.axvline(0, color="gray", linewidth=1, linestyle="--")
    ax.legend()
    plt.tight_layout()
    return fig


def add_common_elements(ax, boundary_gdf, points_gdf):
    boundary_gdf.plot(
        ax=ax, color="none", edgecolor="black", linewidth=1, label="Boundary"
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
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    # ax.legend(fontsize=10)


def plot_PC_score(
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

    # Setting Global Styles
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
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)
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
    boundary_gdf.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.2)
    ax.tick_params(axis="both", which="major", labelsize=fontsize - 2, direction="in")
    ax.set_xlabel("X", labelpad=labelpad)
    ax.set_ylabel("Y", labelpad=labelpad)
    return fig


def plot_PC_interpolation(
    boundary_gdf,
    points_gdf,
    interpolation_method,
    PC="PC1",
    dpi=150,
) -> Figure:
    # Extract interpolated point coordinates
    x = points_gdf.geometry.x
    y = points_gdf.geometry.y
    z = points_gdf[PC].values
    # Create a mesh
    grid_x, grid_y = np.mgrid[
        min(x) - 0.001 : max(x) + 0.001 : 100j, min(y) - 0.001 : max(y) + 0.001 : 100j
    ]

    # Merging boundary polygons
    boundary_polygon = unary_union(boundary_gdf.geometry)
    fig = Figure(figsize=(8, 6), dpi=dpi)
    ax = fig.add_subplot(111, aspect="equal")
    # 绘图配置
    cmap = plt.cm.RdBu_r  # 红到蓝渐变色标
    levels = np.linspace(np.nanmin(z), np.nanmax(z), 20)
    if interpolation_method == "Nearest":
        from scipy.interpolate import griddata

        grid_z = griddata((x, y), z, (grid_x, grid_y), method="nearest")
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)
        contour = ax.contourf(grid_x, grid_y, masked_z, cmap=cmap, levels=levels)
    elif interpolation_method == "Cubic":
        from scipy.interpolate import griddata

        grid_z = griddata((x, y), z, (grid_x, grid_y), method="cubic")
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)
        contour = ax.contourf(grid_x, grid_y, masked_z, cmap=cmap, levels=levels)
    elif interpolation_method == "IDW":
        grid_z = idw_interpolation(x, y, z, grid_x, grid_y, power=2)
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)
        contour = ax.contourf(grid_x, grid_y, masked_z, cmap=cmap, levels=levels)

    elif interpolation_method == "Kriging":
        grid_z = kriging_interpolation(
            x,
            y,
            z,
            np.linspace(min(x) - 0.001, max(x) + 0.001, 100),
            np.linspace(min(y) - 0.001, max(y) + 0.001, 100),
            variogram_model="spherical",
        )
        masked_z = mask_with_polygon(grid_x, grid_y, grid_z, boundary_polygon)
        contour = ax.contourf(grid_x, grid_y, masked_z, cmap=cmap, extend="neither")
    add_common_elements(ax, boundary_gdf, points_gdf)

    # * Customize the colorbar
    cbar = fig.colorbar(contour, ax=ax, orientation="vertical", pad=0.03, shrink=0.8)
    cbar.set_label(f"{PC} Score (Red=High, Blue=Low)", fontsize=10)
    cbar.ax.tick_params(
        labelsize=8,
    )
    from matplotlib.ticker import FormatStrFormatter

    cbar.ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    return fig
