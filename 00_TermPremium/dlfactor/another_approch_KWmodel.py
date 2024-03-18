import pandas as pd
import numpy as np
import copy
from data_processor.data_processor import *
from dlfactor.class_another_Kalman import KalmanFilter
from dlfactor.func_KalmanFilter import DifferentialEquationSolver
from dlfactor.support_func_KWmodel import arrange_param_array_to_list, make_init_params_bounds
from scipy.optimize import minimize


class KWModel:
    def __init__(self, X_train, data_setting, setting_bool, name_list):
        self.X_train = X_train
        self.data_setting = data_setting
        self.setting_bool = setting_bool
        self.name_list = name_list
        self.selected_yield = X_train.iloc[:, np.array(data_setting["residual_array"]) - 1]
        self.estimate_params_array = self.parameter_estimation()
        self.state_mean_dict = self.calc_state_vector()
        self.result_dict = self.calc_estimate_yield()

    def parameter_estimation(self):
        # パラメータ推定の実装
        param_array, bounds = make_init_params_bounds(self.selected_yield, self.data_setting, self.setting_bool)
        result = minimize(
            self.objective_function,
            x0 = param_array,
            args = (self.selected_yield, self.data_setting, self.setting_bool, self.name_list),
            bounds = bounds,
            method = self.data_setting["log_likelihood_method"],
            options={"maxiter": self.data_setting["iteration_count"]}
        )
        return result.x

    def objective_function(self, params_array, observe_yield, data_setting, setting_bool, name_list):
        # 目的関数の実装
        kf = KalmanFilter(observe_yield, data_setting, setting_bool, params_array, name_list)
        log_likelihood, _, _ = kf.run_kalman_filter()
        return -log_likelihood

    def calc_state_vector(self):
        # 状態変数の計算
        kf = KalmanFilter(self.selected_yield, self.data_setting, self.setting_bool, self.estimate_params_array)
        _, state_mean_dict, _ = kf.run_kalman_filter()
        return state_mean_dict

    def calc_estimate_yield(self):
        # イールド推計
        differential_equation_solver = DifferentialEquationSolver(self.estimate_params_array, self.data_setting)
        solve_at, solve_bt = differential_equation_solver.calc_observation_params()
        result_dict = {}
        for key, state_mean in self.state_mean_dict.items():
            result_dict[key] = np.dot(solve_bt, state_mean) + solve_at
        return result_dict

    def calc_term_premium_and_save_result(self):
        # タームプレミアム計算
        zero_params_array = self.adjust_zero_params(copy.deepcopy(self.estimate_params_array))
        zero_result_dict = self.calc_estimate_yield(zero_params_array)
        term_premium_dict = {}
        for key in self.result_dict.keys():
            term_premium_dict[key] = self.result_dict[key] - zero_result_dict[key]
        return term_premium_dict

    def adjust_zero_params(self, params):
        # ゼロパラメータの調整
        params[4 : 4 + self.data_setting["factor_num"]] = np.zeros(self.data_setting["factor_num"])
        params[4 + self.data_setting["factor_num"]: 4 + 2 * self.data_setting["factor_num"]**2] = np.zeros(self.data_setting["factor_num"]**2)
        return params

    def run(self):
        # 全体の処理を実行し、結果を整理して返す
        term_premium_dict = self.calc_term_premium_and_save_result()
        final_result_dict = {
            "result_yield": self.selected_yield,
            "estimate_yield": self.result_dict,
            "term_premium": term_premium_dict,
            # "estimate_rf_rate"の処理が必要であればここに追加
        }
        return final_result_dict





##################################################################################
def main_KW_model(X_train, data_setting, setting_bool, name_list):
    """ 別アプローチでの方法 """
    # イールドの抽出
    selected_yield = X_train.iloc[:, np.array(data_setting["residual_array"]) - 1]
    # システムパラメータの最適化
    estimate_params_array =  parameter_estimation(selected_yield, data_setting, setting_bool, name_list)
    # 状態変数の出力
    state_mean_dict = calc_state_vector(selected_yield, data_setting, setting_bool, estimate_params_array, name_list)
    # イールドの予測
    result_dict = calc_estimate_yield(state_mean_dict, data_setting, estimate_params_array)

    # リスクゼロバージョン
    zero_params = arrange_param_array_to_list(estimate_params_array, data_setting, setting_bool).copy()
    zero_params[2], zero_params[3] = np.zeros(data_setting["factor_num"]), np.zeros((data_setting["factor_num"], data_setting["factor_num"]))
    # リストに戻す
    zero_params_array = restore_params_from_list(zero_params)
    # リスクフリー・イールドの予測
    zero_result_dict = calc_estimate_yield(state_mean_dict, data_setting, zero_params_array)

    # タームプレミアムの計算
    term_premium_dict = calc_term_premium_and_save_result(result_dict, zero_result_dict)

    # 結果の保存
    result_dict = {}
    for name in name_list:
        result_dict[name] = {
            "result_yield" : selected_yield, # イールドカーブ
            "estimate_yield" : result_dict[name], # イールド推計結果
            "term_premium" : term_premium_dict[name], # タームプレミアム推計結果
            "estimate_rf_rate" : zero_result_dict[name] # リスクフリー・イールド推計結果
        }

    return result_dict, arrange_param_array_to_list(estimate_params_array, data_setting, setting_bool)


