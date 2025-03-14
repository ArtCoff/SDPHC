from enum import Enum


class Software_info:
    software_name = "MIM LNAP Pollution Aid Identification Software"
    software_version = "1.0.0"
    software_author = "Hefei University of Technology"
    software_email = ""
    software_website = ""


class Drawing_specifications:
    EPSG_code = 4547


class MIM_indicators(Enum):
    Radon = "Radon"
    VOCs = "VOCs"
    CO2 = "CO2"
    O2 = "O2"
    CH4 = "CH4"
    H2S = "H2S"
    H2 = "H2"
    FG = "Functional genes"


class Methods(Enum):
    Experience_value_method = "Experience value method"
    Background_value_method = "Background value method"
    PCA_method = "PCA method"


class Secondary_Functions_of_ExperienceValue(Enum):
    function_PCP = "Pollution exceedance points"  # "指示污染超标范围点位（除氡气）"
    function_PSA = "Pollution source area"  # "污染源区与疑似污染源区"
    function_SOC = "Scope of contamination"  # "污染范围"
    function_PLI = "Pollution level identification"  # "污染程度识别"
