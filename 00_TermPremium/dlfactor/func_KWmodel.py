import numpy as np
import pandas as pd
from scipy. optimize import minimize
import matplotlib. pyplot as plt
# config.からハイパラの設定を取得
from config.config import hyperparams_dict
from data_processor.data_processor import *
from dlfactor.support_func_KWmodel import *
from pykalman import KalmanFilter
# from pykalman import KalmanFilter # kalman_filter用のパッケージ
from dlfactor.func_KalmanFilter import TransitionParametersCalculator
from dlfactor.func_KalmanFilter import TransitionParametersCalculator
from dlfactor.func_KalmanFilter import DifferentialEquationSolver

def KW_model_main(X_train, data_setting):
    """ KWモデルによるイールドカーブ, タームプレミアム, リスクフリーレートを推計"""

    # パラメータ (初期値) の準備
    params_list = extract_parameters(data_setting, list_bool=True)
    # 観測共分散行列と抽出したイールドカーブ
    init_observed_covariance, selected_yield = calc_init_state_covariance(X_train, data_setting)
    
    # TransitionParametersCalculatorのインスタンス作成
    transition_params_calculator = TransitionParametersCalculator(params_list, data_setting)
    K_delta_t, Q_t = transition_params_calculator.calculate()
    
    # DifferentialEquationSolverのインスタンス作成
    differential_equation_solver = DifferentialEquationSolver(params_list, data_setting)
    solve_at, solve_bt = differential_equation_solver.calc_observation_params()

    # カルマンフィルタの初期パラメータ設定
    kf = KalmanFilter(
        initial_state_mean = data_setting["state_variable_initial_array"][0],  # (初期値) 状態変数の平均値
        initial_state_covariance = data_setting["state_variable_initial_array"][1],  # (初期値) 状態変数の分散
        transition_matrices = K_delta_t,  # 状態方程式の係数 K
        transition_offsets = None,  # 状態方程式の定数項 (KW_model: 0ベクトル)
        transition_covariance = Q_t,  # 状態方程式の分散 Q_t
        observation_matrices = solve_bt,  # 観測方程式の係数 B(n)
        observation_offsets = solve_at,  # 観測方程式の定数項 A(n)
        observation_covariance = init_observed_covariance,  # 観測方程式の共分散
    )

    # EMアルゴリズムによる学習
    EM_kf = kf.em(selected_yield, n_iter = 10)
    # ハイパーパラメータ更新のフィルタリング値・スムージング値
    em_filtered_state_mean, em_filtered_state_covariance = EM_kf.filter(selected_yield)
    em_smoothed_state_mean, em_smoothed_state_covariance = EM_kf.smooth(selected_yield)

    # ハイパーパラメータ推計後のイールド推計値
    # # スムージングによる推計結果
    em_pred_yield = np.dot(em_smoothed_state_mean, EM_kf.observation_matrices.T)
    # # フィルタリング結果
    em_pred_yield_filtered = np.dot(em_filtered_state_mean, EM_kf.observation_matrices.T)

    # # 平滑化の実施
    predicted_yield = np.empty(selected_yield.shape)
    # # 初期値の設定 (バックワードでの推計)
    current_state, current_covariance = em_smoothed_state_mean[-1], em_smoothed_state_covariance[-1]
    # # バックワードでの推計
    for t in range(len(selected_yield)):
        # 1時点前の状態変数の平均・分散共分散行列を計算
        current_state, current_covariance = EM_kf.filter_update(current_state, current_covariance, obsevation = None)  
        # 予測値の推計結果
        predicted_yield[t] = EM_kf.observation_matrices.dot(current_state)






