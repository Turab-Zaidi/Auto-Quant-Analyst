import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def create_dashboard_chart(df: pd.DataFrame, ticker: str, save_path: str):
    """
    Creates a professional, Bloomberg-style 3-panel technical analysis chart.
    
    Args:
        df (pd.DataFrame): DataFrame must contain Date, Close, SMA_50, SMA_200, Volume, RSI.
        ticker (str): The stock ticker for the chart title.
        save_path (str): The full path inside the Docker container to save the image.
    """
    
    # --- Chart Styling ---
    plt.style.use('dark_background')
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, 
        figsize=(16, 12),  # Larger figure size for more space
        gridspec_kw={'height_ratios': [3, 1, 1]},
        facecolor='#121212'
    )
    fig.suptitle(f'{ticker} Technical Analysis Dashboard', fontsize=20, y=0.95, color='white')

    # --- Panel 1: Price and Moving Averages ---
    ax1.plot(df['Date'], df['Close'], color='white', label='Close Price', linewidth=1.5)
    ax1.plot(df['Date'], df['SMA_50'], color='orange', label='50-Day SMA', linestyle='--', linewidth=1)
    ax1.plot(df['Date'], df['SMA_200'], color='cyan', label='200-Day SMA', linestyle='--', linewidth=1)
    ax1.set_title('Price & Moving Averages', color='white', fontsize=14)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.3, color='#444444')
    ax1.tick_params(axis='x', labelrotation=45) # Rotate date labels
    
    # --- Panel 2: Volume ---
    volume_colors = ['#26a69a' if c >= o else '#ef5350' for o, c in zip(df['Open'], df['Close'])]
    ax2.bar(df['Date'], df['Volume'], color=volume_colors, alpha=0.7)
    ax2.set_title('Volume', color='white', fontsize=14)
    ax2.grid(True, which='both', linestyle='--', linewidth=0.3, color='#444444')

    # --- Panel 3: RSI ---
    ax3.plot(df['Date'], df['RSI'], color='purple', linewidth=1.5)
    ax3.axhline(70, linestyle='--', color='red', linewidth=1, alpha=0.7)
    ax3.axhline(30, linestyle='--', color='green', linewidth=1, alpha=0.7)
    ax3.set_ylim(0, 100)
    ax3.set_title('RSI (14-Day)', color='white', fontsize=14)
    ax3.grid(True, which='both', linestyle='--', linewidth=0.3, color='#444444')

    # --- Final Touches ---
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#1a1a2e')
        ax.tick_params(axis='x', colors='white', labelsize=10)
        ax.tick_params(axis='y', colors='white', labelsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y')) # Nicer date format
        ax.grid(True, alpha=0.2) 

    plt.subplots_adjust(hspace=0.4) # Increase vertical space between charts
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
    
    # --- Save Figure ---
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Chart successfully generated and saved to {save_path}")