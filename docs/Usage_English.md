# User Guide

## 1. Input Data Preparation

This software performs site contamination assessment based on non-invasive measurement datasets. Considering spatial relationships, the input data should be spatial vector data. It is recommended to use Geopackage format for data input. You can refer to the test files in the `tests` directory for input specifications.

## 2. Data Loading

On the software startup page, add the corresponding boundary data and non-invasive measurement datasets as instructed. Select the appropriate analysis method and proceed.

## 3. Indicator Matching

The indicators of non-invasive measurements are fixed. Although new indicators and analysis methods can be added based on new technologies in the future, currently supported analysis methods will only perform calculations on the supported measurement indicators.

## 4. Run Analysis

The entire process of analysis, computation, and plotting is executed in the background. Upon successful execution, results are returned to the user interface. Users can view the analysis results through the interface and export them in multiple formats.

## 5. Report Template

Here's how to write a suitable report template.

**Create a new file**
Create a new python file in the _report_templates_ directory with the template name

**Introduce necessary functions**
Introduce the necessary settings for _python-docx_ at the beginning of the file, and the intended function functions from _auto_report_EN_ within the utils module.  
For example:

```
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_ALIGN_PARAGRAPH
from pathlib import Path
from datetime import datetime
import pandas as pd
from utils import (
    add_table,
    add_note,
    add_bullet_list,
    insert_image,
    setup_styles,
    save_docx_safely
)
```

**Write the main content of the template**
Write the different sections of the template according to the required content and encapsulate them as functions.
Finally, a function is used to synthesize the above parts, and the required data is given by parameters.
The images used in the content are recommended to be saved locally in the form of a cache and inserted using PIL.
The center passes the function to the main program and calls it after the analysis is complete.
