#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: None

hyperparams = {
    "国内金利" : {
        "Moodys_Path" : r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\yield_curve_scenarios.csv", # Moodys_ESGファイルパス
        "Maruchu_Path" : r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\yield_curve_scenarios2.csv", # ㊥_ESGファイルパス
        "分位点" : [0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.95, 0.99, 0.995], # 可視化する分位点
        "表示満期" : [1, 3, 5, 7, 10, 20, 30, 40, 50], # 可視化する満期(50年金利まで)
        
    },
    "米国金利" : {
        "Moodys_Path" : r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\yield_curve_scenarios.csv", # Moodys_ESGファイルパス
        "Maruchu_Path" : r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\yield_curve_scenarios2.csv", # ㊥_ESGファイルパス
        "分位点" : [0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.95, 0.99, 0.995], # 可視化する分位点
        "表示満期" : [1, 3, 5, 7, 10, 20, 30, 40, 50], # 可視化する満期(50年金利まで)
        
    },
    # リスク性資産の比較用
    "リスク性資産" : {
        "Moodys_Folder_Path" : r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\risk_assets", # 
        "Maruchu_Folder_Path" : r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Maruchu",
        "可視化資産" : ["国内株式", "海外株式"],
        "分位点" : [0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.95, 0.99, 0.995],
        "表示満期" : [1, 3, 5, 7, 10], # 可視化する満期
    },
    "相関係数" : {
        "計算対象資産" : [],
    },
    "その他設定" :{
        "リターン効率計算" : True, # μ/σ の計算
        "キャピタルリターン計算" : True,

    }

}
