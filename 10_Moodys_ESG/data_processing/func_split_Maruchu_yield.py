#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: None

import os
import pandas as pd
import numpy as np


def export_yield_scenarios(data, output_folder, time_points = 21):
    """
    Exports yield data for each future time point into separate Excel files, each containing 10,000 scenarios.
    
    Args:
    data (DataFrame): The input DataFrame containing the yield data.
    scenarios_num (int): Number of scenarios per time point.
    total_time_points (int): Total number of time points to process.
    n_columns (int): Number of columns in each output file, representing yield points.
    output_folder (str): Path to the directory where the Excel files will be saved.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Calculate number of columns representing yield points
    n_columns = len(data.columns)
    data.columns = [i * 0.5 for i in range(n_columns)]

    # Extract and save data for each time point
    for i in range(time_points):
        # Calculate the starting indices for each time point ensuring not to exceed the data frame's length
        start_indices = range(i, len(data), time_points)
        df_time_point = data.iloc[start_indices].reset_index(drop=True)
        output_file_path = os.path.join(output_folder, f"Yield_Scenarios_at_{i * 0.5}_Years.csv")
        df_time_point.to_csv(output_file_path, index=False, encoding = "shift-jis")

if __name__ == "__main__":

    #  必要情報をインプット
    df = pd.read_csv(r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\yield_curve_scenarios.csv", header = None)
    output_folder = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Maruchu\yield_scenario"

    export_yield_scenarios(df, output_folder)



