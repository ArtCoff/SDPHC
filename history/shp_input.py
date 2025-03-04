import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import random
from scipy.spatial import ConvexHull
import numpy as np
import matplotlib.pyplot as plt

Monitoring_indicators = [
    "Radon",
    "VOCs",
    "CO2",
    "O2",
    "CH4",
    "H2",
    "H2S",
]  # 氡气 VOCs CO2 O2 CH4 H2 H2S
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
# print(Anomaly_value_Scale)
Anomaly_Rating_Scale = pd.DataFrame(data=abnormal_score, index=Monitoring_indicators)
# print(Anomaly_Rating_Scale)

shp_file = "C:\\Users\\g2382\\Desktop\\new_datas\\data_points.shp"
outline_polygon = "C:\\Users\\g2382\\Desktop\\datas\\outline_polygon.shp"
gdf = gpd.read_file(shp_file)
gdf["点位编号"] = np.random.randint(1, 200, 123)
gdf["Radon"] = gdf["Radon"].apply(
    lambda x: (np.random.uniform(3000, 3100) if x == 0 else x)
)
# gdf.loc[50, "Radon"] = 10.0
# gdf.loc[51, "Radon"] = 10.0
gdf["VOCs"] = gdf["VOCs"].apply(
    lambda x: (np.random.uniform(0.01, 0.1) if x == 0 else x)
)
# gdf["VOCs"] = np.random.uniform(0.01, 0.1, 123)
gdf["CO2"] = np.random.uniform(0.001, 0.01, 123)
gdf["O2"] = np.random.uniform(0.3, 0.2, 123)
gdf["CH4"] = np.random.uniform(0.0001, 0.0002, 123)
gdf["H2"] = np.random.uniform(1, 100, 123)
gdf["H2S"] = np.random.uniform(0.01, 1, 123)
gdf["SO2"] = np.random.uniform(0.1, 5, 123)

# print(gdf)
# print(gdf.head(52))

# gdf.to_file("./dataPoints.gpkg", driver="GPKG")


# 计算异常评分,标规范不统一，分两部分来写
def calculate_anomaly_score(row):
    more_indicators = ["VOCs", "CO2", "CH4", "H2", "H2S"]
    less_indicators = ["O2", "Radon"]
    score: int = 0
    for indicator in Monitoring_indicators:
        value = row[indicator]
        if indicator in more_indicators:
            if value >= Anomaly_value_Scale.loc[indicator, "A"]:
                score += Anomaly_Rating_Scale.loc[indicator, "A"]
            elif value >= Anomaly_value_Scale.loc[indicator, "B"]:
                score += Anomaly_Rating_Scale.loc[indicator, "B"]
            elif value >= Anomaly_value_Scale.loc[indicator, "C"]:
                score += Anomaly_Rating_Scale.loc[indicator, "C"]
            elif value >= Anomaly_value_Scale.loc[indicator, "D"]:
                score += Anomaly_Rating_Scale.loc[indicator, "D"]
        elif indicator in less_indicators:
            if value <= Anomaly_value_Scale.loc[indicator, "A"]:
                score += Anomaly_Rating_Scale.loc[indicator, "A"]
            elif value <= Anomaly_value_Scale.loc[indicator, "B"]:
                score += Anomaly_Rating_Scale.loc[indicator, "B"]
            elif value <= Anomaly_value_Scale.loc[indicator, "C"]:
                score += Anomaly_Rating_Scale.loc[indicator, "C"]
            elif value <= Anomaly_value_Scale.loc[indicator, "D"]:
                score += Anomaly_Rating_Scale.loc[indicator, "D"]

    return score


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


# 为每个监测指标计算单独得分并追加到gdf中
for indicator in Monitoring_indicators:
    score_column_name = f"{indicator}_Score"
    gdf[score_column_name] = gdf[indicator].apply(
        lambda x: calculate_single_indicator_score(x, indicator)
    )
gdf["Total_Anomaly_Score"] = gdf.apply(calculate_anomaly_score, axis=1)


def contamination_type_of_sampling_points(row):
    if row["Total_Anomaly_Score"] >= 17 and row["Radon_Score"] >= 1:
        return "污染源区"
    elif row["Total_Anomaly_Score"] >= 6 and row["VOCs_Score"] >= 1:
        return "疑似污染源区"
    elif row["Total_Anomaly_Score"] >= 1:
        return "污染范围"
    else:
        return "0"


gdf["Contamination_Type"] = gdf.apply(contamination_type_of_sampling_points, axis=1)
print(gdf)
# gdf.to_file("./Test.gpkg", driver="GPKG")


def gdf2excel(gdf):
    # 移除几何列，将GeoDataFrame转换为普通DataFrame
    df = gdf.drop(columns="geometry")
    # 定义要保存的文件路径和文件名
    output_file = "采样点.xlsx"
    # 将DataFrame导出为Excel文件
    df.to_excel(output_file, index=False)


# gdf2excel(gdf)
