import pandas as pd
import numpy as np
from numpy import newaxis
import matplotlib.pyplot as plt
import copy
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from data_processor.data_processor import *


def AMC_model_main(X_train, data_setting, setting_bool):
    """ ACMモデルによるイールドカーブ, タームプレミアム, リスクフリーレートを推計
    
    Parameters:
        X_train: np.array
            トレーニングデータ
        yield_PCs: np.array
            イールドの主成分
        maturity_array: np.array
            残存期間の配列
        data_setting: dict
            データ処理の設定
        bool_setting: dict
            モデルのブール設定    
    Returns:
        result_list: list
            予測されたイールドカーブ, タームプレミアム, リスクフリーレートを含むリスト
        parms_list: list
            モデルで使用されるパラメータを含むリスト
    """

    # スケール変換(平均値減算)したイールドカーブの抽出
    scaled_X_trian = standard_data(
        np.array(X_train)[:, data_setting["start_maturity"] :], setting_bool # 最初の2か月は使用しない
    )
    # 主成分スコアと固有ベクトルの計算
    yield_PCs, _, _ = calc_yield_PC_by_PCA(
        scaled_X_trian, data_setting, setting_bool
    )
    # 推計する残存年数の配列
    maturity_array = make_estimate_maturity_array(data_setting)

    # VARパラメータと超過リターンを計算する
    VAR_params_list = VAR_param_estimate(yield_PCs, setting_bool)
    excess_return, risk_free_rate = calc_excess_return(np.array(X_train), maturity_array)
    # 超過リターンモデルパラメータとリスクの市場価格を計算する
    excess_return_params_list = estimated_excess_return_params(
        yield_PCs, excess_return, data_setting, VAR_params_list
    )
    lambda_list, zero_lambda_list = calc_risk_price(
        excess_return_params_list, VAR_params_list
    )

    # イールドカーブのパラメータを計算する
    A, B = calc_yield_curve_params(
        yield_PCs, risk_free_rate, excess_return_params_list,
        VAR_params_list, lambda_list, data_setting
    )
    
    # イールドカーブを予測してプレミアム期間を計算する
    pred_yield_curve = yield_curve_estimate(
        yield_PCs, A, B, maturity_array
    )
    
    # 無リスク金利を計算する
    A_zero, B_zero = calc_yield_curve_params(
        yield_PCs, risk_free_rate, excess_return_params_list,
        VAR_params_list, zero_lambda_list, data_setting
    )
    pred_risk_free_rate = yield_curve_estimate(
        yield_PCs, A_zero, B_zero, maturity_array
    )
    
    # プレミアム期間を計算する
    term_premium = pred_yield_curve - pred_risk_free_rate
    
    # 結果をリストにまとめる
    result_dict = {
        "result_yield" : X_train,
        "estimate_yield" : pd.DataFrame(pred_yield_curve, index = X_train.index, columns = X_train.columns), 
        "term_premium" : pd.DataFrame(term_premium, index = X_train.index, columns = X_train.columns), 
        "estimate_rf_rate" : pd.DataFrame(pred_risk_free_rate, index = X_train.index, columns = X_train.columns)
    }
    
    return result_dict


def VAR_param_estimate(yield_PCs, bool_setting):
    """
    イールドデータの主成分からVARモデルのパラメータを推定します。

    Args:
        yield_PCs : np.array
            イールドデータの主成分
        bool_setting : dict
            VARモデルで切片を使用するかどうかを決定するブール設定を持つ辞書

    Returns:
        VAR_params_list : list
            推定されたVARモデルのパラメータを含むリスト
                Mu    : 切片項（適用される場合）
                Phi   : 自己回帰係数の行列
                v     : VARモデルの残差
                Sigma : 残差の共分散行列
    """
    
    # VARモデルのためのLHS（左辺）とRHS（右辺）を構築する
    LHS = yield_PCs[1:, :].T  # 依存変数のシフトされたデータ
    RHS = np.vstack((np.ones((1, LHS.shape[1])), yield_PCs[0 : -1, :].T))  # 必要に応じて切片を追加

    if bool_setting["use_mu_bool"]:
        # 切片をVARモデルに使用する場合
        var_coeffs = LHS @ np.linalg.pinv(RHS)
        Mu = var_coeffs[:, [0]]  # 切片項
        Phi = var_coeffs[:, 1:]  # 自己回帰係数
    else:
        # 切片がない場合
        RHS = np.vstack((yield_PCs[0 : -1, :].T))  # 切片なしの過去の値のみ
        var_coeffs = LHS @ np.linalg.pinv(RHS)
        Mu = np.zeros((yield_PCs.shape[1], 1))
        Phi = var_coeffs  # 自己回帰係数のみ

    # 残差を計算する
    v = LHS - var_coeffs @ RHS
    # 残差の共分散行列を計算する
    Sigma = v @ v.T / LHS.shape[1]

    # VARパラメータをリストにまとめる
    VAR_params_list = [Mu, Phi, v, Sigma]

    return VAR_params_list