def calc_yield_curve(params_list, Sigma_t, data_setting):
    """ イールドカーブを推計する関数
    Args:
        remain_term_array : np.array
            残存年数を格納した配列
        params_list : list
            固有パラメータを格納したリスト
        state_vector : np.array
            状態変数 (3, 1)行列
        hyperparam_dict : dict
            ハイパラを格納した辞書
    Return:
        yield_curve : pd.DataFrame
            推計されたイールドカーブ
        solve_bt : scipy.array
            常微分方程式 b(n) の結果
    """

    # 残存年数の配列
    remain_term_array = make_estimate_maturity_array(data_setting)
    # methodの確認
    method = data_setting["solve_ode_method"]
    # 必要なパラメータの設定
    rho_0, phi, rho, Phi, Sigma, K = params_list

    # b(n)を計算
    solve_bt = solve_differential_equation(
        func_yield_term_order_ode, # 常微分方程式
        remain_term_array, # 残存年数
        data_setting["an_and_bn_init_value"][1:], # b(n)の初期値
        method, # 常微分方程式の解法
        args = (rho, Phi, Sigma, K) # 固有パラメータ
    )
    # b(n)の結果をもとにa(n)を計算
    solve_at = func_yield_term_constant_ode(rho_0, phi, Sigma_t, solve_bt.y)
    # 常微分方程式の結果を基にイールドカーブを復元
    yield_curve = - (solve_at + np.diag(np.dot(solve_bt.y.T, Sigma_t), solve_bt.y)) / remain_term_array
    # B(n)の計算
    solve_bt = - (solve_bt.y / remain_term_array).T[data_setting["residural_array"] - 1]

    return yield_curve, solve_at, solve_bt # B(n)を出力する設定


def kalman_function(observe_yield, initial_state_list, data_setting, params_list):
    """ カルマンフィルターの実行を行う関数
    
    Args:
        observe_yield_array (np.array): 観測されたイールドカーブの配列。
        remain_term (np.array): 残存期間。
        initial_state_list (list): 状態ベクトルと共分散の初期値が格納されたリスト。
        hyper_param_dict (dict): ハイパーパラメータを格納した辞書。
        params_list (list): モデルパラメータのリスト。
        var_eps (float): 観測ノイズの分散。

    Returns:
        tuple: 対数尤度、予測状態変数の配列、予測状態共分散の配列、フィルター済み状態変数の配列、
               フィルター済み状態共分散の配列を含むタプル。
    """
    
    # ハイパーパラメータの辞書からパラメータを選択するための配列を作成
    choose_array = np.array(data_setting['residural_array']) - 1
    # 初期状態の設定
    state_vector, state_covariance = initial_state_list
    # 
    K_delta_t, Q_t = calc_K_delta_t_and_Q_t(params_list, data_setting, integrate_range = [0, 10])
    # 対数尤度の初期値
    log_likelihood = 0
    
    # カルマンフィルタリングの各ステップを実行
    for t in range(len(observe_yield)):
        # Step 1: 状態変数のフィルタリング
        filtered_state, filtered_covariance = predict_state(state_vector, state_covariance, K_delta_t, Q_t)
        
        # Step 2: イールドの予測
        conditional_yield, solve_bt = calc_yield_curve(params_list, filtered_state, data_setting)

        # Step 3 : 状態変数の更新に必要な変数
        # # イールドの抽出
        selected_observe_yield, selected_conditional_yield = observe_yield.iloc[t, choose_array], conditional_yield[t, choose_array]
        Ft, vt, Kt = calc_kalman_gain(
            selected_observe_yield, selected_conditional_yield, filtered_covariance, solve_bt, params_list
            )

        # Step 4: 状態変数の更新
        state_vector, state_covariance = update_state(
            filtered_state, filtered_covariance, solve_bt, Kt, vt
            )
        
        # Step 5: 対数尤度の更新
        log_likelihood += calc_log_likelihood(vt, Ft)
        
        # # 結果の格納
        if t != 0:
            # フィルタリングされた状態変数
            filterd_state_variable = np.append(filterd_state_variable, filtered_state)
            filterd_state_covariance = np.append(filterd_state_covariance, filtered_covariance)
            # 予測された状態変数
            predicted_state_variable = np.append(predicted_state_variable, state_vector)
            predicted_state_covariance = np.append(predicted_state_covariance, state_covariance)
        else:
            # フィルタリングされた状態変数
            filterd_state_variable = filtered_state
            filterd_state_covariance = filtered_covariance
            # 予測された状態変数
            predicted_state_variable = state_vector
            predicted_state_covariance = state_covariance 

    # 結果を辞書で格納
    state_variable_dict = {
        "filtered_state" : filterd_state_variable,
        "filtered_covariance" : filterd_state_covariance,
        "predicted_state" : predicted_state_variable,
        "predicted_covariance" : predicted_state_covariance
    }

    # 結果のタプルを返す
    return log_likelihood, state_variable_dict


