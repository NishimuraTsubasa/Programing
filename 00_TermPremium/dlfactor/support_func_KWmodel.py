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
    selected_yield = yield_curve.iloc[:, np.array(data_setting["residural_array"]) - 1]
    # 分散を計算
    init_state_covariance = np.cov(selected_yield, rowvar = False, bias = True)

    return init_state_covariance, selected_yield


def matrix_integral(K, Sigma, integrate_range):
    """ 行列表記の非積分関数を積分する関数

    Args:
        K : np.array
            状態変数の定数項 K
        Sigma : np.array
            状態変数の分散部分 
    Returns:
        integrate_matrix : np.array
            積分した行列
    """

    # 各成分の積分を行う関数
    def integrand_matrix_element(s, K, i, j, matrix_function):
        """ 行列の特定の成分に対する非積分関数を返す """
        return matrix_function(s, K, Sigma)[i, j]
    # 各要素を積分する関数
    def integrate_matrix_function(matrix_function, integrate_range, K, Simga):
        """ 指定された積分期間で行列を積分する関数 """
        # 結果の格納用
        matrix_shape = K
        result_matrix = np.zeros(matrix_shape)
        # 積分範囲の指定
        a, b = integrate_range
        # for文で各成分を計算
        for i in range(matrix_shape[1]):
            for j in range(matrix_shape[0]):
                # integrate_matrix_element関数を適用 (package使用)
                result, _ = quad(integrand_matrix_element, a, b, args = (K, Sigma, i, j, matrix_function))
                result_matrix[i, j] = result
        return result_matrix
    # 積分関数の準備
    def matrix_function(s, K, Sigma):
        """ 非積分関数の指定 """
        non_integram_for_cov = np.dot(expm(K * s), np.dot(Sigma, np.dot(Sigma.T, expm(K.T * s))))
        return non_integram_for_cov
    
    # 各成分を積分した結果を格納した行列
    integrate_matrix = integrate_matrix_function(matrix_function, integrate_range, K, Sigma)

    return integrate_matrix
    

def solve_differential_equation(function, remain_term_array, init_matrix, method, args = ()):
    """ 常微分方程式を解く関数（バックワードでやる場合は時点を逆に）
    Args:
        function : function
            常微分方程式
        remain_term_array : np.array
            残存年数の配列
        time_series_initial_array : np.array
            初期値条件
        method : str
            常微分方程式の解き方
        args(tuple, optional) : str
            制約条件 Defaults to ()
    Returns:
        solve : scipy.array
            常微分方程式の結果
    """

    # 常微分方程式を解く
    solve = solve_ivp(
        function, # 常微分方程式の指定
        t_span = [0, np.max(remain_term_array)], # 積分を行う時間範囲
        y0 = init_matrix, # 常微分方程式の初期値
        method = method, # 常微分方程式の解き方(自動で解き方を調整)
        args = args, # 制約条件
        t_eval = remain_term_array # 常微分方程式の推計期間
    )

    # 正しく解けたか確認
    if not solve.success:
        raise Exception("常微分方程式の計算に失敗しました")
    
    return solve


def matrix_exponential_approximate(X):
    """ 行列Xのn次のマクローリン展開を用いた指数関数の近似値を計算する
    Args:
        X : np.array
            行列(3, 3)
    return:
        result : np.array
            行列の指数関数の近似値
    """

    return expm(X) # パッケージによるマクローリン展開


def func_yield_term_order_ode(remain_term, init_matrix, rho, Phi, Sigma, K):
    """ a(n) に関する常微分方程式
    Args:
        remain_term: float
            残存年数 (n)
        time_series_initial_array : list
            b (t, T) に関する初期値を格納したリスト (全てゼロ)
          pho : np.array
            金利モデル ファクター係数
        Phi : np.array
            リスクの市場価格 ファクター係数
        Sigma : np.array
            状態変数の分散
        K : np.array
            状態変数の定数項
    Return:
        dbdt : np.array
            a(n)の常微分方程式の結果
    """

    # 常微分方程式の計算
    dbdt = - rho + np.dot((K - np.dot(Sigma, Phi)).T, init_matrix)
    
    return dbdt

