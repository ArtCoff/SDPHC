from enum import Enum

software_name = "MIM LNAP Pollution Aid Identification Software"
#
# MethodsCode = {
#     "Experience value method": "M1",
#     "Background value method": "M2",
#     "PCA method": "M3",
# }

EPSG_code = 4547


class Methods(Enum):
    Experience_value_method = "Experience value method"
    Background_value_method = "Background value method"
    PCA_method = "PCA method"


class Secondary_Functions_of_ExperienceValue(Enum):
    function_PCP = "Pollution exceedance points"
    function_PSA = "Pollution source area"
    function_SOC = "Scope of contamination"
    function_PLI = "Pollution level identification"
