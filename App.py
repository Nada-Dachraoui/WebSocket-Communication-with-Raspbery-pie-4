import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Scrollbar, filedialog, Menu
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging

class RealTimeDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Dashboard")
        self.root.geometry("600x600")
        self.root.configure(background='white')
        self.file_path = 'voltage_measurements.csv'
        self.setup_menu()
        self.setup_ui()
        self.setup_plot()
        self.update_dashboard()

    def setup_menu(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Load CSV", command=self.load_csv_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about_info)
        help_menu.add_command(label="Help", command=self.show_help_info)
        menu_bar.add_cascade(label="Help", menu=help_menu)

    def setup_ui(self):

        style = ttk.Style()
        style.configure("white.TLabelframe", background='white', foreground='white')
        style.configure("white.TLabel", background='white', foreground='white')
        self.label_frame = ttk.LabelFrame(self.root, text="Measurements", style="white.TLabelframe")
        self.label_frame.pack(fill='both', padx=10, pady=10)

        self.labels = {
            "Voltage_FXS": ttk.Label(self.label_frame, text="Voltage_FXS (V):", style="Black.TLabel"),
            "RingVoltage": ttk.Label(self.label_frame, text="Ring Voltage (V):", style="Black.TLabel"),
            "Current_FXS": ttk.Label(self.label_frame, text="Current_FXS (mA):", style="Black.TLabel"),
            "Power": ttk.Label(self.label_frame, text="Power (Watt):", style="Black.TLabel"),
        }


        for idx, (key, label) in enumerate(self.labels.items()):
            label.grid(row=idx, column=0, padx=5, pady=5, sticky="w")
            value_label = ttk.Label(self.label_frame, text="", style="Black.TLabel")
            value_label.grid(row=idx, column=1, padx=5, pady=5, sticky="e")
            self.labels[key] = value_label

        self.buttons_frame = ttk.Frame(self.root)
        self.buttons_frame.pack(fill='x', padx=10, pady=5)

        self.id_button = ttk.Button(self.buttons_frame, text="Show Device ID", command=self.show_device_id)
        self.id_button.pack(side='left', padx=5, pady=5)

        self.csv_button = ttk.Button(self.buttons_frame, text="Show CSV Data", command=self.show_csv_data)
        self.csv_button.pack(side='left', padx=5, pady=5)

        self.refresh_button = ttk.Button(self.buttons_frame, text="Refresh Data", command=self.refresh_data)
        self.refresh_button.pack(side='left', padx=5, pady=5)

        self.histogram_button = ttk.Button(self.buttons_frame, text="Show Histograms", command=self.show_histograms)
        self.histogram_button.pack(side='left', padx=5, pady=5)

        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def setup_plot(self):

        self.fig, (self.ax1, self.ax2, self.ax3, self.ax4) = plt.subplots(4, 1, figsize=(12, 8))
        self.fig.patch.set_facecolor('white')

        for ax in (self.ax1, self.ax2, self.ax3, self.ax4):
            ax.set_facecolor('white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.grid(True, linestyle='--', alpha=0.7)

        self.line1, = self.ax1.plot([], [], 'r-', label='Voltage FXS')
        self.line2, = self.ax2.plot([], [], 'g-', label='Ring Voltage')
        self.line3, = self.ax3.plot([], [], 'b-', label='Current FXS')
        self.line4, = self.ax4.plot([], [], 'm-', label='Power')

        self.ax1.legend()
        self.ax2.legend()
        self.ax3.legend()
        self.ax4.legend()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000, blit=False)

    def update_dashboard(self):
        df = self.load_csv_data(self.file_path)
        if df is not None and not df.empty:
            latest_data = df.iloc[-1]
            for key in self.labels:
                self.update_label(self.labels[key], latest_data.get(key, ""), key)
        self.root.after(1000, self.update_dashboard)

    def update_label(self, label_widget, value, measurement_type):
        label_widget.config(text=value)
        state = self.get_state(measurement_type)
        color = self.get_color_by_state(state)
        label_widget.config(foreground=color)

    def get_color_by_state(self, state):
        return 'red' if state == 'over' else 'green'

    def get_state(self, measurement_type):
        df = self.load_csv_data(self.file_path)
        if df is not None and not df.empty:
            latest_state = df.iloc[-1]['state']
            return self.get_measurement_state(latest_state, measurement_type)
        return "average"

    def get_measurement_state(self, latest_state, measurement_type):
        if f"{measurement_type} over average" in latest_state:
            return "over"
        elif f"{measurement_type} under average" in latest_state:
            return "under"
        return "average"

    def load_csv_data(self, file_path):
        try:
            df = pd.read_csv(file_path)
            return df
        except FileNotFoundError:
            self.handle_file_not_found(file_path)
        except Exception as e:
            self.handle_generic_error(f"An error occurred while loading the CSV file: {e}")
        return pd.DataFrame()

    def animate(self, i):
        df = self.load_csv_data(self.file_path)
        if df is not None and not df.empty:
            x_data = df.index
            self.line1.set_data(x_data, df['Voltage_FXS'])
            self.line2.set_data(x_data, df['RingVoltage'])
            self.line3.set_data(x_data, df['Current_FXS'])
            self.line4.set_data(x_data, df['Power'])
            for ax in (self.ax1, self.ax2, self.ax3, self.ax4):
                ax.relim()
                ax.autoscale_view()
        self.canvas.draw()

    def show_device_id(self):
        try:
            with open('report.txt', 'r') as file:
                serial_number = file.readline().strip()
                messagebox.showinfo("Device ID", f"Serial Number: {serial_number}\nThis device is facing an electrical issue. Please check your device.")
        except FileNotFoundError:
            messagebox.showerror("File Not Found", "report.txt file not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def show_csv_data(self):
        top = Toplevel(self.root)
        top.title("CSV Data")
        top.configure(background='white')
        text_widget = tk.Text(top, wrap=tk.NONE, fg='black', bg='white')
        text_widget.grid(row=0, column=0, sticky="nsew")
        h_scroll = Scrollbar(top, orient='horizontal', command=text_widget.xview)
        h_scroll.grid(row=1, column=0, sticky='ew')
        text_widget.config(xscrollcommand=h_scroll.set)
        v_scroll = Scrollbar(top, orient='vertical', command=text_widget.yview)
        v_scroll.grid(row=0, column=1, sticky='ns')
        text_widget.config(yscrollcommand=v_scroll.set)
        try:
            with open(self.file_path, 'r') as file:
                csv_data = file.read()
                text_widget.insert(tk.END, csv_data)
        except FileNotFoundError:
            self.handle_file_not_found(self.file_path)
        except Exception as e:
            self.handle_generic_error(f"An error occurred while reading the CSV file: {e}")
        top.grid_rowconfigure(0, weight=1)
        top.grid_columnconfigure(0, weight=1)

    def load_csv_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.file_path = file_path
            self.update_dashboard()

    def refresh_data(self):
        self.update_dashboard()

    def show_histograms(self):
        df = self.load_csv_data(self.file_path)
        if df is not None and not df.empty:
            columns = ['Voltage_FXS', 'RingVoltage', 'Current_FXS', 'Power']
            for column in columns:
                plt.figure()
                plt.hist(df[column].dropna(), bins=20, edgecolor='black')
                plt.title(f'Histogram of {column}')
                plt.xlabel(column)
                plt.ylabel('Frequency')
                plt.grid(True)
                plt.show()
        else:
            messagebox.showerror("Error", "No data available to plot histograms.")

    def show_about_info(self):
        messagebox.showinfo("About", "Real-Time Dashboard v1.0\nDeveloped by Nada Dachraoui")

    def show_help_info(self):
        messagebox.showinfo("Help", "Use this application to monitor real-time data from the CSV file. Click 'Show CSV Data' to view the raw data.")

    def handle_file_not_found(self, file_path):
        messagebox.showerror("File Not Found", f"The file {file_path} does not exist. Please ensure the file path is correct.")

    def handle_generic_error(self, error_message):
        messagebox.showerror("Error", error_message)

if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimeDashboard(root)
    root.mainloop()