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

def export_asset_returns_to_csv(data, output_folder):
    """
    Exports asset return data into individual Excel files, with future points as columns and scenarios as rows.
    
    Args:
    data (DataFrame): Input DataFrame containing 'Scenario', 'Time', and asset returns.
    output_folder (str): Path to the directory where the Excel files will be saved.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Process each asset and save to an Excel file
    for column in data.columns[2:]:  # start from 3rd column (asset returns)
        asset_data = data.pivot(index='Scenario', columns='Time', values=column)
        file_path = os.path.join(output_folder, f"{column}.xlsx")
        asset_data.to_csv(file_path, index=True)


if __name__ == "__main__":

    #  必要情報をインプット
    df = pd.read_csv(r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Moodys_ESG.csv", encoding = "shift-jis")
    output_folder = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Moodys"

    export_asset_returns_to_csv(df, output_folder)