def calc_estimate_yield(state_mean_dict, data_setting, estimate_params_array):
    """ イールドの推計結果を格納 """

    # DifferentialEquationSolverのインスタンス作成
    differential_equation_solver = DifferentialEquationSolver(estimate_params_array, data_setting)
    solve_at, solve_bt = differential_equation_solver.calc_observation_params()
    # 推計結果の保存
    result_dict = {}
    for key, state_mean in state_mean_dict.items():
        yield_list = np.empty((len(state_mean), solve_bt.shape[0]))
        for t, state in enumerate(state_mean):
            yield_list[t] = np.append(yield_list, np.array([np.dot(solve_bt, state) + solve_at]), axis = 0)
        result_dict[key] = np.dot(solve_bt, state) + solve_at

    return result_dict


def calc_state_vector(selected_yield, data_setting, setting_bool, estimate_params_array, name_list):
    """ 状態変数を計算する関数 """
    # カルマンフィルターのインスタンス化
    kf = KalmanFilter(selected_yield, data_setting, setting_bool, estimate_params_array, name_list)
    # 状態変数の出力
    _, state_mean_dict, _ = kf.run_kalman_filter()

    return state_mean_dict

def parameter_estimation(selected_yield, data_setting, setting_bool, name_list):
    """ システムパラメータを推計する関数 """
    # システムパラメータの設定
    param_array, bound = make_init_params_bounds(selected_yield, data_setting, setting_bool)
    # scipyによる対数尤度最大化
    result = minimize(
        objective_function, # 目的関数
        x0 = param_array, # パラメータの初期化
        args = (selected_yield, data_setting, setting_bool, name_list), # 固定パラメータ
        bounds = bound, # 制約条件
        options = {"maxiter" : data_setting["iteration_count"]}
    )
    # # 結果をリストに変換
    # result_list = arrange_param_array_to_list(result.x, data_setting, setting_bool)

    return result.x


def objective_function(params_array, observe_yield, data_setting, setting_bool, name_list):
    """ 対数尤度の関数 """
    # try:
    #     kf = KalmanFilter(observe_yield, data_setting, setting_bool, params_array, name_list)
    #     log_likelihood, _, _ = kf.run_kalman_filter()
    #     print(log_likelihood)
    #     return -log_likelihood  # 対数尤度のマイナス倍を最小化
    # except Exception as e:
    #     print(f"計算失敗: {e}")
    #     return np.inf

    kf = KalmanFilter(observe_yield, data_setting, setting_bool, params_array, name_list)
    log_likelihood, _, _ = kf.run_kalman_filter()
    print(log_likelihood)
    return -log_likelihood  # 対数尤度のマイナス倍を最小化


def restore_params_from_list(params_list):
    """ ベクトルや行列を含むリストから1次元配列を復元する関数 """

    restored_params = []

    for item in params_list:
        if item.ndim == 1:  # ベクトルの場合
            restored_params.extend(item)
        elif item.ndim == 2:  # 行列の場合
            if np.array_equal(item, np.diag(np.diag(item))):  # 対角行列の場合
                restored_params.extend(np.diag(item))
            elif np.allclose(item, np.tril(item)):  # 下三角行列の場合
                restored_params.extend(item[np.tril_indices(item.shape[0])])
            else:  # 一般的な行列の場合
                restored_params.extend(item.flatten())
        else:
            raise ValueError("Unsupported array dimensions: {}".format(item.ndim))

    return np.array(restored_params)

def calc_term_premium_and_save_result(yield_dict, zero_yield_dict):
    """ 算出した結果をまとめる関数 ("filtered_yield", "smoothed_yield", "fixed-interval_smoothed_yield") """

    # 空の辞書を準備
    term_premium_dict = {}
    # タームプレミアムを計算
    for key, df_yield in yield_dict.items():
        # 差分を計算
        term_premium_dict[key] = df_yield - zero_yield_dict[key]

    return term_premium_dict