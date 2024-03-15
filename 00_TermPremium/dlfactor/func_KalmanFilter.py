import numpy as np
import sys
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.integrate import quad

class MatrixOperations:
    """行列操作を扱うクラス"""

    @staticmethod
    def exponential_approximate(X):
        """行列Xの指数関数の近似値を計算する"""
        return expm(X)

    @staticmethod
    def integral(K, Sigma, integrate_range):
        """ 行列の積分を行う """

        def matrix_function(s, K, Sigma):
            """積分対象の関数"""
            return np.dot(expm(K * s), np.dot(Sigma, np.dot(Sigma.T, expm(K.T * s))))

        def integrate_element(i, j):
            """行列の要素を積分する"""
            integrand = lambda s: matrix_function(s, K, Sigma)[i, j]
            result, _ = quad(integrand, *integrate_range)
            return result

        shape = K.shape
        integrate_matrix = np.zeros(shape)
        for i in range(shape[0]):
            for j in range(shape[1]):
                integrate_matrix[i, j] = integrate_element(i, j)

        return integrate_matrix

class TransitionParametersCalculator:
    """状態遷移パラメータの計算を行うクラス"""

    def __init__(self, params_list, data_setting):
        self.params_list = params_list
        self.data_setting = data_setting

    def calculate(self):
        """ 状態遷移パラメータ(K_delta_t, Q_t)の計算 """
        try:
            if self.data_setting["estimate_term"] == "週次":
                delta_t = 1 / 52
            elif self.data_setting["estimate_term"] == "月次":
                delta_t = 1 / 12
        except Exception as e:
            print("\delta_t の設定でエラー")
            sys.exit(1)

        K = self.params_list[5] * delta_t
        Sigma = self.params_list[4]
        integrate_range = [0, delta_t] # 積分範囲

        K_delta_t = MatrixOperations.exponential_approximate(K)
        Q_t = MatrixOperations.integral(K, Sigma, integrate_range)

        return K_delta_t, Q_t

class DifferentialEquationSolver:
    def __init__(self, params_list, data_setting):
        self.params_list = params_list
        self.data_setting = data_setting

    def make_estimate_maturity_array(self):
        # 1年を12ヶ月として、10年分の月次データを生成します。
        maturity_array = np.arange(1, self.data_setting["maturities"] + 1)[np.newaxis:] / (self.data_setting["maturities"] / 10)
        return maturity_array

    def solve_an_bn_differential_equation(self, t, init_matrix):
        a, b = init_matrix[0], init_matrix[1:]
        rho_0, rho, phi, Phi, Sigma, K, state_covariance = self.params_list
        da_dt = - rho_0 - np.dot(np.dot(b.T, Sigma), phi) + 0.5 * np.dot(np.dot(np.dot(b.T, Sigma), Sigma.T), b)
        db_dt = - rho + np.dot((K - np.dot(Sigma, Phi)).T, b)
        return np.concatenate((da_dt, db_dt))

    def solve_differential_equation(self, remain_term_array, init_matrix):
        method = self.data_setting["solve_ode_method"]

        solution = solve_ivp(
            self.solve_an_bn_differential_equation,
            t_span = [0, np.max(remain_term_array)],
            y0 = init_matrix,
            method = method,
            t_eval = remain_term_array
        )
        if not solution.success:
            raise Exception("常微分方程式の計算に失敗しました。")
        else:
            print("常微分方程式の計算に成功しました")
        return solution

    def calc_observation_params(self):
        remain_term_array = np.array(self.data_setting["residual_array"]) / 12
        remain_term_array_reshaped = remain_term_array.reshape(-1, 1)
        init_matrix = self.data_setting["an_and_bn_init_value"]
        solution = self.solve_differential_equation(remain_term_array, init_matrix)
        solve_at = -solution.y[0, :] / remain_term_array # 観測方程式の定数項
        solve_bt = -solution.y[1:, :].T / remain_term_array_reshaped  # 観測方程式の係数（各状態変数に対する）

        # 検証用
        test_array = np.arange(1, (max(self.data_setting["residual_array"]) + 1)) / max(self.data_setting["residual_array"]) * 10
        test_solution = self.solve_differential_equation(test_array, init_matrix)
        test_solve_at = -test_solution.y[0, np.array(self.data_setting["residual_array"]) - 1] / remain_term_array  # 観測方程式の定数項
        test_solve_bt = -test_solution.y[1:, np.array(self.data_setting["residual_array"]) - 1].T / remain_term_array_reshaped # 観測方程式の係数（各状態変数に対する）

        # return solve_at, solve_bt
        return test_solve_at, test_solve_bt


#####################################################
# old
#####################################################
# class DynamicKalmanFilter(KalmanFilter):
#     def __init__(self, *args, **kwargs):
#         super(DynamicKalmanFilter, self).__init__(*args, **kwargs)
#         self.params_list = kwargs.get('params_list')
#         self.data_setting = kwargs.get('data_setting')
#         self.solver = DifferentialEquationSolver(self.params_list, self.data_setting)

#     def filter_update(self, filtered_state_mean, filtered_state_covariance, observation=None):
#         solve_at, solve_bt = self.solver.calc_observation_params(filtered_state_covariance)
#         self.observation_matrices = solve_bt
#         self.observation_offsets = solve_at
#         return super(DynamicKalmanFilter, self).filter_update(filtered_state_mean, filtered_state_covariance, observation)
    
# class EMKalmanFilter:
#     def __init__(self, observations, n_dim_state, n_dim_obs, initial_parameters, data_setting):
#         self.observations = observations
#         self.n_dim_state = n_dim_state
#         self.n_dim_obs = n_dim_obs
#         self.initial_parameters = initial_parameters
#         self.data_setting = data_setting
#         self.kf = KalmanFilter(n_dim_obs=n_dim_obs, n_dim_state=n_dim_state,
#                                initial_state_mean=initial_parameters['initial_state_mean'],
#                                initial_state_covariance=initial_parameters['initial_state_covariance'],
#                                transition_matrices=initial_parameters['transition_matrices'],
#                                observation_matrices=initial_parameters['observation_matrices'],
#                                transition_covariance=initial_parameters['transition_covariance'],
#                                observation_covariance=initial_parameters['observation_covariance'])

#     def run_em(self, n_iter=10):
#         differential_solver = DifferentialEquationSolver(self.initial_parameters['params_list'], self.data_setting)

#         for i in range(n_iter):
#             # Eステップ: フィルタリングとスムージングを実行して状態推定を得る
#             self.kf.filter(self.observations)
#             smoothed_state_means, smoothed_state_covariances = self.kf.smooth(self.observations)
            
#             # Mステップ: ハイパーパラメータに基づいて観測方程式のパラメータを計算
#             solve_at, solve_bt = differential_solver.calc_observation_params()
#             self.kf.observation_matrices = solve_bt
#             self.kf.observation_offsets = solve_at

#         return {
#             'transition_matrices': self.kf.transition_matrices,
#             'observation_matrices': self.kf.observation_matrices,
#             'transition_covariance': self.kf.transition_covariance,
#             'observation_covariance': self.kf.observation_covariance,
#             'initial_state_mean': self.kf.initial_state_mean,
#             'initial_state_covariance': self.kf.initial_state_covariance,
#         }