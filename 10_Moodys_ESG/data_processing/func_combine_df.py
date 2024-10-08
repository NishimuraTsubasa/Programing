#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: None

import os
import pandas as pd

def combine_asset_scenarios_by_scenario(input_folder, output_file, asset_list, num_scenarios = 10000):
    """
    各アセットのリターンデータをシナリオ番号ごとに結合し、1つのCSVファイルに保存する関数

    Parameters:
    -----------
    input_folder : str
        複数の資産リターンファイルが含まれているフォルダのパス
    output_file : str
        結合後のデータを保存するCSVファイルのパス
    asset_list : list
        各資産のファイル名

    Returns:
    --------
    None
    """
    # 全資産のデータを読み込む (index はないものとして処理)
    asset_data_list = [pd.read_csv(os.path.join(input_folder, f"{asset_file}.csv"), header = None) for asset_file in asset_list]

    # 結果を格納するリスト
    combined_data = []

    # 各シナリオごとに、すべてのアセットのデータを結合してリストに追加
    for scenario_idx in range(num_scenarios):
        for asset_data in asset_data_list:
            # 各アセットの特定のシナリオ（1行分）を取り出す
            combined_data.append(asset_data.iloc[scenario_idx, :])

    # リストをデータフレームに変換
    combined_df = pd.DataFrame(combined_data)

    # 結合したデータをCSVファイルとして保存
    combined_df.to_csv(os.path.join(output_file, "combined_df.csv"), header = None)

    print(f"Combined data saved to: {output_file}")

if __name__ == "__main__":
    # 加工用データパス
    input_folder = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\risk_assets" # 結合対象のExcelを格納したフォルダパス
    output_folder = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\risk_assets" # 結合対象のExcelを格納したフォルダパス
    # アセット名
    asset_names = [
        "国内株式", 
        "オープン外債", 
        "ヘッジ外債", 
        "外国株式", 
        "ヘッジファンド",  
        "国内リアルアセット",  
        "海外プライベートエクイティ", 
        "海外リアルアセット", 
    ]

    # 関数を実行
    combine_asset_scenarios_by_scenario(input_folder, output_folder, asset_names)

