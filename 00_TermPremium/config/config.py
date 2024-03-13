"""
KWモデルにおけるハイパラの設定を記載
"""

import numpy as np

hyperparams_dict = {
    "ACM_model" : {
        "data_setting" : {
            "factor_num" : 5, # ファクター数(default : 5)
            "maturities" : 120, # イールドカーブ作成期間 (月次入力(120 : 10年))
            "estimate_term" : "月次", # 月次, 日次 (週次は対象外)
            "choose_date" : "BM", # (月次の場合) データ抽出時点 (BM : 月末, MS : 月初)
            "rx_maturities" : (6, 12, 24, 36, 48, 60, 72, 84, 96, 120), # 保有超過リターンパラメータ推計に使用する時点
            "start_maturity" : 2, # イールドカーブの抽出開始の残存 (2 : 残存2か月以上のデータを推計に使用)
            "plot_maturity" : (12, 24, 36, 48, 60, 72, 84, 96, 108, 120), # 推計結果を可視化する時点
            "graph_date_format" : "%Y%m", # グラフの横軸の表示方法
        },
        "setting_bool" : {
            "subtract_mean_yield_bool" : True, # 平均を差し引いたイールドをパラメータ推計に使用 (Default : True)
            "use_mu_bool" : False, # VARモデルの定数部分 \mu を使用した推計を行うか (Default : False)
            "standardize_eigenvector_bool" : False, # 固有ベクトルのスケール変換有無 (Default : False))
            "standardize_yield_PCs_bool" : True, # 主成分スコアのスケール変換有無 (Defalut : True)
        },
    },
    "KW_model" : {
        "data_setting" : {
            "factor_num" : 3, # 使用するファクター数
            "maturities" : 120, # 満期の最大値(年表示)
            "estimate_term" : "週次", # 週次, 月次
            "Data_term" : "BM", # 月次の場合 データ抽出時点(BM : 月次, MS : 月初)
            "weekday" : 2, # 週次の場合 データ抽出の曜日(月 : 0, ~ 日 : 6)
            "residural_array" : (6, 12, 24, 36, 48, 60, 72, 84, 96, 120), # パラメータ推計に使用する残存年数
            "plot_maturity" : (12, 24, 36, 48, 60, 72, 84, 96, 108, 120), # PDFにイールドを出力するときの残存年数
            "solve_ode_method" : "RK45", # ODEの解放
            "state_variable_initial_array" : [
                np.array([[0], [0], [0]]),
                np.array([[0.005095, 0, 0], [0, 0.01103, 0], [0, 0, 0.02647]])
            ], # 状態変数の初期値設定（不要になります）
            "an_and_bn_init_value" : np.array([0, 0, 0, 0]), # 常微分方程式の初期値
            "param_matrix_num" : 3, # 推計行列の数
            "param_vector_num" : 2, # 推計ベクトルの数
            "graph_date_format" : "%Y%m"
        },
        "setting_bool" : {
            "state_covariance_bool" : False, # 
        },
    },
    "Country" : {
        "US" : {
            "file_path" : 'https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv', # CSVファイルのURL
            "delete_row" : 9, # ダウンロードファイルの上9行は不要
        },
        # "GE" : {
        #     "file_path" : "",
        #     "delete_row" : 9, # ダウンロードファイルの上9行は不要
        # },
        # "EUR_AAA" : {
        #     "file_path" : "",
        #     "delete_row" : 9, # ダウンロードファイルの上9行は不要
        # },
        # "EUR_ALL" : {
        #     "file_path" : "",
        #     "delete_row" : 9, # ダウンロードファイルの上9行は不要
        # },
    },
}
