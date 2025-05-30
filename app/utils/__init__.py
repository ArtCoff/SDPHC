from .predefined_data import (
    Software_info,
    Methods,
    NIS_indicators,
    Drawing_specifications,
    Secondary_Functions_of_ETA,
)
from .pyside6_utils import (
    AppStyle,
    center_window,
    load_settings,
    traverse_layout,
    show_multiple_plots,
    update_config_value,
)
from .interpolation_utils import (
    kriging_interpolation,
    scipy_interpolation,
    idw_interpolation,
)
from .auto_report_EN import (
    save_docx_safely,
    insert_image,
    setup_styles,
    add_cover,
    add_bullet_list,
    add_table,
    add_note,
    report_test,
)
