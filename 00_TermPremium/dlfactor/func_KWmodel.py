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
from dlfactor.func_KalmanFilter import TransitionParametersCalculator, DifferentialEquationSolver, MatrixOperations

def KW_model_main(X_train, data_setting, setting_bool, name_list):
    """ KWモデルによるイールドカーブ, タームプレミアム, リスクフリーレートを推計"""

    # 観測共分散行列と抽出したイールドカーブ
    _, selected_yield = calc_init_state_covariance(X_train, data_setting)
    # # システムパラメータの推計
    estimate_params = estimate_params_list(
        selected_yield, data_setting, setting_bool, iteration_count = data_setting["iteration_count"]
        )

    # Kalman Filter のインスタンス化
    kf = kalman_filter(estimate_params, data_setting)
    # イールド推計結果
    result_yield_dict = kalman_smoothing(selected_yield, kf, name_list)

    # ゼロイールド版 (Term Premium 用)
    zero_params = estimate_params.copy()
    # カルマンフィルターの計算
    # # リスクの市場価格 (phi, Phi)をゼロに変換 (rho_0, rho, phi, Phi, Sigma, K, state_covariance)
    zero_params[2], zero_params[3] = np.zeros(data_setting["factor_num"]), np.zeros((data_setting["factor_num"], data_setting["factor_num"]))
    # Kalman Filter のインスタンス化
    zero_kf = kalman_filter(zero_params, data_setting)
    # リスクフリーなイールド推計結果
    result_zero_yield_dict = kalman_smoothing(selected_yield, zero_kf, name_list)

    # タームプレミアムの計算
    term_premium_dict = calc_term_premium_and_save_result(result_yield_dict, result_zero_yield_dict)

    # 結果の保存
    result_dict = {}
    for name in name_list:
        result_dict[name] = {
            "result_yield" : selected_yield, # イールドカーブ
            "estimate_yield" : result_yield_dict[name], # イールド推計結果
            "term_premium" : term_premium_dict[name], # タームプレミアム推計結果
            "estimate_rf_rate" : result_zero_yield_dict[name] # リスクフリー・イールド推計結果
        }

    return result_dict, estimate_params


def estimate_params_list(selected_yield, data_setting, setting_bool, iteration_count):
    """ システムパラメータを推計する関数 """
    # 異なる初期値での最適化を実行
    best_solution = None
    best_value = np.inf

    for count in range(data_setting["init_value_try_count"]):
        # ランダムに配列を作成
        param_array, bound = make_init_params_bounds(selected_yield, data_setting, setting_bool)
        # scipyによる最適化
        result = minimize(
            log_likelihood, # 最適化関数
            x0 = param_array, # パラメータ初期値
            args = (data_setting, setting_bool, selected_yield),
            bounds = bound, # 制約条件
            method = data_setting["log_likelihood_method"], # 最適化方法
            options = {"maxiter" : iteration_count, # # イテレーション数
                    'verbose': 2} # 最適化の進行状況
        )
        # 試行回数の確認
        print(f"try {count + 1} result : {result.success}")

        # 最適化の確認
        if result.fun < best_value: # result.success and
            best_value = result.fun
            best_solution = result.x

    # リスト形式に変換して出力
    estimate_params = arrange_param_array_to_list(best_solution, data_setting, setting_bool)

    return estimate_params


