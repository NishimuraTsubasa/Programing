#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Tsubasa Nishimura
# Date: 2024-09-23
# Description: This script processes financial data and outputs a summary.
# Version: 1.0
# License: None

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def visualize_yield_distributions(data, years, output_pdf):
    """
    Visualizes the distribution of yield data for multiple specified years as subplots, color-coded by quantiles, and saves as a PDF.
    
    Args:
    data (DataFrame): The input DataFrame containing the yield data.
    years (list of float): List of specific years for which the distributions will be visualized.
    output_pdf (str): The path where the resulting PDF will be saved.
    """
    n_years = len(years)
    
    # Set up the subplots layout based on the number of years to visualize
    cols = 2
    rows = (n_years + 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(12, 6 * rows))
    axes = axes.flatten() if n_years > 1 else [axes]

    # Loop through each specified year and create a subplot for it
    for i, year in enumerate(years):
        if str(year) not in data.columns:
            raise ValueError(f"Year {year} is not in the DataFrame columns.")
        
        yield_data = data[str(year)]
        
        # Calculate quantiles (25%, 50%, 75%)
        quantiles = yield_data.quantile([0.25, 0.5, 0.75])
        
        # Plot the distribution in the corresponding subplot
        axes[i].hist(yield_data, bins=50, color='lightblue', edgecolor='black', alpha=0.7)
        
        # Mark the quantiles with lines and annotations
        colors = ['red', 'green', 'blue']
        labels = ['25th Percentile', '50th Percentile (Median)', '75th Percentile']
        for quantile, color, label in zip(quantiles, colors, labels):
            axes[i].axvline(quantile, color=color, linestyle='--', linewidth=2)
            axes[i].text(quantile, plt.ylim()[1] * 0.9, f'{label}: {quantile:.4f}', color=color)
        
        # Set titles and labels for the subplot
        axes[i].set_title(f'Yield Distribution at {year} Years', fontsize=14)
        axes[i].set_xlabel('Yield')
        axes[i].set_ylabel('Frequency')
    
    # Remove any empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    
    # Adjust layout and save as a PDF
    plt.tight_layout()
    plt.savefig(output_pdf)
    plt.close()

# Example: visualize multiple years and save to a PDF
output_pdf_path_multi = r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Moodys\Yield_Distributions_Multiple_Years.pdf"
df = pd.read_csv(r"C:\Users\bldyr\OneDrive\デスクトップ\自己研鑽用\20_GitHub\Moodys_ESG\input\Maruchu\yield_scenario\Yield_Scenarios_at_0.0_Years.csv", encoding = "shift-jis")
visualize_yield_distributions(df, [0.5, 1.0, 5.0, 10.0], output_pdf_path_multi)

# Return the path to the generated PDF for verification
output_pdf_path_multi


