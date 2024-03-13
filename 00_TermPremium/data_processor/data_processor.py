import pandas as pd
import numpy as np
import os
from datetime import datetime
from pandas.tseries.offsets import *
from sklearn.preprocessing import StandardScaler


def split_data(df, train_test_dict, data_setting):
    """ 訓練データ・テストデータに分割する関数

    Parameters:
        df: pd.DataFrame
            分割対象のデータフレーム
        train_test_dict : dict
            訓練期間を格納した辞書
        monthly_bool: bool
            A flag to determine whether monthly data selection should be performed.
    Returns:
        X_train : pd.DataFrame
            The DataFrame for training data.
        Y_train : pd.DataFrame
            The DataFrame for training labels.
    """

    # 欠損データ削除
    df = data_preprocess(df)
    # 取得データの期間を確認
    start, end = df.index[0], df.index[-1]
    # 必要なデータのみを抽出
    df_extracted = selet_estimate_data(df, data_setting)

    # 訓練データとテストデータに分割
    try:
        X_train = extract_dataset(df_extracted, train_test_dict["train_start_date"], train_test_dict["train_end_date"])
        Y_train = extract_dataset(df_extracted, train_test_dict["test_start_date"], train_test_dict["test_end_date"])
    except:
        print(f"データフレームの期間指定が {start} - {end} の範囲外です. 正しいデータ期間を設定してください")
        raise SystemExit

    return X_train, Y_train


def extract_dataset(df, start_date, end_date):
    """ 指定期間のデータセットを抽出

    Parameters:
        df: pd.DataFrame
            データフレーム
        start_date: datetime
            訓練データ (start)
        end_date: datetime
            訓練データ (end)

    Returns:
        df_extracted : pd.DataFrame
            指定期間のデータフレーム
        test_term : np.array
            訓練期間の配列
    """
    # 抽出期間のフラグ
    flag_date = (df.index >= start_date) & (df.index <= end_date)
    # データ抽出
    df_extracted = df.loc[flag_date, :]

    return df_extracted


def selet_estimate_data(df, data_setting):
    """ 時点の刻み回数を出す関数
    Args:
        data_setting : dict
            ハイパーパラメータの条件を格納した辞書
    Returns:
        df : int
            データ抽出後のデータフレーム
    """
    # 推計期間の確認
    try:
        if data_setting["estimate_term"] == "月次":
            if data_setting["choose_date"] == "BM":
                # 月末データを取得
                df = df.resample(data_setting["choose_date"], convention = "end").last()
            elif data_setting["choose_date"] == "MS":
                # 月初データを取得
                df = df.resample(data_setting["choose_date"]).first()
        elif data_setting["estimate_term"] == "週次":
            # 2で指定すれば水曜日
            df = df[df.index.weekday == data_setting["weekday"]]
        elif data_setting["estimate_term"] == "日次":
            df = df.copy()
        else:
            print("正しい推計期間を設定してください")
    except Exception as e:
        print("エラー")

    return df


def make_estimate_maturity_array(data_setting):
    """ 残存年数の配列を作成する関数
    
    Parameters:
        data_setting : dict
            ハイパラを格納したリスト
    
    Returns:
        maturity_array : np.array
            推計対象の残存年数を格納した配列
    """

    # 推計年数
    estimate_year = data_setting["maturities"] / 12
    # 残存年数配列の作成    
    maturity_array = np.arange(1.0, data_setting["maturities"] + 1.0)[np.newaxis :] / 12.0

    return maturity_array


def data_preprocess(df):
    """ データの欠損処理を行う関数

    Parameters:
        df : pd.DataFrame
            データフレーム
    Returns:
        df : pd.DataFrame
            欠損処理後のデータフレーム
    """
    # NAN値のある列を削除
    df = df.dropna()
    # 数値データではない列の削除
    df = df.select_dtypes(include = [np.number])

    return df



# ベクトル化関数
def vec(x):
    return np.reshape(x, (-1, 1))

# 二乗形式のベクトル化関数
def vec_quad_form(x):
    return vec(np.outer(x, x))


def standard_data(data, setting_bool, ddof = 1):
    """ イールドカーブの標準化

    Parameters:
        data : np.array
            標準化するデータ
        setting_bool : bool
            標準化を行うかどうかのフラグ
        ddof : int
            標準偏差の計算時の自由度補正 (0 は母標準偏差, 1 は標本標準偏差)
    Returns:
        standard_data : np.array
            標準化されたデータ配列
    """

    # 平均値を差し引くだけか
    if setting_bool["subtract_mean_yield_bool"]:
        scaled_data = data - np.mean(data, axis = 0)
    # 標準化
    else:
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)

    return scaled_data

def set_save_folder_path(folder_path, model, country, train_test_dict):
    """ 結果を格納するフォルダパスの作成

    Parameters:
        folder_path : str
            フォルダパス
        model : str
            推計対象のモデル
        country : str
            分析対象国
        train_test_dict : dict
            分析期間を格納した辞書
    Returns:
        save_path : str
            結果の保存パス
    """

    # 保存パスを作成
    data_save_path = os.path.join(folder_path, model)
    # フォルダがない場合は新規作成
    os.makedirs(data_save_path, exist_ok = True)
    # 各モデルの保存パス作成
    data_save_path = os.path.join(data_save_path, country)
    # フォルダがない場合は新規作成
    os.makedirs(data_save_path, exist_ok = True)
    # 訓練期間データ抽出
    start, end = train_test_dict["train_start_date"].strftime("%Y%m%d"), train_test_dict["train_end_date"].strftime("%Y%m%d") 
    # フォルダ名
    folder_name = f"train_term : {start}-{end}"
    save_path = os.path.join(data_save_path, folder_name)
    # フォルダが存在しない場合は新規作成
    os.makedirs(data_save_path, exist_ok = True)

    return save_path