def log_likelihood(params_array, data_setting, setting_bool, selected_yield):
    """ KWモデルによるイールドカーブ, タームプレミアム, リスクフリーレートを推計 """

    # パラメータのリスト
    params_list = arrange_param_array_to_list(params_array, data_setting, setting_bool)

    # try:
    #     # カルマンフィルターのインスタンス設定
    #     kf = kalman_filter(params_list, data_setting)
    #     # EMアルゴリズムによるパラメータの最適化
    #     kf = kf.em(selected_yield, n_iter = 3)
    #     # カルマンフィルターにおける対数尤度を計算
    #     lk = kf.loglikelihood(selected_yield)
    #     # 数値計算
    #     print(f"対数尤度 : {lk}")
    #     return -lk
    # except Exception as e:
    #     print(f"計算失敗: {e}")
    #     return np.inf # 失敗した場合は大きなペナルティを課す

    try:
        # カルマンフィルターのインスタンス設定
        kf = kalman_filter(params_list, data_setting)
        # # EMアルゴリズムによるパラメータの最適化
        # kf = kf.em(selected_yield, n_iter = 3)
        # カルマンフィルターにおける対数尤度を計算
        lk = kf.loglikelihood(selected_yield)
        # # 数値計算
        # print(f"対数尤度 : {lk}")
    except np.linalg.LinAlgError as e:
        if 'not positive definite' in str(e):
            # print("正定値行列でないため、処理をスキップします。")
            lk = -1000000000000

    return -lk


def kalman_filter(params_list, data_setting):
    """" カルマンフィルターによる推計を行う関数 """

    # 観測方程式の分散初期値
    init_state_covariance = MatrixOperations.integral(
        params_list[5], params_list[4], integrate_range = [0, 10]
    )

    # TransitionParametersCalculatorのインスタンス作成
    transition_params_calculator = TransitionParametersCalculator(params_list, data_setting)
    K_delta_t, Q_t = transition_params_calculator.calculate()
    # DifferentialEquationSolverのインスタンス作成
    differential_equation_solver = DifferentialEquationSolver(params_list, data_setting)
    solve_at, solve_bt = differential_equation_solver.calc_observation_params()

    # カルマンフィルタの初期パラメータ設定
    kf = KalmanFilter(
        initial_state_mean = data_setting["state_variable_initial_array"][0], # (初期値) 状態変数の平均値
        initial_state_covariance = init_state_covariance, # (初期値) 状態変数の分散
        transition_matrices = K_delta_t, # 状態方程式の係数 K
        transition_offsets = None, # 状態方程式の定数項 (KW_model: 0ベクトル)
        transition_covariance = Q_t, # 状態方程式の分散 Q_t
        observation_matrices = solve_bt, # 観測方程式の係数 B(n)
        observation_offsets = solve_at, # 観測方程式の定数項 A(n)
        observation_covariance = params_list[6], # 観測方程式の共分散
    )

    return kf


def kalman_smoothing(selected_yield, kf, name_list):
    """ Rauch–Tung–Striebeによる固定区間平滑化 """

    # ここは必要かどうか要検討
    # kf = kf.em(selected_yield, n_iter = 5)
    yield_result_list = []

    # ハイパーパラメータ更新のフィルタリング値・スムージング値
    em_filtered_state_mean, em_filtered_state_covariance = kf.filter(selected_yield)
    em_smoothed_state_mean, em_smoothed_state_covariance = kf.smooth(selected_yield)

    # ハイパーパラメータ推計後のイールド推計値
    # # フィルタリング結果
    yield_result_list.append(np.dot(kf.observation_matrices, em_filtered_state_mean.T).T + kf.observation_offsets)
    # # スムージングによる推計結果
    yield_result_list.append(np.dot(em_smoothed_state_mean, kf.observation_matrices.T) + kf.observation_offsets)

    # # 平滑化の実施
    predicted_yield = np.empty(selected_yield.shape)
    # # 初期値の設定 (バックワードでの推計)
    current_state, current_covariance = em_smoothed_state_mean[-1], em_smoothed_state_covariance[-1]
    # # バックワードでの推計
    for t in range(len(selected_yield)):
        # 1時点前の状態変数の平均・分散共分散行列を計算
        current_state, current_covariance = kf.filter_update(current_state, current_covariance, observation = None)
        # 予測値の推計結果
        predicted_yield[t] = kf.observation_matrices.dot(current_state) + kf.observation_offsets # 定数項部分も追加
    # 結果の格納
    yield_result_list.append(predicted_yield)

    # 結果格納用のリスト
    result_yield_dict = {}
    for i, df in enumerate(yield_result_list):
        result_yield_dict[name_list[i]] = pd.DataFrame(df, index = selected_yield.index, columns = selected_yield.columns)

    return result_yield_dict

