# 必要ライブラリ
import pandas as pd
import numpy as np
import datetime as dt
from numpy import newaxis
import os

# 作成した関数を読み込み
from dlfactor.func_NSSmodel import main_calc_yield_curve # イールドカーブを生成する関数
from data_processor.data_processor import *
from dlfactor.func_ACMmodel import AMC_model_main
from dlfactor.func_KWmodel import *
from dlfactor.another_approch_KWmodel import main_KW_model

def main_run(hyperparams_dict, folder_path, country, model, residual) :
    """ Kim & Wright modelによる推計
    """

    # 訓練期間とテスト期間に分割
    if country == "US" :
        train_test_dict = {
            "train_start_date": dt.datetime(1990, 1, 1),  # 1987, 1, 1
            "train_end_date": dt.datetime(2005, 8, 1),    # 2023, 8, 1 
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
    data_setting, bool_setting = hyperparams_dict[model]["data_setting"], hyperparams_dict[model]["setting_bool"]
    data_setting["residual_array"] = residual
    # csvの格納されたURLの確認
    file_dict = hyperparams_dict["Country"][country]
    # 結果の保存パスを設定
    save_path = set_save_folder_path(data_setting, folder_path, model, country, train_test_dict)
    # パラメータデータの整理
    df_yield_curve = main_calc_yield_curve(data_setting, file_dict, country)

    # 訓練データの抽出
    X_train, _ = split_data(df_yield_curve, train_test_dict, data_setting) # (月次等のデータを抽出)

    # model に基づき推計を実施
    if model == "ACM_model":
        result_dict = AMC_model_main(X_train, data_setting, bool_setting)
        ACM_save_result_to_pdf(save_path, result_dict, data_setting)
    elif model == "KW_model":
        # 結果格納時の辞書key
        name_list = ["filtered_yield", "smoothed_yield", "fixed-interval_smoothed_yield"]
        result_dict, estimate_params = KW_model_main(X_train, data_setting, bool_setting, name_list)

        # # # 別アプローチの検討
        # name_list = ["filtered_state", "predicted_state", "smoothed_state"]
        # result_dict, estimate_params = main_KW_model(X_train, data_setting, bool_setting, name_list)

        # KW_model のみ (パラメータ推計結果)
        save_estimate_params(save_path, estimate_params)
        KW_save_result_to_pdf(save_path, result_dict, data_setting)

    # 結果をExcelに出力
    save_result_to_excel(save_path, result_dict, model)

    print("終了")


if __name__ == "__main__":

    # ハイパラを格納した辞書の読み込み
    from config.config import hyperparams_dict
    # 推計するモデル
    estimate_model = ["KW_model"] # リストに含まれたモデルのみ推計 (ACM_model, KW_model)
    # 出力結果保存用のフォルダパス
    # folder_path = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Programing\00_TermPremium\result"
    folder_path = r"C:\Users\user\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Programing\00_TermPremium\result"

    residual_list = [
        (3, 6, 12, 24, 48, 84, 120),
        (3, 6, 9),
        (12, 24, 36),
        (114, 117, 120),
        (108, 114, 120),
        (96, 108, 120)
    ]

    for model in estimate_model:
        for country, key in hyperparams_dict["Country"].items():
            for residual in residual_list:
                # メイン関数
                main_run(hyperparams_dict, folder_path, country, model, residual)