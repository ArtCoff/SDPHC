# User Guide

## 1. Input Data Preparation

This software performs site contamination assessment based on non-invasive measurement datasets. Considering spatial relationships, the input data should be spatial vector data. It is recommended to use Geopackage format for data input. You can refer to the test files in the `tests` directory for input specifications.

## 2. Data Loading

On the software startup page, add the corresponding boundary data and non-invasive measurement datasets as instructed. Select the appropriate analysis method and proceed.

## 3. Indicator Matching

The indicators of non-invasive measurements are fixed. Although new indicators and analysis methods can be added based on new technologies in the future, currently supported analysis methods will only perform calculations on the supported measurement indicators.

## 4. Run Analysis

The entire process of analysis, computation, and plotting is executed in the background. Upon successful execution, results are returned to the user interface. Users can view the analysis results through the interface and export them in multiple formats.
