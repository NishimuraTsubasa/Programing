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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def visualize_scenario_comparison_and_save_to_pdf(results_dict, output_folder, pdf_filename = "result.pdf"):
    """
    辞書に格納された外貨建てと円建ての2つのシナリオ、および為替変化率の分位点と平均値を可視化し、指定フォルダにPDF形式で保存する関数
    
    Parameters:
    -----------    
    results_dict : dict
        各アセットのシナリオ比較結果を含む辞書（外貨建て、円建て、為替変化率のデータを含む）
    output_folder : str
        PDFファイルを保存するフォルダ
    pdf_filename : str
        保存するPDFファイル名 (例: 'comparison_results.pdf')
    
    Returns:
    --------
    None
    """
    # PDFファイルの保存先を指定
    pdf_file_path = os.path.join(output_folder, pdf_filename)
    
    # PDFファイルに書き込む準備
    with PdfPages(pdf_file_path) as pdf:
        for asset, result in results_dict.items():
            if asset == 'Fx_change':  # 為替変化率の処理
                plot_fx_change_and_save_to_pdf(pdf, result)
                continue

            # 外貨建てと円建ての結果を取得してプロットを作成・保存
            years = result['Foreign_Currency']['File1_result'].columns[:-1]  # 最後の列は「Mean」なので除く
            save_plots_to_pdf(pdf, asset, result, years)

    print(f"PDF saved at: {pdf_file_path}")


def plot_quantiles_and_mean(years, file1_quantiles, file1_mean, file2_quantiles, file2_mean, title, ylabel):
    """
    分位点と平均値のプロットを作成する関数
    
    Parameters:
    -----------
    years : pd.Index
        年ごとのデータを表すインデックス
    file1_quantiles : pd.DataFrame
        ファイル1の分位点データ
    file1_mean : pd.Series
        ファイル1の平均値
    file2_quantiles : pd.DataFrame
        ファイル2の分位点データ
    file2_mean : pd.Series
        ファイル2の平均値
    title : str
        プロットのタイトル
    ylabel : str
        Y軸ラベル
    
    Returns:
    --------
    None
    """
    plt.figure(figsize=(10, 6))
    
    # 分位点のプロット
    for quantile in file1_quantiles.index:
        plt.plot(years, file1_quantiles.loc[quantile], label=f'File1 {quantile}', linestyle='--', marker='o')
        plt.plot(years, file2_quantiles.loc[quantile], label=f'File2 {quantile}', linestyle='-', marker='x')
    
    # 平均値のプロット
    plt.plot(years, file1_mean, label='File1 Mean', color='blue', linewidth=2)
    plt.plot(years, file2_mean, label='File2 Mean', color='red', linewidth=2)
    
    # プロットの設定
    plt.title(title, fontsize=16)
    plt.xlabel('Years', fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.tight_layout()


def save_plots_to_pdf(pdf, asset, result, years):
    """
    外貨建てと円建てのシナリオデータの可視化を行い、PDFに保存する関数
    
    Parameters:
    -----------
    pdf : PdfPages
        PDF書き込み用のオブジェクト
    asset : str
        アセット名
    result : dict
        外貨建てと円建てのリターン結果を含む辞書
    years : pd.Index
        年ごとのデータを表すインデックス
    
    Returns:
    --------
    None
    """
    # 外貨建ての結果
    foreign_result = result['Foreign_Currency']
    file1_foreign = foreign_result['File1_result']
    file2_foreign = foreign_result['File2_result']

    # 円建ての結果
    jpy_result = result['JPY']
    file1_jpy = jpy_result['File1_result']
    file2_jpy = jpy_result['File2_result']

    # プロット作成（外貨建て）
    plot_quantiles_and_mean(
        years, 
        file1_foreign.loc[file1_foreign.index[:-1], years], file1_foreign.loc['Mean', years], 
        file2_foreign.loc[file2_foreign.index[:-1], years], file2_foreign.loc['Mean', years], 
        f'Scenario Comparison (Foreign Currency) for {asset}', 
        'Return'
    )
    pdf.savefig()
    plt.close()

    # プロット作成（円建て）
    plot_quantiles_and_mean(
        years, 
        file1_jpy.loc[file1_jpy.index[:-1], years], file1_jpy.loc['Mean', years], 
        file2_jpy.loc[file2_jpy.index[:-1], years], file2_jpy.loc['Mean', years], 
        f'Scenario Comparison (JPY) for {asset}', 
        'Return'
    )
    pdf.savefig()
    plt.close()


def plot_fx_change_and_save_to_pdf(pdf, fx_change_result):
    """
    為替変化率の可視化を行い、PDFに保存する関数
    
    Parameters:
    -----------
    pdf : PdfPages
        PDF書き込み用のオブジェクト
    fx_change_result : pd.DataFrame
        為替変化率の分位点と平均値を含むデータフレーム
    
    Returns:
    --------
    None
    """
    years = fx_change_result.columns[:-1]  # 最後の列は「Mean」なので除く
    
    # 為替変化率の分位点と平均値
    fx_quantiles = fx_change_result.loc[fx_change_result.index[:-1], years]
    fx_mean = fx_change_result.loc['Mean', years]

    # プロット作成
    plt.figure(figsize=(10, 6))
    
    # 分位点のプロット
    for quantile in fx_quantiles.index:
        plt.plot(years, fx_quantiles.loc[quantile], label=f'{quantile} Quantile', linestyle='--', marker='o')
    
    # 平均値のプロット
    plt.plot(years, fx_mean, label='Mean', color='blue', linewidth=2)
    
    # プロットの設定
    plt.title('FX Change Rate Comparison', fontsize=16)
    plt.xlabel('Years', fontsize=12)
    plt.ylabel('FX Change Rate', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.tight_layout()
    
    # 現在のグラフをPDFの1ページとして追加
    pdf.savefig()
    plt.close()


