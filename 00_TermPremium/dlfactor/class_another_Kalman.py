import numpy as np
from data_processor.data_processor import *
from dlfactor.func_KalmanFilter import TransitionParametersCalculator, DifferentialEquationSolver, MatrixOperations
from dlfactor.support_func_KWmodel import arrange_param_array_to_list

class KalmanFilter:
    def __init__(self, observe_yield, data_setting, setting_bool, params_array, name_list):
        self.observe_yield = observe_yield
        self.params_list = arrange_param_array_to_list(params_array, data_setting, setting_bool)
        self.data_setting = data_setting
        self.setting_bool = setting_bool
        self.name_list = name_list
        self.log_likelihood = 0
        # 状態を格納する辞書を初期化
        self.state_mean_dict = {state_name: [] for state_name in self.name_list}
        self.state_covariance_dict = {state_name: [] for state_name in self.name_list}


    def run_kalman_filter(self):
        state_vector = self.data_setting["state_variable_initial_array"][0]
        state_covariance = MatrixOperations.integral(self.params_list[5], self.params_list[4], integrate_range=[0, 10]) # 積分範囲は[0, 10]

        for t in range(len(self.observe_yield)):
            filtered_state, filtered_covariance = self.predict_state(state_vector, state_covariance) # 1期先予測
            solve_at, solve_bt = self.calc_observation_params() # 状態変数の計算
            conditional_yield = np.dot(solve_bt, state_vector) + solve_at # 1期先予測イールド
            selected_observe_yield, selected_conditional_yield = self.observe_yield.iloc[t, :], conditional_yield # 1期先予測
            Ft, vt, Kt = self.calc_kalman_gain(self, selected_observe_yield, selected_conditional_yield, filtered_covariance, solve_bt) # カルマンゲイン
            state_vector, state_covariance = self.update_state(filtered_state, filtered_covariance, solve_bt, Kt, vt) # フィルタリング値
            self.log_likelihood += self.calc_log_likelihood(vt, Ft) # 対数尤度
            self.store_results(t, filtered_state, filtered_covariance, state_vector, state_covariance) # 結果の保存

        # RTS平滑化を実行
        self.rts_smoother()

        # log_likelihood と更新された状態の平均値および共分散値を返す
        return self.log_likelihood, self.state_mean_dict, self.state_covariance_dict


    def predict_state(self, state_vector, state_covariance):
        conditional_xt = np.dot(self.K_delta_t, state_vector)
        conditional_cov = np.dot(np.dot(self.K_delta_t, state_covariance), self.K_delta_t.T) + self.Q_t
        return conditional_xt, conditional_cov

    def calc_kalman_gain(self, observe_yield, conditional_yield, predicted_covariance, solve_bt):
        vt = observe_yield - conditional_yield
        Ft = np.dot(np.dot(solve_bt, predicted_covariance), solve_bt.T) + self.params_list[6]
        Kt = np.dot(np.dot(predicted_covariance, solve_bt.T), np.linalg.inv(Ft))
        return Ft, vt, Kt

    @staticmethod
    def update_state(predicted_state, predicted_covariance, solve_bt, Kt, vt):
        update_state_ = (predicted_state + np.dot(Kt, vt))
        update_covariance = predicted_covariance - np.dot(np.dot(Kt, solve_bt), predicted_covariance)
        return update_state_, update_covariance

    @staticmethod
    def calc_log_likelihood(vt, Ft):
        log_likelihood = -0.5 * (len(Ft) * np.log(2 * np.pi) + np.log(np.linalg.det(Ft)) + np.dot(np.dot(vt.T, np.linalg.inv(Ft)), vt))
        return log_likelihood

    def calc_observation_params(self):
        differential_equation_solver = DifferentialEquationSolver(self.params_list, self.data_setting)
        solve_at, solve_bt = differential_equation_solver.calc_observation_params()
        return solve_at, solve_bt
    
    def rts_smoother(self):
        n_timesteps = len(self.observe_yield)
        # 平滑化された状態と共分散を格納するための空リストを初期化
        smoothed_state = [None] * n_timesteps
        smoothed_covariance = [None] * n_timesteps

        # 最後のフィルタリングされた状態と共分散を平滑化された最終状態として使用
        smoothed_state[-1] = self.state_dict[self.name_list[0]][-1]  # filtered_stateを参照
        smoothed_covariance[-1] = self.state_covariance_dict[self.name_list[0]][-1]

        # 時間を逆向きにループして平滑化を実行
        for t in reversed(range(n_timesteps - 1)):
            # ゲインの計算
            Ck = np.dot(self.state_covariance_dict["filtered_covariance"][t], np.linalg.inv(self.state_covariance_dict["predicted_covariance"][t + 1]))

            # 平滑化された状態と共分散の計算
            smoothed_state[t] = self.state_mean_dict["filtered_state"][t] + np.dot(Ck, (smoothed_state[t + 1] - self.state_mean_dict["predicted_state"][t + 1]))
            smoothed_covariance[t] = self.state_covariance_dict["filtered_covariance"][t] + np.dot(Ck, (smoothed_covariance[t + 1] - self.state_covariance_dict["predicted_covariance"][t + 1])).dot(Ck.T)

        # 平滑化された状態と共分散をstate_dictに追加
        self.state_dict[self.name_list[2]] = smoothed_state  # smoothed_stateを更新
        self.state_covariance_dict[self.name_list[2]] = smoothed_covariance

    def store_results(self, t, filtered_state, filtered_covariance, state_vector, state_covariance):
        # 結果を適切なリストに追加
        # ここではフィルタリングと予測の状態を保存
        if t == 0:
            # 初期状態の設定
            self.state_dict[self.name_list[0]] = [filtered_state]  # filtered_state
            self.state_dict[self.name_list[1]] = [state_vector]  # predicted_state
            self.state_covariance_dict[self.name_list[0]] = [filtered_covariance]
            self.state_covariance_dict[self.name_list[1]] = [state_covariance]
        else:
            # 後続の状態の追加
            self.state_dict[self.name_list[0]].append(filtered_state)
            self.state_dict[self.name_list[1]].append(state_vector)
            self.state_covariance_dict[self.name_list[0]].append(filtered_covariance)
            self.state_covariance_dict[self.name_list[1]].append(state_covariance)
