#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: None

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.backends.backend_pdf import PdfPages

def calculate_quantiles_from_csv(file_path_1, file_path_2, percentiles, years_ahead_list):
    """
    金利期間構造比較（分位点と平均値ごとに数値を比較）。複数の将来時点をリストで指定可能。
    
    Parameters:
    -----------
    file_path_1 : str
        最初のCSVファイルのパス。
    file_path_2 : str
        2つ目のCSVファイルのパス。
    percentiles : list of float
        計算する分位点のリスト（例: [5, 50, 95]）。
    years_ahead_list : list of float
        将来時点のリスト (例: [3, 10] 3年後・10年後の計算)

    Returns:
    --------
    pd.DataFrame
        各将来時点における指定された分位点と平均値の計算結果を含むデータフレーム。
    """
    # CSVファイルを読み込む
    yield_1_df = pd.read_csv(file_path_1, encoding="shift-jis")
    yield_2_df = pd.read_csv(file_path_2, encoding="shift-jis")
    
    # 結果を格納する辞書
    results = {}

    # 各将来時点に対して計算
    for years_ahead in years_ahead_list:
        # 指定された年後の列を抽出
        column_index = int((years_ahead - 0.5) / 0.5)  # 0.5年刻みのため
        yield_1_future = yield_1_df.iloc[:, column_index]
        yield_2_future = yield_2_df.iloc[:, column_index]

        # %表記のため調整し、累積リターンを計算
        cumulative_returns_yield_1 = np.cumprod(1 + yield_1_future.values / 100, axis=0) - 1
        cumulative_returns_yield_2 = np.cumprod(1 + yield_2_future.values / 100, axis=0) - 1

        # 指定された分位点を計算
        quantiles_yield_1 = np.percentile(cumulative_returns_yield_1, percentiles, axis=0)
        quantiles_yield_2 = np.percentile(cumulative_returns_yield_2, percentiles, axis=0)

        # 平均値を計算
        mean_yield_1 = np.mean(cumulative_returns_yield_1)
        mean_yield_2 = np.mean(cumulative_returns_yield_2)

        # 結果を格納（分位点と平均値）
        results[years_ahead] = {
            "Percentile": [f"{p}th" for p in percentiles] + ["Mean"],
            f"Yield Scenario 1 ({years_ahead} years)": list(quantiles_yield_1) + [mean_yield_1],
            f"Yield Scenario 2 ({years_ahead} years)": list(quantiles_yield_2) + [mean_yield_2]
        }
    
    return results


def process_yield_curve(df, years_list = None, num_scenarios = 10000, time_points_per_scenario = 21):
    """
    指定された将来時点ごとのイールドカーブを分割し、辞書形式で返す関数

    Parameters:
    -----------
    df : pandas.DataFrame
        金利データを持つ元データフレーム (シナリオ数 × 将来時点数 × 列数)
    years_list : list of float, optional
        出力したい将来時点のリスト (例: [0.0, 1.0, 2.0])。デフォルトは None で、全ての将来時点を使用。
    num_scenarios : int, optional
        シナリオの数 (例: 10,000)。デフォルトは10,000。
    time_points_per_scenario : int, optional
        1シナリオあたりの将来時点の数 (例 : 0.5年刻みで21ポイント)。デフォルトは21。

    Returns:
    --------
    dict
        指定された将来時点ごとに分けられた辞書形式のデータ。
        キーは指定された将来時点 (例: '0.0_years', '1.0_years')、値はその時点のデータフレーム。
    """
    
    # デフォルトで全ての将来時点 (0年後, 0.5年後, ..., 10年後) を使用
    if years_list is None:
        years_list = np.linspace(0, (time_points_per_scenario - 1) / 2, time_points_per_scenario)  # 0.5年刻みの将来時点のリストを作成
    
    # 将来時点ごとのデータを辞書に格納
    data_dict = {}
    
    for time_point in years_list:
        # 指定された将来時点が何番目かを計算 (例: 0.5年 -> インデックス1)
        index_within_scenario = int(time_point * 2)  # 0.5年刻みの場合は2倍する
        
        # 各将来時点に対するデータを全シナリオ分抽出
        data = df.iloc[index_within_scenario::time_points_per_scenario, :]
        
        # データを辞書に格納 (キーは "X.0_years" の形式)
        data_dict[f"{time_point:.1f}_years"] = data
    
    # 加工後の辞書を返す
    return data_dict