def minus_likelihood(params_list):
    """ 対数尤度関数のマイナス倍を返す関数 """


def calc_log_likelihood(vt, Ft):
    """ 対数尤度関数を計算する関数
    Args:
        vt : np.array
            イールドカーブの誤差項
        Ft : np.array
            イールドカーブの誤差項の分散
    Return:
        log_likelihood : np.array
            対数尤度関数
    """

    # 対数尤度関数を計算
    log_likelihood = -1 / 2 * (len(vt) * np.log(2 * np.pi) + np.log(np.linalg.det(Ft)) + np.dot(np.dot(vt.T, np.linalg.inv(Ft)), vt))

    return log_likelihood


def calc_K_delta_t_and_Q_t(params_list, data_setting, integrate_range = [0, 10]):
    """ 固定値の計算 (K_delta_t, Q_t)
    Args :
        param_list : list
            ハイパラを格納したリスト
        data_setting : dict
            設定を格納したリスト
    Returns :
        K_delta_t : np.array
            状態変数の定数項部分
        Q_t : np.array
            状態変数の誤差項の部分の分散 
    """
    # delta_tの確認
    delta_t = check_delta_t(data_setting)
    # 状態変数の更新部分(K_delta_t)
    K_delta_t = matrix_exponential_approximate(-params_list[5] / delta_t)
    # 状態変数の分散部分
    Q_t = matrix_integral(-params_list[5], params_list[4], integrate_range)

    return K_delta_t, Q_t

def predict_state(state_vector, state_covariance, K_delta_t, Q_t):
    """ 状態変数の予測ステップを実行する """
    # 必要な部分の計算

    # # 状態変数 x_(t|t-\delta{t}) の1期先予測値
    conditional_xt = np.dot(K_delta_t, state_vector)
    # # 状態変数の分散 \Sigma_(t|t-\delta{t}) 1期先予測値
    conditional_cov = np.dot(np.dot(K_delta_t, state_covariance), K_delta_t) + Q_t
    
    return conditional_xt, conditional_cov

def calc_kalman_gain(observe_yield, conditional_yield, predicted_covariance, solve_bt, params_list):
    """ 状態変数の更新に必要な変数の計算 """
    #　観測誤差の計算
    vt = observe_yield - conditional_yield
    # 観測誤差の標準偏差
    Ft = np.dot(np.dot(solve_bt, predicted_covariance), solve_bt.T) + params_list[6] # 観測誤差の誤差項分散
    # カルマンゲインの計算
    Kt = np.dot(np.dot(predicted_covariance, solve_bt.T), np.linalg.inv(Ft))

    return Ft, vt, Kt

def update_state(predicted_state, predicted_covariance, solve_bt, Kt, vt):
    """ 状態変数の更新ステップを実行する """
    # 状態変数の更新
    update_state_ = (predicted_state + np.dot(Kt, vt))
    # 状態変数の分散の更新
    update_covariance = predicted_covariance - np.dot(np.dot(Kt, solve_bt), predicted_covariance)

    return update_state_, update_covariance
