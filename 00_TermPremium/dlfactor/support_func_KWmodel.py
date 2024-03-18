import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator
import sympy as sp # マクローリン展開用
from scipy.linalg import expm # マクローリン展開用
from scipy.integrate import quad
from scipy.integrate import solve_ivp


def calc_init_state_covariance(yield_curve, data_setting):
    """ イールドカーブから必要データを抽出して分散を計算 """
    # イールドカーブの抽出
    selected_yield = yield_curve.iloc[:, np.array(data_setting["residual_array"]) - 1]
    # 分散を計算
    init_state_covariance = np.cov(selected_yield, rowvar = False, bias = True)

    return init_state_covariance, selected_yield


def make_init_params_bounds(selected_yield, data_setting, setting_bool):
    """ パラメータ配列を適切な形に変換する関数 """
    # 必要なパラメータの抽出
    matrix_num, vector_num = 3, 2
    factor_num = data_setting["factor_num"]
    # 必要なパラメータ数の整理
    if setting_bool["K_and_Sigma_restrict"]:
        need_param_num = 1 + factor_num * vector_num + factor_num ** 2 * matrix_num - 3/2 * factor_num * (factor_num - 1)  #
    else:
        need_param_num = 1 + factor_num * vector_num + factor_num ** 2 * matrix_num
    need_param_num = int(need_param_num)

    # パラメータの初期値設定
    # np.random.seed(data_setting["random_seed"]) # 乱数固定
    params_array = np.random.rand(need_param_num) * data_setting["init_scale"]
    # 分散の初期値を設定
    init_state_covariance = np.cov(selected_yield, rowvar = False, bias = True).flatten()
    # 後ろに結合
    params_array = np.concatenate((params_array, init_state_covariance))

    # 制約条件(\rho) の追加
    bounds = make_bound_array(setting_bool, len(params_array), (1, 1), start_index = 1, end_index = factor_num)

    return params_array, bounds

def arrange_param_array_to_list(params, data_setting, setting_bool):
    """ 1次元配列をベクトルに変換する関数 """

    # その他のパラメータ
    factor_num, vector_num, matrix_num = data_setting["factor_num"], 2, 3
    if setting_bool["K_and_Sigma_restrict"]:
        matrix_num = 1

    # 結果格納用のリスト
    params_list = []
    for i in range(matrix_num + vector_num + 1):
        if i == 0:
            params_list.append(np.array(params[0 : 1]))
        elif i > 0 and i <= vector_num:
            params_list.append(np.array(params[1 + factor_num * (i - 1) : 1 + factor_num * i]))
            end = 1 + factor_num * i
        else:
            start = end
            end = end + factor_num ** 2
            params_list.append(np.array(params[start:end]).reshape(factor_num, factor_num))

    if setting_bool["K_and_Sigma_restrict"]:
        Sigma = params[end : end + factor_num]
        K = params[end + factor_num: end + int(factor_num * (factor_num + 3) / 2)]
        # 対角成分のみ抽出
        params_list.append(np.diag(Sigma))
        # 下三角行列を復元
        K_ = np.zeros_like(params_list[4])
        # # 下三角行列のインデックスを取得
        tril_indices = np.tril_indices(params_list[4].shape[0])
        # 復元する
        K_[tril_indices] = K
        params_list.append(K_)
        # 最後の部分更新
        end = end + int(factor_num * (factor_num + 3) / 2)

    # 観測方程式の分散共分散行列の追加
    # # 観測方程式の次元数
    try:
        n_dim_obs = len(data_setting["residual_array"])
    except Exception as e:
        n_dim_obs = 1

    params_list.append(params[end:].reshape(n_dim_obs, n_dim_obs))

    return params_list

def make_bound_array(setting_bool, need_param_num, restrict_range, start_index, end_index):
    """ 制約条件を格納したリストを準備 """
    # 制約条件を入力した箱を準備
    bounds = [(-1, 1)] * need_param_num
    # 指定した範囲の要素に対して非正値の制約を設定
    if setting_bool["rho_restrict"]:
        for i in range(start_index, min(end_index + 1, need_param_num)):
            bounds[i] = restrict_range

    return bounds

def calc_term_premium_and_save_result(yield_dict, zero_yield_dict):
    """ 算出した結果をまとめる関数 ("filtered_yield", "smoothed_yield", "fixed-interval_smoothed_yield") """

    # 空の辞書を準備
    term_premium_dict = {}
    # タームプレミアムを計算
    for key, df_yield in yield_dict.items():
        # 差分を計算
        term_premium_dict[key] = df_yield - zero_yield_dict[key]

    return term_premium_dict