def compute_quantiles(data_dict, quantiles_list):
    """
    辞書内の各将来時点における10,000パスのデータに対して、任意の分位点を計算し、分位点の結果を辞書に格納して返す関数。

    Parameters:
    -----------
    data_dict : dict
        将来時点をキー、10,000行のデータフレームを値とする辞書形式のデータ。
    quantiles_list : list of float
        計算したい分位点のリスト（例: [0.25, 0.50, 0.75]）。

    Returns:
    --------
    quantiles_dict : dict
        各将来時点をキーとし、その時点での指定された分位点を含む
        データフレームを値とする辞書。
    """
    
    # 分位点を格納する辞書
    quantiles_dict = {}
    
    # 各将来時点ごとに処理
    for time_point, df in data_dict.items():
        # 各列の指定された分位点を計算
        quantiles = df.quantile(quantiles_list)
        
        # 分位点を辞書に格納
        quantiles_dict[time_point] = quantiles
        
        # 分位点を表示
        print(f"\n{time_point} の分位点:")
        print(quantiles)
    
    # 分位点を格納した辞書を返す
    return quantiles_dict


def plot_and_save_histograms(data_dict, save_path):
    """
    辞書内の各将来時点のデータに対してヒストグラムを作成し、
    指定されたパスにPDFとして保存する関数。

    Parameters:
    -----------
    data_dict : dict
        将来時点をキー、10,000行のデータフレームを値とする辞書形式のデータ。
    save_path : str
        ヒストグラムを保存するパス。指定したディレクトリにPDFファイルが保存される。

    Returns:
    --------
    None
    """
    
    # 保存先ディレクトリの存在を確認、なければ作成
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    # 保存先のPDFファイル名を設定
    pdf_file_path = os.path.join(save_path, 'histograms.pdf')

    # PDFファイルにヒストグラムを1ページずつ保存
    with PdfPages(pdf_file_path) as pdf:
        for time_point, df in data_dict.items():
            # ヒストグラムを作成
            plt.figure(figsize=(10, 6))
            df.hist(bins=50, alpha=0.75, figsize=(10, 6))
            plt.suptitle(f"Histograms for {time_point}")
            
            # 現在のページをPDFに追加
            pdf.savefig()  
            plt.close()  # プロットを閉じてメモリを節約
            
    print(f"ヒストグラムが {pdf_file_path} に保存されました。")


def compute_quantiles_and_plot_histograms(data_dict, quantiles_list):
    """
    辞書内の各将来時点における10,000パスのデータに対して任意の分位点を計算し、ヒストグラムをプロット,
    分位点の結果を辞書に格納して返す関数。

    Parameters:
    -----------
    data_dict : dict
        将来時点をキー、10,000行のデータフレームを値とする辞書形式のデータ。
    quantiles_list : list of float
        計算したい分位点のリスト（例: [0.25, 0.50, 0.75]）。

    Returns:
    --------
    quantiles_dict : dict
        各将来時点をキーとし、その時点での指定された分位点を含むデータフレームを値とする辞書。
    """
    
    # 分位点を格納する辞書
    quantiles_dict = {}
    
    # 各将来時点ごとに処理
    for time_point, df in data_dict.items():
        # 各列の指定された分位点を計算
        quantiles = df.quantile(quantiles_list)
        
        # 分位点を辞書に格納
        quantiles_dict[time_point] = quantiles
        
        # 分位点を表示
        print(f"\n{time_point} の分位点:")
        print(quantiles)
        
        # データフレーム内のすべての列を対象にヒストグラムを作成
        plt.figure(figsize=(10, 6))
        df.hist(bins = 50, alpha = 0.75, figsize =( 10, 6))
        plt.suptitle(f"Histograms for {time_point}")
        plt.show()
    
    # 分位点を格納した辞書を返す
    return quantiles_dict



