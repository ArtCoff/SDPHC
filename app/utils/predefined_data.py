from enum import Enum
from pathlib import Path

current_dir = Path(__file__).parent


class Software_info(Enum):
    software_name = "Software for Detecting Petroleum Hydrocarbons Contamination"
    software_short_name = "SDPHC"
    software_name_chinese = "微扰动污染调查分析软件"
    software_version = "1.0.0"
    software_author = "Hefei University of Technology"
    software_email = ""
    software_website = ""


class Drawing_specifications:
    EPSG_code = 4547


class Methods(Enum):
    Empirical_Threshold_Analysis = "Empirical Threshold Analysis"
    Background_Level_Analysis = "Background Level Analysis"
    Principal_Component_Analysis = "Principal Component Analysis"


class Secondary_Functions_of_ETA(Enum):
    function_PCP = "Pollution exceedance points"  # "指示污染超标范围点位（除氡气）"
    function_PSA = "Pollution source area"  # "污染源区与疑似污染源区"
    function_SOC = "Scope of contamination"  # "污染范围"
    function_PLI = "Pollution level identification"  # "污染程度识别"


# 单个指标的类
class indicator:
    def __init__(self, name, chinese_name, unit, label: str = None):
        self.name = name
        self.chinese_name = chinese_name
        self.unit = unit
        if label is None:
            self.label = str(name)
        else:
            self.label = label

    def __repr__(self):
        return f"indicator(name={self.name}, chinese_name={self.chinese_name}, unit={self.unit},label={self.label})"


class NIS_indicators(Enum):
    Radon = indicator(
        name="Radon",
        chinese_name="氡气",
        unit="Bq/m³",
    )
    VOCs = indicator(name="VOCs", chinese_name="挥发性有机物", unit="ppb")
    CO2 = indicator(
        name="CO2", chinese_name="二氧化碳", unit="ppm", label="CO<sub>2</sub>"
    )
    O2 = indicator(name="O2", chinese_name="氧气", unit="%", label="O<sub>2</sub>")
    CH4 = indicator(name="CH4", chinese_name="甲烷", unit="%", label="CH<sub>4</sub>")
    H2S = indicator(
        name="H2S", chinese_name="硫化氢", unit="mg/L", label="H<sub>2</sub>S"
    )
    H2 = indicator(name="H2", chinese_name="氢气", unit="mg/L", label="H<sub>2</sub>")
    FG = indicator(
        name="FG",
        chinese_name="功能基因",
        unit="copies/g",
        label="Functional<br>genes",
    )

    @classmethod
    def get_unit_by_name(cls, name):
        for member in cls:
            if member.value.name == name:
                return member.value.unit
        return ""  # 如果未找到匹配项，返回空字符串

    @classmethod
    def get_enumName_by_valueName(cls, value_name):
        for member in cls:
            if member.value.name == value_name:
                return member.name
        return None