def calc_bond_return(yield_curve, maturity_array):
    """ 無リスク金利と対数値債券価格を計算

    Args:
        yield_curve: np.array
            Svenssonモデルから得られたイールドカーブ
        maturity_array: np.array
            各債券の満期までの残存期間
    Returns:
        risk_free_rate: np.array
            計算された無リスク金利
        log_price: np.array
            債券価格の自然対数
    """

    # 債券価格を計算する
    # P(t) = e^(-rt) の計算
    log_price = - yield_curve * np.array([maturity_array])
    # 債券価格からリスクフリーレートを計算する
    risk_free_rate = - log_price[: -1, 0]

    return risk_free_rate, log_price


def calc_excess_return(yield_curve, maturity_array):
    """ 債券の無リスク金利に対する超過リターンを計算

    Args:
        yield_curve: np.array
            Svenssonモデルから得られたイールド曲線を表す配列
        maturity_array: np.array
            残存年数を格納した配列
    Returns:
        excess_return: np.array
            各債券の超過リターンの配列
        rf: np.array
            各債券の無リスク金利の配列
    """
    # 債券のリターンと無リスク金利を計算
    rf, log_price = calc_bond_return(yield_curve, maturity_array)

    # 超過リターンは対数価格と無リスク金利の差
    excess_return = log_price[1 :, : -1] - log_price[:-1, 1 :] - rf[np.newaxis].T

    return excess_return, rf



def estimated_excess_return_params(yield_PCs, excess_return, data_setting, VAR_params_list):
    """ 保有超過リターンパラメータの推定

    Args:
        yield_PCs : np.array
            イールドデータの主成分
        excess_return : np.array
            超過リターンの配列
        data_setting : dict
            データの設定を含む辞書
        VAR_params_list : list
            VARパラメータを含むリスト
    Returns:
        excess_return_params_list : list
            推定された超過リターンのパラメータのリスト
    """

    # 設定に基づいて関連する満期を選択する
    select_maturity = data_setting["rx_maturities"]
    selected_excess_return = excess_return[:, [x - 2 for x in select_maturity]].T

    # 回帰方程式のためのZ行列を構築するW
    Z = np.vstack([np.ones((1, VAR_params_list[2].shape[1])), VAR_params_list[2], yield_PCs[0 : -1, :].T])

    # 超過リターンのパラメータを計算する
    parms = selected_excess_return @ np.linalg.pinv(Z)

    # 期待誤差とその分散を計算する
    expected_error = selected_excess_return - parms @ Z
    excess_return_Sigma = np.sum(expected_error ** 2) / len(expected_error)

    # 超過リターンのパラメータをまとめる
    excess_return_params_list = [parms[:, [0]], parms[:, 1:yield_PCs.shape[1] + 1].T, parms[:, yield_PCs.shape[1] + 1 :], excess_return_Sigma]

    return excess_return_params_list


def calc_risk_price(excess_return_params_list, VAR_params_list):
    """ リスクの市場価格を計算

    Args:
        excess_return_params_list: list
            超過リターンのパラメータを含むリスト(a, beta, c, Sigma)
        VAR_params_list: list
            VARのパラメータを含むリスト (mu、Phi、v、Sigma)
    Returns:
        lambda_list: list
            リスクの市場価格パラメータを含むリスト。
        zero_lambda_list: list
            リスクの市場価格がゼロの場合のリスト
    """

    # 超過リターンのパラメータとVARパラメータを展開する
    a, beta, c, excess_return_Sigma = excess_return_params_list
    mu, Phi, v, Sigma = VAR_params_list

    # betaの二次形式のB*行列を計算する
    B_star = np.squeeze(np.apply_along_axis(vec_quad_form, 1, beta.T))

    # ラムダ値を推定する
    # lambda_0は定数項のリスク価格、lambda_1は時変項のリスク価格
    lambda_0 = np.linalg.pinv(beta.T) @ (a + 1/2 * (B_star @ vec(Sigma) + excess_return_Sigma))
    lambda_1 = np.linalg.pinv(beta.T) @ c

    # さらなる計算のためにlambda_0とlambda_1を結合する
    lambda_list = [lambda_0, lambda_1]

    # 超過リターンがないと仮定した場合のゼロのlambdaリストを計算する
    zero_lambda_list = [
        np.zeros(lambda_0.shape),
        np.zeros(lambda_1.shape)
    ]

    # ラムダパラメータを返す
    return lambda_list, zero_lambda_list


