import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def make_figure(test_df, pred_df, i, graph_title, y_lim, data_setting, pdf):
    """ 推計結果を基にグラフを作成する関数

    Args:
    - test_df : pd.DataFrame
        Dataframe containing the test data.
    - pred_df : pd.DataFrame
        Dataframe containing the prediction data.
    - i : int
        Index representing the ith term.
    - graph_title : str
        The title of the graph.
    - y_lim : list
        List of y-axis limits.
    - data_setting : dict
        Dictionary containing settings for the graph such as date format.
    - pdf : PdfPages
        PdfPages object to save the figure into.

    Returns:
        None
    """

    # Calculate the term for selection based on the index
    select_term = int(i / 12) - 1
    # Do not display the window frame
    plt.ioff()
    # Set font size
    plt.rcParams['font.size'] = 10
    # Create figure and axes
    fig, axes = plt.subplots(figsize=(10, 10), dpi=144)
    # Plot the FRB and prediction lines
    axes.plot(test_df.index, test_df.iloc[:, i], linestyle='-', label=f"{i / 12}year FRB", linewidth=1)
    axes.plot(test_df.index, pred_df.iloc[:, select_term] * 100, linestyle='--', label=f"{i / 12}year Predict", linewidth=1)
    # Plot the difference line
    axes.plot(test_df.index, (test_df.iloc[:, i] - pred_df.iloc[:, select_term] * 100), linestyle='-', label=f"Difference(FRB - Predict)", linewidth=1)
    # Set x-axis major locator and formatter
    axes.xaxis.set_major_locator(mdates.AutoDateLocator())
    axes.xaxis.set_major_formatter(mdates.DateFormatter(data_setting["graph_date_format"]))
    # Autofit x-date
    fig.autofmt_xdate()
    # Set labels and title
    axes.set_ylabel("Percent")
    axes.set_xlabel("date")
    axes.set_title(graph_title)
    # Set grid and legend
    axes.grid(which='major', axis='y', color='black', alpha=0.5, linestyle='--', linewidth=0.5)
    plt.legend(loc='upper right', fontsize=6)
    # Set the y-axis limit
    axes.set_ylim(y_lim)
    # Save to PDF
    pdf.savefig(fig)
    # Close the plot
    plt.close()