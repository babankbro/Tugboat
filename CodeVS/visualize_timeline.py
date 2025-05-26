import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime

def visualize_timeline(data):
    """Visualize tugboat operations timeline as a Gantt chart."""
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Convert datetime strings to datetime objects
    df['enter_datetime'] = pd.to_datetime(df['enter_datetime'])
    df['exit_datetime'] = pd.to_datetime(df['exit_datetime'])
    
    # Calculate duration in hours
    df['duration'] = (df['exit_datetime'] - df['enter_datetime']).dt.total_seconds() / 3600
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create color mapping for operation types
    colors = {
        'Start': 'green',
        'Barge': 'blue',
        'o1': 'orange',
        's2': 'red',
        'Travel': 'purple'
    }
    
    # Create horizontal bars for each operation
    for i, (_, row) in enumerate(df.iterrows()):
        ax.barh(
            y=row['description'], 
            width=row['duration'], 
            left=row['enter_datetime'], 
            height=0.5,
            color=colors.get(row['operation'], 'gray'),
            label=row['operation']
        )
    
    # Format x-axis as dates
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    # Add labels and title
    ax.set_xlabel('Timeline')
    ax.set_ylabel('Operation Description')
    ax.set_title('Tugboat Operations Timeline')
    
    # Add grid and legend
    ax.grid(True, which='both', axis='x', linestyle='--', alpha=0.7)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))  # Remove duplicate labels
    ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Adjust layout
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    # Example data structure - replace with your actual data
    example_data = [
        {
            'operation': 'Start',
            'description': 'Start',
            'enter_datetime': '2025-01-12 06:30:00.000000',
            'exit_datetime': '2025-01-12 06:30:00.000000'
        },
        {
            'operation': 'Barge',
            'description': 'Barge Location',
            'enter_datetime': '2025-01-12 06:30:00.000000',
            'exit_datetime': '2025-01-12 07:30:00.000000'
        }
    ]
    
    fig = visualize_timeline(example_data)
    plt.savefig('tugboat_timeline.png', bbox_inches='tight', dpi=300)
    plt.show()
