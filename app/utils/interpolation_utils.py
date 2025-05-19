import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from pykrige.ok import OrdinaryKriging
import scipy.interpolate as spi


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
