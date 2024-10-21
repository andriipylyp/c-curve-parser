import sys
import matplotlib as mpl
mpl.use("Qt5Agg")
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QCheckBox, QLabel, QRadioButton, QButtonGroup
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from dbfread import DBF
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Transformation")

        # Data
        self.data = None
        self.uploaded_file_name = None

        # Widgets
        self.load_button = QPushButton("Load file")

        self.remove_noise_checkbox = QCheckBox("Remove voltage noise of water")
        self.remove_noise_checkbox.setChecked(True)

        self.remove_data_before_spike_checkbox = QCheckBox("Remove data before spike")
        self.remove_data_before_spike_checkbox.setChecked(True)

        self.normilize_checkbox = QCheckBox("Normilize outputs using MinMax (0,1)")
        self.normilize_checkbox.setChecked(True)

        self.savitzky_golay_filter_checkbox = QCheckBox("Smooth graph with Savitzky-Golay filter")

        self.transform_data_button = QPushButton("Transform data")
        
        self.export_to_excel_button = QPushButton("Export to excel")

        self.button_group = QButtonGroup(self)

        self.radio_button1 = QRadioButton('Normilized')

        self.radio_button2 = QRadioButton('Savitzky-golay')

        self.radio_button3 = QRadioButton('Normilized + Savitzky-golay')
        

        self.button_group.addButton(self.radio_button1)
        self.button_group.addButton(self.radio_button2)
        self.button_group.addButton(self.radio_button3)

        self.save_plot_button = QPushButton("Save plot as...")

        self.file_status = QLabel("File not found...\nPlease upload a new file...", self)

        self.kon_2_min_retention_time_label = QLabel()
        self.kon_2_min_retention_time_label.hide()
        self.kon_5_min_retention_time_label = QLabel()
        self.kon_5_min_retention_time_label.hide()

        self.kon_2_max_retention_time_label = QLabel()
        self.kon_2_max_retention_time_label.hide()
        self.kon_5_max_retention_time_label = QLabel()
        self.kon_5_max_retention_time_label.hide()

        self.checkbox_label = QLabel("Choose transformation options: ", self)

        self.figure = Figure(figsize=(5, 4), dpi=100)


        # Create a subplot
        self.subplot = self.figure.add_subplot(111)

        # Create a FigureCanvas instance which serves as a QWidget displaying the figure
        self.canvas = FigureCanvas(self.figure)


        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(self.file_status)
        layout.addWidget(self.checkbox_label)
        layout.addWidget(self.remove_noise_checkbox)
        layout.addWidget(self.remove_data_before_spike_checkbox)
        layout.addWidget(self.normilize_checkbox)
        layout.addWidget(self.savitzky_golay_filter_checkbox)
        layout.addWidget(self.transform_data_button)
        layout.addWidget(self.export_to_excel_button)
        layout.addWidget(self.kon_2_min_retention_time_label)
        layout.addWidget(self.kon_2_max_retention_time_label)
        layout.addWidget(self.kon_5_min_retention_time_label)
        layout.addWidget(self.kon_5_max_retention_time_label)
        layout.addWidget(self.radio_button1)
        layout.addWidget(self.radio_button2)
        layout.addWidget(self.radio_button3)
        layout.addWidget(self.canvas)
        layout.addWidget(self.save_plot_button)


        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Signals and slots
        self.load_button.clicked.connect(self.load_file)
        self.export_to_excel_button.clicked.connect(self.save_file)
        self.transform_data_button.clicked.connect(self.transform_data)
        self.save_plot_button.clicked.connect(self.save_plot)
        self.button_group.buttonClicked.connect(self.set_plot)

        self.reset_data()

    def save_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", self.uploaded_file_name.split('/')[-1].split('.')[0], "PNG Files (*.png)")

        if file_path:
            self.figure.savefig(file_path)

    def reset_data(self):
        self.data = None
        self.transformed_data = None
        self.figure.clear()
        self.save_plot_button.hide()
        self.button_group.setExclusive(False)
        self.radio_button3.hide()
        self.radio_button3.setChecked(False)
        self.radio_button2.hide()
        self.radio_button2.setChecked(False)
        self.radio_button1.hide()
        self.radio_button1.setChecked(False)
        self.button_group.setExclusive(True)
        self.export_to_excel_button.setDisabled(True)
        self.transform_data_button.setDisabled(True)
        self.kon_2_max_retention_time_label.hide()
        self.kon_2_min_retention_time_label.hide()
        self.kon_5_max_retention_time_label.hide()
        self.kon_5_min_retention_time_label.hide()
        self.adjustSize()

    def set_plot(self, button):
        
        self.figure.clear()
        if button.text() == "Normilized":
            ax = self.figure.add_subplot(111)
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_2_normilized"], label="KON 2")
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_5_normilized"], label="KON 5")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Voltage")
            ax.set_title(self.uploaded_file_name.split('/')[-1].split('.')[0])
            ax.legend()
            
        elif button.text() == "Savitzky-golay":
            ax = self.figure.add_subplot(111)
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_2_smoothed"], label="KON 2")
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_5_smoothed"], label="KON 5")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Voltage")
            ax.set_title(self.uploaded_file_name.split('/')[-1].split('.')[0])
            ax.legend()
        else:
            ax = self.figure.add_subplot(111)
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_2_normilized"], label="KON 2")
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_2_smoothed"])
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_5_normilized"], label="KON 5")
            ax.plot(self.transformed_data["time (s)"], self.transformed_data["KON_5_smoothed"])
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Voltage")
            ax.set_title(self.uploaded_file_name.split('/')[-1].split('.')[0])
            ax.legend()

        self.canvas.draw()
        self.adjustSize()
        self.save_plot_button.show()
    

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import .DBF file...", "",
                                                   "dBase database file (*.DBF);;All Files (*)")
        self.reset_data()
        if file_name:
            self.file_status.setText(f"Uploaded file: {file_name.split('/')[-1]}")
            self.uploaded_file_name = file_name
            self.transform_data_button.setDisabled(False)
            table = DBF(file_name)
            records = [record for record in table]
            self.data = pd.DataFrame(records)

    def save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export excel to...", f"{self.uploaded_file_name[:-4]}.xlsx",
                                                   "Microsoft Excel Open XML Spreadsheet (*.xlsx);;All Files (*)")
        if file_name:
            self.transformed_data.to_excel(file_name)

    def transform_data(self):
        selected_data = self.data.drop(["DATE", "TIME", "MSEC", "SECSSS", "KON_1", "KON_4", "KON_6", "KON_7", "KON_8", "PRU_1"] + [f"TEP_{num}" for num in range(1,9)], axis=1)
        self.radio_button1.hide()
        self.radio_button2.hide()
        self.radio_button3.hide()

        # Calculate start of experiment
        spike_idx = selected_data[selected_data["KON_3"] != 0].index[0]

        if self.remove_noise_checkbox.isChecked():
            data_before_spike = selected_data.iloc[:spike_idx]
            selected_data["KON_2"] = selected_data["KON_2"] - data_before_spike["KON_2"].mean()
            selected_data["KON_5"] = selected_data["KON_5"] - data_before_spike["KON_5"].mean()

        if self.remove_data_before_spike_checkbox.isChecked():
            selected_data = selected_data.iloc[spike_idx:len(selected_data)-1] # Remove also last element
        selected_data["time (s)"] = [x * 0.5 for x in range(0, len(selected_data))]
        if self.normilize_checkbox.isChecked():
            selected_data["KON_2_normilized"] = (selected_data["KON_2"] - selected_data["KON_2"].min()) / (selected_data["KON_2"].max() - selected_data["KON_2"].min())
            selected_data["KON_5_normilized"] = (selected_data["KON_5"] - selected_data["KON_5"].min()) / (selected_data["KON_5"].max() - selected_data["KON_5"].min())
            self.radio_button1.show()
        if self.savitzky_golay_filter_checkbox.isChecked() and self.normilize_checkbox.isChecked():
            self.radio_button3.show()
            
        selected_data = selected_data.reset_index()
        spike_idx_kon2 = np.argmax([(sum(selected_data.iloc[idx-minus]["KON_2_normilized"] for minus in range(10)) - selected_data.iloc[idx-10]["KON_2_normilized"]) > 2 for idx in range(10, len(selected_data))])
        selected_data.loc[:spike_idx_kon2, "KON_2_normilized"] = 0.0
        spike_idx_kon5 = np.argmax([(sum(selected_data.iloc[idx-minus]["KON_5_normilized"] for minus in range(10)) - selected_data.iloc[idx-10]["KON_5_normilized"]) > 2 for idx in range(10, len(selected_data))])
        selected_data.loc[:spike_idx_kon5, "KON_5_normilized"] = 0.0

        if self.savitzky_golay_filter_checkbox.isChecked():
            selected_data["KON_2_smoothed"] = savgol_filter(selected_data["KON_2_normilized"], window_length=51, polyorder=4) 
            selected_data["KON_5_smoothed"] = savgol_filter(selected_data["KON_5_normilized"], window_length=51, polyorder=4) 
            selected_data.loc[:spike_idx_kon2, "KON_2_smoothed"] = 0.0
            selected_data.loc[:spike_idx_kon5, "KON_5_smoothed"] = 0.0
            self.radio_button2.show() 

        self.kon_2_min_retention_time_label.setText(f"KON 2 minimal retention time: {selected_data.loc[selected_data['KON_2_normilized'] != 0].iloc[0]['time (s)']}") 
        self.kon_5_min_retention_time_label.setText(f"KON 5 minimal retention time: {selected_data.loc[selected_data['KON_5_normilized'] != 0].iloc[0]['time (s)']}")

        self.kon_2_max_retention_time_label.setText(f"KON 2 maximal retention time: {selected_data.loc[np.argmax(selected_data['KON_2_normilized']), 'time (s)']}")
        self.kon_5_max_retention_time_label.setText(f"KON 5 maximal retention time: {selected_data.loc[np.argmax(selected_data['KON_5_normilized']), 'time (s)']}")  
        
        self.kon_2_max_retention_time_label.show()
        self.kon_2_min_retention_time_label.show()
        self.kon_5_max_retention_time_label.show()
        self.kon_5_min_retention_time_label.show()

        self.transformed_data = selected_data
        
        self.export_to_excel_button.setDisabled(False)
        
    
    


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
