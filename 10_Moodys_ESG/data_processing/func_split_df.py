#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: None

import os
import pandas as pd

def data_processing(data, output_folder, asset_list):
    """
    各資産ごとの将来リターンデータを分割し、指定フォルダに出力する関数

    Parameters:
    -----------
    data : pd.DataFrame
        各時点の将来リターンのみを含むデータフレーム
    output_folder : str
        各資産ごとのデータを保存するフォルダのパス
    num_assets : int
        リスク性資産の数 (例: 8つのアセットの場合、8と指定)
    """
    # アセットリスト
    num_assets = len(asset_list)

    # 保存先フォルダが存在しない場合は作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 各資産ごとのデータを分割し保存
    for i in range(num_assets):
        # 各資産のデータを取得 (i番目の資産のデータ)
        asset_data = data.iloc[i::num_assets, :]
        
        # ファイル名を生成して保存 (例: asset_1.xlsx)
        asset_file = os.path.join(output_folder, f"{asset_list[i]}.csv")
        asset_data.to_csv(asset_file, index = False, header = False)
        
        print(f"{asset_list[i]} data saved to: {asset_file}")



if __name__ == "__main__":
    # 加工用データパス
    df = pd.read_csv(r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\10000_risk_assets_2.csv", header = None) # 加工用Excelパス
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
    # アウトプットフォルダパス
    output_folder = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Maruchu"

    # 関数を実行
    data_processing(df, output_folder, asset_names)