def func_yield_term_constant_ode(rho_0, phi, Sigma, solve_bt):
    """ b(n)に関する常微分方程式
    Args:
        remain_term : float
            残存年数 (T-t)
        time_series_initial_array : list
            a (t, T) , b (t, T) に関する初期値を格納したリスト
        pho_0 : float
            金利モデル 定数項
        Phi: np.array
            リスクの市場価格 ファクター係数
        Sigma : np.array
            状態変数の分散
    Return:
        dadt_array : np.array
            b(n) の常微分方程式の結果
    """

    # 常微分方程式を普通に解いていく
    dadt_array = np.empty(len(solve_bt[0]))
    # 1つずつ解いていく
    for i in range (len(solve_bt[0])):
        bt = solve_bt[:, i]
        dadt = - rho_0 - np.dot(np.dot(bt.T, Sigma), phi) + 1/2 * np.dot(np.dot(np.dot(bt.T, Sigma), Sigma.T), bt)
        dadt_array[i] = dadt

    return dadt_array

def solve_an_bn_differential_equation(init_matrix, rho_0, rho, phi, Phi, Sigma, K):
    """ イールドカーブの微分方程式の解を求める関数

    Args:
        remain_term (np.array): 残存年数 n
        init_matrix (np.array): a(n), b(n) の初期値の行列
        rho_0 (np.array): 定数項
        rho (np.array): (3, 3) 行列
        phi (np.array): (3, 1) ベクトル
        Phi (np.array): (3, 3) 行列
        Sigma (np.array): (3, 3) 行列
        K (np.array): (3, 3) 行列
    Returns:
        np.array: 微分方程式の解
    """
    # 初期値の抽出
    a, b = init_matrix[0], init_matrix[1]

    # 微分方程式の解を計算
    da_dn = - rho_0 - np.dot(np.dot(b.T, Sigma), phi) + 1/2 * np.dot(np.dot(np.dot(b.T, Sigma), Sigma.T), b)
    db_dn = - rho + np.dot((K - np.dot(Sigma, Phi)).T, b)

    # 解の結合
    return np.concatenate((da_dn, db_dn))

#####################################################
# 補助関数
#####################################################
def check_delta_t(data_setting):
    """ 時点の刻み回数を出す関数
    Args:
        data_setting : dict
            ハイパーパラメータの条件を格納した辞書
    Returns:
        delta_t : int
            時点の刻み幅 (どちらかというと回数)
    """

    if data_setting["estimate_term"] == " 月次":
        delta_t = 12
    elif data_setting["estimate_term"] == " 週次":
        # デルタの設定
        delta_t = 52

    return delta_t

def extract_parameters(hyper_param_dict, list_bool):
    """パラメータ配列を適切な形に変換する関数
    """

    # 必要なパラメータ数の整理
    need_param_num = 1 + hyper_param_dict ["factor_num"] * hyper_param_dict ["param_vector_num"] \
                    + hyper_param_dict ["factor_num"] ** 2 * hyper_param_dict ["param_matrix_num"]
    # パラメータの初期値設定
    np.random.seed(1) # 乱数固定
    params = np.random.rand(need_param_num) / 100

    # 必要なパラメータの抽出
    matrix_num = hyper_param_dict ["param_matrix_num"] 
    factor_num= hyper_param_dict ["factor_num"]
    vector_num= hyper_param_dict ["param_vector_num"]

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

    # 辞書に格納
    params_dict = {
        "rho_0" : params_list[0],
        "rho" : params_list[1],
        "phi" : params_list[2],
        "Phi" : params_list[3],
        "Sigma" : params_list[4],
        "K" : params_list[5],
    }

    if list_bool:
        return params_list
    else:
        return params_dict


