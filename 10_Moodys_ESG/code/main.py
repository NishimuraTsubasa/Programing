#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: 

import pandas as pd
import numpy as np
import matplotlib
import os
import 

def main():
    """
    
    
    """



    # テスト実行（例: 3年後）
    compare_future_distributions(file_path_1, file_path_2, 3)


    # 関数をテスト実行 (例: 3年後と10年後)
    compare_future_distributions(file_path_1, file_path_2, 3)  # 3年後の比較
    compare_future_distributions(file_path_1, file_path_2, 10)  # 10年後の比較


    # 関数をテスト実行 (例: 5%, 50%, 95%)
    percentiles_to_calculate = [5, 50, 95]
    result_df = calculate_quantiles_from_csv(file_path_1, file_path_2, percentiles_to_calculate)
    tools.display_dataframe_to_user(name="Custom Percentile Comparison Function Result", dataframe=result_df)


    # テスト実行（例: 3年後と10年後の結果）
    years_ahead_to_calculate = [3, 10]
    result_df_multiple_years = calculate_quantiles_from_csv(file_path_1, file_path_2, percentiles_to_calculate, years_ahead_to_calculate)
    tools.display_dataframe_to_user(name="Quantile Comparison for Multiple Future Years with Doc", dataframe=result_df_multiple_years)

if __name__ is main:

