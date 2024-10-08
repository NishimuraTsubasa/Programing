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


def process_and_compare_scenario_data(folder1, folder2, percentiles, fx_file_name = "為替レート.csv"):
    """
    2つのフォルダに存在する同名ファイルの将来リターンデータを比較し、外貨建ておよび円建てで累積リターンを計算し、
    為替シナリオの分位点と平均値を含む結果を辞書形式に格納する関数
    
    Parameters:
    -----------    
    folder1 : str
        最初のフォルダのパス
    folder2 : str
        2つ目のフォルダのパス
    percentiles : list of float
        計算したい分位点のリスト（例: [5, 50, 95] など）
    fx_file_name : str
        為替シナリオのファイル名（例: '為替レート.csv'）

    Returns:
    --------
    dict
        各アセットごとの外貨建てリターン、円建てリターン、為替レート変化率を含む辞書
    """
    results_dict = {}  # 結果を格納する辞書

    # 1. 為替シナリオの処理
    fx_scenario = process_fx_scenarios(folder1, folder2, fx_file_name, percentiles)
    results_dict['FX_change'] = fx_scenario

    # 2. folder1のファイルを全て確認し、folder2に同じ名前のファイルがあるかを確認
    for file_name in os.listdir(folder1):
        # FXは 1.にて処理しているので、飛ばす
        if file_name != fx_file_name:
            file1_path = os.path.join(folder1, file_name)
            file2_path = os.path.join(folder2, file_name)

            # 両方のフォルダに同名のファイルが存在する場合のみ処理を行う
            if os.path.isfile(file2_path):
                # ここでデータを処理し、結果を辞書に格納
                asset_name = file_name.split('.')[0]  # アセット名をファイル名から取得
                results_dict[asset_name] = process_asset_data(file1_path, file2_path, percentiles, fx_scenario)

    return results_dict


def process_fx_scenarios(folder1, folder2, file_name, percentiles):
    """
    2つのフォルダから為替シナリオを読み込み、分位点と平均値を計算する関数
    
    Parameters:
    -----------    
    folder1 : str
        最初のフォルダのパス
    folder2 : str
        2つ目のフォルダのパス
    file_name : str
        為替シナリオのファイル名（例: '為替レート.csv'）
    percentiles : list of float
        計算したい分位点のリスト
    
    Returns:
    --------
    dict
        為替シナリオのファイル1とファイル2の分位点と平均値を含む辞書
    """
    def load_data(folder, file_name):
        return pd.read_csv(os.path.join(folder, file_name), header=None)

    data1 = load_data(folder1, file_name)
    data2 = load_data(folder2, file_name)

    result_df1 = calculate_statistics(data1, percentiles)
    result_df2 = calculate_statistics(data2, percentiles)

    return {
        'File1_result': result_df1,
        'File2_result': result_df2
    }

def process_asset_data(file1_path, file2_path, percentiles, fx_scenario, convert_to_jpy=True):
    """
    各アセットに対して、外貨建ておよび円建てのリターンを計算し、分位点と期待値を辞書形式で返す関数。
    
    Parameters:
    -----------    
    file1_path : str
        ファイル1のパス
    file2_path : str
        ファイル2のパス
    percentiles : list of float
        計算したい分位点のリスト
    fx_scenario : pd.DataFrame
        為替レートの将来シナリオデータ
    convert_to_jpy : bool, optional
        True の場合は外貨建てから円建てに変換し、False の場合は円建てから外貨建てに変換する。デフォルトは True。
    
    Returns:
    --------
    dict
        各アセットの外貨建てリターンと円建てリターンを含む辞書
    """
    data1 = pd.read_csv(file1_path, header=None)
    data2 = pd.read_csv(file2_path, header=None)

    result_df1_foreign = calculate_statistics(data1, percentiles)
    result_df2_foreign = calculate_statistics(data2, percentiles)

    returns1_jpy = convert_returns(data1, fx_scenario, convert_to_jpy)
    returns2_jpy = convert_returns(data2, fx_scenario, convert_to_jpy)

    result_df1_jpy = calculate_statistics(returns1_jpy, percentiles)
    result_df2_jpy = calculate_statistics(returns2_jpy, percentiles)

    conversion_label = 'JPY' if convert_to_jpy else 'Foreign_Currency'
    original_label = 'Foreign_Currency' if convert_to_jpy else 'JPY'

    return {
        original_label: {
            'File1_result': result_df1_foreign,
            'File2_result': result_df2_foreign
        },
        conversion_label: {
            'File1_result': result_df1_jpy,
            'File2_result': result_df2_jpy
        }
    }

def calculate_statistics(data, percentiles):
    """
    リターンデータまたは為替データに基づいて分位点と期待値を計算する共通関数
    
    Parameters:
    -----------    
    data : pd.DataFrame
        リターンデータまたは為替リターンデータ (0.5年刻み)
    percentiles : list of float
        計算したい分位点のリスト
    
    Returns:
    --------
    pd.DataFrame
        分位点と期待値を含むデータフレーム
    """
    returns = (1 + data.iloc[:, ::2]) * (1 + data.iloc[:, 1::2]) - 1

    quantiles = np.percentile(returns, percentiles, axis=0)
    mean_values = np.mean(returns, axis=0)

    result_df = pd.DataFrame(quantiles, index=[f"{p}th" for p in percentiles], columns=[f"Year_{i+1}" for i in range(returns.shape[1])])
    result_df.loc['Mean'] = mean_values  # 期待値を追加

    return result_df


def convert_returns(returns, fx_scenario, convert_to_jpy = True):
    """
    外貨建てのリターンを為替シナリオに基づいて円建てに変換、または円建てから外貨建てに変換する関数
    
    Parameters:
    -----------    
    returns : pd.DataFrame
        リターンのデータフレーム (0.5年刻み)
    fx_scenario : pd.DataFrame
        為替レートの将来シナリオデータ (0.5年刻み)
    convert_to_jpy : bool, optional
        True の場合は外貨建てから円建てに変換し、False の場合は円建てから外貨建てに変換する。デフォルトは True。
    
    Returns:
    --------
    pd.DataFrame
        円建てまたは外貨建てに変換されたリターンのデータフレーム
    """
    cumulative_fx_returns = (1 + fx_scenario.iloc[:, ::2]) * (1 + fx_scenario.iloc[:, 1::2]) - 1
    if convert_to_jpy:
        return (1 + returns) * (1 + cumulative_fx_returns) - 1
    else:
        return (returns / (1 + cumulative_fx_returns)) - 1