def calc_yield_curve_params(yield_PCs, risk_free_rate, excess_return_params_list, VAR_params_list, lambda_list, data_setting):
    """ イールドカーブのパラメータ推計

    Args:
        yield_PCs: np.array
            イールドの主成分
        risk_free_rate: np.array
            無リスク金利
        excess_return_params_list: list
            超過リターンのパラメータを含むリスト
        VAR_params_list: list
            VARモデルのパラメータを含むリスト
        lambda_list: list
            リスクの市場価格λのリスト
        data_setting: dict
            データの設定を含む辞書
    Returns:
        A: np.array
            イールドカーブのパラメータ行列 A
        B: np.array
            イールドカーブのパラメータ行列 B
    """

    # 行列 A と B を初期化
    num_maturities, factor_num = data_setting["maturities"], data_setting["factor_num"]
    A = np.zeros((1, num_maturities))
    B = np.zeros((factor_num, num_maturities))

    # 対数債券価格の時系列モデルパラメータの初期値を計算
    delta = np.array([risk_free_rate]) @ np.linalg.pinv(
        np.vstack((
            np.ones((1, yield_PCs.shape[0] - 1)),
            yield_PCs[0 : -1, :].T
        ))
    )
    # 第1成分はA_0、第2成分はB_0
    delta_zero, delta_one = delta[[0], [0]], delta[[0], 1 :]
    A[0, 0] = - delta_zero
    B[:, 0] = - delta_one

    # A と B の残りの要素を計算する
    for i in range(1, num_maturities):
        A[0, i] = A[0, i - 1] + B[:, i - 1].T @ (VAR_params_list[0] - lambda_list[0]) \
                + 0.5 * (B[:, i - 1].T @ VAR_params_list[3] @ B[:, i - 1] + excess_return_params_list[3]) - delta_zero
        B[:, i] = B[:, i - 1] @ (VAR_params_list[1] - lambda_list[1]) - delta_one 

    return A, B



def yield_curve_estimate(yield_PCs, A, B, maturity_array):
    """ パラメータ A および B を用いたイールドカーブの推定

    Paramters:
        yield_PCs: np.array
            イールド曲線の主成分
        A: np.array
            イールド曲線の推定に使用されるパラメータ行列 A
        B: np.array
            イールド曲線の推定に使用されるパラメータ行列 B
        maturity_array: np.array
            各債券の満期までの時間を表す配列
    Returns:
        pred_yield_curve: np.array
            推定されたイールド曲線
    """
    # 推定された対数価格を計算する
    estimated_log_price = (A.T + B.T @ yield_PCs.T).T
    
    # 対数価格をイールド曲線に変換する
    # 式 log(P(t)) = -rt を再配列して r = -log(P(t)) / t
    pred_yield_curve = - estimated_log_price / maturity_array

    return pred_yield_curve


def calc_estimate_error(yield_PCs):
    """ 予測されたイールド主成分の推定誤差を計算

    Parameters:
        yield_PCs: np.array
            イールド曲線の主成分
    Returns:
        estimate_error: np.array
            モデルの推定誤差
    """

    # VARモデルの推定のために左辺（LHS）と右辺（RHS）を準備する
    LHS = yield_PCs[1:, :]  # 依存変数（y_t+1）
    RHS = np.hstack((np.ones((LHS.shape[0], 1)), yield_PCs[:-1, :]))  # 切片を含む独立変数（y_t）
    # VAR係数を計算する
    var_coeffs = np.linalg.pinv(RHS) @ LHS
    # 残差（誤差）を計算する
    v = LHS - RHS @ var_coeffs
    # 推定誤差を計算する（残差のノルムを観測値の数で割る）
    estimate_error = np.sqrt((v ** 2).sum(axis=1)) / LHS.shape[1]

    return estimate_error


