import numpy as np
import pandas as pd

# 横軸: 満期 (0年, 0.5年, 1年, ..., 50年)
maturities = np.linspace(0, 50, 101)

# 縦軸: シナリオ (0年後, 0.5年後, ..., 10年後) とパス (10,000パス)
num_scenarios = 10000
time_scenarios = np.linspace(0, 10, 21)

# データの行数は21,000、列数は101
data = np.random.rand(21000, 101)

# DataFrameに変換して、CSVとして保存
df = pd.DataFrame(data, columns=[f"Maturity_{m:.1f}" for m in maturities])

# CSVファイルを保存
df.to_csv(r'C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\yield_curve_scenarios2.csv', index=False)

