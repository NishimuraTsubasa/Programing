"""
Ceated on Thr May 7 22:14:50 2024 

@author Tsubasa Nishimura
"""

import pandas as pd
import numpy as np
import requests

from config.config import hyperparams_dict

def main_calc_yield_curve(data_setting, file_path, country):
    """ イールドカーブを出力するmain関数
    """
    # パラメータをサイトよりダウンロードし，必要なパラメータの抽出
    params_list, date_array = download_df(file_path, country)
    # 残存年数の設定
    maturity_array = np.arange(1, data_setting["maturities"] + 1)[np.newaxis:] / (data_setting["maturities"] / 10) 
    # イールドカーブの推計
    df_yield_curve = make_yield_curve(maturity_array, params_list, date_array)

    return df_yield_curve


def svensson_model(t, param_array):
    """ Svensson model による金利推定
    Args :
        t : float
            残存年数（年単位）
        param_array : np.array
            Scensson model パラメータを格納した配列
    Return :
        yield_ : np.array
            推計されたイールドカーブ
    """

    # パラメータの抽出    
    beta0, beta1, beta2, beta3, tau1, tau2 = param_array
    
    # Svensson model に従うイールドカーブの復元
    term1 = beta0 + (beta1 + beta2) * ((1 - np.exp(-t / tau1)) / (t / tau1)) - beta2 * np.exp(-t / tau1)
    term2 = beta3 * ((1 - np.exp(-t / tau2)) / (t / tau2) - np.exp(-t / tau2))
    
    return term1 + term2

def make_yield_curve(maturity_array, param_array, date_array):
    """ 分析期間でイールドカーブを復元する関数
    Args :
        maturity_array : np.array
            残存年数 (120か月で設定)
        param_array : np.array
            Svenssonモデルパラメータ
        date_array : np.array
            イールドカーブの日付
    Return :
        df_yield_curve : pd.DataFrame
            分析期間のイールドカーブ
    """

    # Svensson_model によるイールドカーブ推計
    for i, t in enumerate(maturity_array):
        # svensson_model関数によるイールド推計
        yield_ = svensson_model(t, param_array)
        # 配列に格納
        if i == 0:
            yield_curve = np.array([yield_])
        else:
            yield_curve = np.append(yield_curve, [yield_], axis = 0)
    # データフレーム形式で保存
    df_yield_curve = pd.DataFrame(yield_curve, index = maturity_array, columns = date_array).T / 100 # % 表記から変更

    return df_yield_curve

def download_df(file_path, country):
    """ サイトからCSVファイルを読み込み, データフレームを加工する関数
    """
    # サイトURLを読み込み
    csv_url = file_path["file_path"]

    try:
        # ファイルのダウンロード
        response = requests.get(csv_url)
        # ダウンロードに成功した場合
        if response.status_code == 200:
            # ファイルを開く
            with open('data.csv', 'wb') as file:
                file.write(response.content)
            # データフレームに読み込み
            df = pd.read_csv('data.csv', skiprows = file_path["delete_row"], delimiter = ',')
            # データフレームを加工
            df = df.filter(items = ["Date", "BETA0", "BETA1", "BETA2", "BETA3", "TAU1", "TAU2"])
        else:
            print(f"{country} にてファイルがダウンロードできませんでした: {response.status_code}")
            exit()
    except:
        print(f"{country} のURLでCSVファイルがダウンロード出来ませんでした")

    # パラメータをリストに格納
    params_list = [df["BETA0"], df["BETA1"], df["BETA2"], df["BETA3"], df["TAU1"], df["TAU2"]]
    # 日付データの抽出
    date_array = pd.to_datetime(df["Date"])

    return params_list, date_array


