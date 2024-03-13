# 必要ライブラリ
import pandas as pd
import numpy as np
import datetime as dt
from numpy import newaxis
import os
import matplotlib. pyplot as plt
import matplotlib. dates as mdates
from matplotlib. backends. backend_pdf import PdfPages
# 作成した関数を読み込み
from dlfactor.func_NSSmodel import main_calc_yield_curve # イールドカーブを生成する関数
from data_processor.data_processor import *
from dlfactor.func_ACMmodel import AMC_model_main
from dlfactor.func_KWmodel import *

def main_run(hyper_param_dict, folder_path, country, model) :
    """ Kim & Wright modelによる推計
    """

    # 訓練期間とテスト期間に分割
    if country == "US" :
        train_test_dict = {
            "train_start_date": dt.datetime(1987, 1, 1),  # 1987, 1, 1
            "train_end_date": dt.datetime(2023, 8, 1),    # 2023, 8, 1 
            "test_start_date": dt.datetime(2013, 1, 1),
            "test_end_date": dt.datetime(2022, 8, 1),
        }
    elif country == "GE" :
        train_test_dict = {
            "train_start_date": dt.datetime(1987, 1, 1),  # 1987, 1, 1
            "train_end_date": dt.datetime(2023, 8, 1),    # 2023, 8, 1 
            "test_start_date": dt.datetime(2013, 1, 1),
            "test_end_date": dt.datetime(2022, 8, 1),
        },
    elif country == "EUR_AAA" or country == "EUR_ALL":
        train_test_dict = {
            "train_start_date": dt.datetime(2004, 8, 1),  # 1987, 1, 1
            "train_end_date": dt.datetime(2023, 8, 1),    # 2023, 8, 1 
            "test_start_date": dt.datetime(2013, 1, 1),
            "test_end_date": dt.datetime(2022, 8, 1),
        }

    # データセッティング
    data_setting, bool_setting = hyper_param_dict[model]["data_setting"], hyper_param_dict[model]["setting_bool"]
    # csvの格納されたURLの確認
    file_dict = hyper_param_dict["Country"][country]
    # 結果の保存パスを設定
    save_path = set_save_folder_path(folder_path, model, country, train_test_dict)
    # パラメータデータの整理
    df_yield_curve = main_calc_yield_curve(data_setting, file_dict, country)

    # 訓練データの抽出
    X_train, _ = split_data(df_yield_curve, train_test_dict, data_setting) # (月次等のデータを抽出)

    # model に基づき推計を実施
    if model == "ACM_model":
        result_dict = AMC_model_main(X_train, data_setting, bool_setting)
    elif model == "KW_model":
        result_dict = KW_model_main(X_train, data_setting)

    print("a")



if __name__ == "__main__":

    # ハイパラを格納した辞書の読み込み
    from config.config import hyperparams_dict
    # 推計するモデル
    estimate_model = ["KW_model"] # リストに含まれたモデルのみ推計 (ACM_model, KW_model)
    # 出力結果保存用のフォルダパス
    folder_path = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\02_FT勉強会\2023年度\研究開発（親会社）\02_下期\code\result"

    for model in estimate_model:
        for country, key in hyperparams_dict["Country"].items():
            # メイン関数
            main_run(hyperparams_dict, folder_path, country, model)