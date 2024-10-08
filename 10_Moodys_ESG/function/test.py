import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def simulate_results_dict():
    percentiles = [5, 50, 95]
    years = [f"Year_{i+1}" for i in range(10)]  # Simulating 10 years
    asset_list = ['foreign_stock', 'domestic_bond']

    results_dict = {}

    for asset in asset_list:
        # Simulate quantiles and mean values for File1 and File2
        file1_quantiles = np.random.rand(len(percentiles), len(years)) * 0.1  # Random values between 0 and 0.1
        file2_quantiles = np.random.rand(len(percentiles), len(years)) * 0.1  # Random values between 0 and 0.1
        file1_mean = np.random.rand(len(years)) * 0.1  # Mean values for File1
        file2_mean = np.random.rand(len(years)) * 0.1  # Mean values for File2

        # Create DataFrames for File1 and File2 results
        file1_result = pd.DataFrame(file1_quantiles, index=[f"{p}th" for p in percentiles], columns=years)
        file1_result.loc['Mean'] = file1_mean
        file2_result = pd.DataFrame(file2_quantiles, index=[f"{p}th" for p in percentiles], columns=years)
        file2_result.loc['Mean'] = file2_mean

        # Store results in the dictionary
        results_dict[asset] = {
            'File1_result': file1_result,
            'File2_result': file2_result
        }

    return results_dict

# Visualizing the scenario comparison using the previously defined function
def visualize_scenario_comparison(results_dict):
    for asset, result in results_dict.items():
        file1_result = result['File1_result']
        file2_result = result['File2_result']
        years = file1_result.columns[:-1]
        file1_quantiles = file1_result.loc[file1_result.index[:-1], years]
        file1_mean = file1_result.loc['Mean', years]
        file2_quantiles = file2_result.loc[file2_result.index[:-1], years]
        file2_mean = file2_result.loc['Mean', years]
        plt.figure(figsize=(10, 6))
        for quantile in file1_quantiles.index:
            plt.plot(years, file1_quantiles.loc[quantile], label=f'File1 {quantile}', linestyle='--', marker='o')
            plt.plot(years, file2_quantiles.loc[quantile], label=f'File2 {quantile}', linestyle='-', marker='x')
        plt.plot(years, file1_mean, label='File1 Mean', color='blue', linewidth=2)
        plt.plot(years, file2_mean, label='File2 Mean', color='red', linewidth=2)
        plt.title(f'Scenario Comparison for {asset}', fontsize=16)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Return', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend(loc='upper left')
        plt.tight_layout()
        plt.show()

# Generate the simulated data
results_dict = simulate_results_dict()

# Visualize the data
visualize_scenario_comparison(results_dict)
