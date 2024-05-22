import os
import csv
import matplotlib.pyplot as plt

def plot_line_from_csv(csv_file, x_col, y_cols, title, x_label, y_label, legend_labels, start_row=None, end_row=None):
    x_data = []
    y_data = {y_col: [] for y_col in y_cols}

    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for i, row in enumerate(csv_reader):
            if (start_row is not None and i < start_row) or (end_row is not None and i >= end_row):
                continue
            x_data.append(float(row[x_col]))
            for y_col in y_cols:
                y_data[y_col].append(float(row[y_col]))

    # Plot data
    plt.figure(figsize=(10, 6))  # Adjust figure size as needed
    for y_col, legend_label in zip(y_cols, legend_labels):
        plt.plot(x_data, y_data[y_col], label=legend_label)

    # Add title and labels
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    #plt.yticks(range(0, 100, 10))  # Set ticks at each multiple of 10 from 0 to the maximum y-value

    # Add legend
    plt.legend()

    # Show plot
    plt.grid(True)
    plt.show()


# Example usage
script_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(script_dir, 'output')
csv_file = os.path.join(images_dir, 'file.csv')

x_col = "time"     # Update with the column name for x-axis
y_cols = ["yaw_mag", "yaw_comp",  "yaw_k"]  # Update with the column names for y-axis
title = r"$\psi_{magnetometer}$ vs $\psi_{Complementary Filter  \alpha=0.05}$"
x_label = "Time (s)"
y_label = "$\\psi$ (º)"
legend_labels = [r"$\psi_{magnetometer}$" , r"$\psi_{CF  \alpha=0.05}$", r"$\psi_{KF}$"]  # Update with legend labels
# legend_labels = y_cols
start_row = int(20*1000/11)# Update with the starting row index
end_row = int(35*1000/11)   # Update with the ending row index
# end_row = None
plot_line_from_csv(csv_file, x_col, y_cols, title, x_label, y_label, legend_labels, start_row, end_row)