def calc_yield_PC_by_PCA(scaled_X_train, data_setting, bool_setting):
    """ スケーリングされたイールドデータに対して主成分分析(PCA)を実行して主成分を計算

    Parameters:
        scaled_X_train: np.array
            スケーリングされたイールドデータ
        data_setting : dict
            PCAで保持する因子の数を含む辞書
        bool_setting: dict
            固有ベクトルと主成分を標準化するかを決定するブール設定を含む辞書
    Returns:
        yield_PC_by_PCA: np.array
            PCAから導出された主成分。
        eigenvectors: np.array
            PCAから導出された固有ベクトル。
        pca_explained_variance: np.array
            PCAコンポーネントによって説明される分散
    """

    # データ設定で指定された成分数でPCAを初期化
    pca = PCA(n_components=data_setting["factor_num"])
    pca.fit(scaled_X_train)

    # ブール設定に基づいて固有ベクトルを標準化するかを決定
    if bool_setting["standardize_eigenvector_bool"]:
        eigenvectors = standardize_eigenvectors(pca.components_, pca.explained_variance_)
    else:
        eigenvectors = pca.components_

    # ブール設定に基づいて主成分を標準化するかを決定
    if bool_setting["standardize_yield_PCs_bool"]:
        yield_PCs = standardize_PCs(pca.transform(scaled_X_train), pca.explained_variance_)
    else:
        yield_PCs = pca.transform(scaled_X_train)

    return yield_PCs, eigenvectors, pca.explained_variance_


def standardize_eigenvectors(eigenvectors, variances):
    """ 固有ベクトルを標準化. 固有値 (分散) の逆平方根でスケーリング
    
    Parameters :
        eigenvectors: np.array
            標準化する固有ベクトル
        variances: np.array
            各固有ベクトルに関連する分散    
    Returns :
        標準化された固有ベクトル
    """
    # scikit_learn のスケーリング
    scaler = StandardScaler()
    return scaler.fit_transform(np.diag(np.sqrt(variances)) @ eigenvectors)


def standardize_PCs(principal_components, variances):
    """ 主成分 (PCs) を固有値の逆平方根でスケーリングして標準化
    
    Parameters:
        principal_components: np.array
            標準化する主成分
        variances : np.array
            各主成分に関連する分散
    Returns :
        標準化された主成分
    """
    # scikit_learn のパッケージで標準化
    scaler = StandardScaler()
    return scaler.fit_transform(principal_components * np.sqrt(variances))


##########################################
# 下2つの関数は使用していない
##########################################
def standard_eigenvector(eigenvector, variance):
    """ 固有ベクトルを標準化. 固有値 (分散) の逆平方根でスケーリング

    Parameters :
        eigenvector: np.array
            標準化する固有ベクトル
        variance : np.array
            固有ベクトルに関連する固有値(PCAから取得)

    Returns :
        scaled_eigenvector: np.array
            スケーリングされた固有ベクトル
    """
    # 固有値の逆平方根を計算する
    sqrt_eigenvalues = np.sqrt(variance)
    diag_sqrt_eigenvalues = np.diag(np.reciprocal(sqrt_eigenvalues))

    # 固有ベクトルをスケーリングする
    scaled_eigenvector = diag_sqrt_eigenvalues @ eigenvector

    # 固有ベクトルを標準化する
    mean_eigenvector = np.mean(eigenvector, axis=0)
    std_eigenvector = np.std(eigenvector, axis=0, ddof=1)
    scaled_eigenvector = (eigenvector - mean_eigenvector) / std_eigenvector

    return scaled_eigenvector

def standard_data_PCs(yield_PCs, variance):
    """ 主成分 (PCs) を固有値の逆平方根でスケーリングして標準化

    Parameters :
        yield_PCs: np.array
            標準化する主成分
        variance : np.array
            主成分に関連する固有値 (PCAから取得)

    Returns:
        scaled_yield_PCs: np.array
            スケーリングされた主成分
    """
    # 固有値の逆平方根を計算
    sqrt_eigenvalues = np.sqrt(variance)
    diag_sqrt_eigenvalues = np.diag(np.reciprocal(sqrt_eigenvalues))

    # 主成分をスケーリング
    scaled_yield_PCs = yield_PCs @ diag_sqrt_eigenvalues

    return scaled_yield_PCs