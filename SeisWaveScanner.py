#!/usr/bin/env python3

import os
import subprocess
import random
import getpass
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFormLayout, QLineEdit, QComboBox, QDateTimeEdit, QCheckBox, QMessageBox, QHBoxLayout, QLabel, QGridLayout
from PyQt5.QtCore import Qt, QTime, QDate, QDateTime, QTimer

# Configuration Variables
BUFFER_SIZE = ["0.1","0.5","1","2","3","4","5","6","7","8","9","10","11","12","24","36","48"]
PROTO_LIST = ["FDSNWS","SLINK","ROUTER","IRIS-FDSNWS","CAPS-SERVER"]
PROTO_LIST_TOOLTIPS = {
    "FDSNWS": "FDSN Web Service: Request the waveform data from local FDSNWS Service",
    "SLINK": "SeedLink: Request the waveform data from local SeedLink",
    "ROUTER": "Request data from separate sources using Router API",
    "IRIS-FDSNWS": "IRIS FDSN Web Service: Request the waveform data from IRIS FDSNWS Service",
    "CAPS-SERVER": "Request the data from localhost CAPS-SERVER"
}

class Form(QWidget):
    def __init__(self):
        super().__init__()
        self.remote_host = f"localhost:18180"
        self.db_strg = f"mysql://sysop:sysop@$localhost:3306/seiscomp"

        # Create a QCheckBox widget for showPicks
        self.showPicksCheck = QCheckBox()
        self.showPicksCheck.setToolTip('Check this box to show picks')

        # Create QCheckBox widgets for noInventory and offline
        self.noInventoryCheck = QCheckBox()
        self.noInventoryCheck.setToolTip('Check this box to include --no-inventory in the command')
        self.offlineCheck = QCheckBox()
        self.offlineCheck.setToolTip('Check this box to include --offline in the command')

        # Actual stream codes corresponding to the placeholders
        self.actual_stream_codes = {
            "Australia": "AU.*.*.?HZ,II.WRAB.00.BHZ,IM.AS31..BHZ,IU.MBWA.00.BHZ,IU.NWAO.*.BHZ,G.CAN.00.BHZ",
            "Australian Arrays": "AU.AS*..?HZ,AU.WB..?HZ,AU.WC..?HZ,,AU.WR..?HZ,AU.PS*.00.?HZ,IM.AS*..?HZ,IM.WB..?HZ,IM.WC..?HZ,IM.WR..?HZ",
            "Fijian Stations": "FJ.*.*.?HZ",
        }

        self.initUI()

    def initUI(self):
        self.setWindowTitle('SeisWaveScanner with scrttv')

        # Create layout
        layout = QGridLayout()
        self.setLayout(layout)

        # Create form layout
        formLayout = QFormLayout()

        # Create widgets
        self.endTimeEdit = QDateTimeEdit(QDateTime.currentDateTimeUtc())
        self.endTimeEdit.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.endTimeEdit.setTimeSpec(Qt.UTC)
        self.endTimeEdit.setToolTip('Enter the end time in UTC')

        self.resetTimeNowButton = QPushButton('Reset Time Now')
        self.resetTimeNowButton.clicked.connect(self.reset_time_now)
        self.resetTimeNowButton.setToolTip('Click to reset time to now')

        # Create a horizontal layout to hold the end time edit and reset time now button
        endTimeLayout = QHBoxLayout()
        endTimeLayout.addWidget(self.endTimeEdit)
        endTimeLayout.addWidget(self.resetTimeNowButton)

        self.bufferSizeCombo = QComboBox()
        self.bufferSizeCombo.addItems(BUFFER_SIZE)
        self.bufferSizeCombo.setEditable(True)
        self.bufferSizeCombo.setToolTip('Type or Select the buffer length from the list (in hours)')

        self.protocolCombo = QComboBox()
        self.protocolCombo.addItems(PROTO_LIST)
        for i in range(self.protocolCombo.count()):
            proto = self.protocolCombo.itemText(i)
            self.protocolCombo.setItemData(i, PROTO_LIST_TOOLTIPS[proto], Qt.ToolTipRole)
        self.protocolCombo.setToolTip('Select the protocol')

        # Create a QComboBox widget for stream codes
        self.streamsCombo = QComboBox(self)
        self.streamsCombo.setEditable(True)  # Allow the user to enter their own stream codes
        self.streamsCombo.setToolTip('Enter Streams Codes in format of (NET.STA.LOC.CHA) like AU.ARMA.*.?HZ \n or select predefined set of stations from dropdown menu')

        # Add items with different stream codes
        stream_codes_list = [
            "Fijian Stations",
            "Australia",
            "Australian Arrays",
        ]

        for stream_codes in stream_codes_list:
            self.streamsCombo.addItem(stream_codes)

        # Connect the currentIndexChanged signal to a function
        self.streamsCombo.currentIndexChanged.connect(self.change_streams)

        # Add widgets to form layout
        formLayout.addRow('End Time (UTC)', endTimeLayout)
        formLayout.addRow('Buffer Length (hours)', self.bufferSizeCombo)
        formLayout.addRow('Recordstream', self.protocolCombo)
        formLayout.addRow('Stream Codes', self.streamsCombo) # Add the stream codes widget to the form layout
        formLayout.addRow('Show Picks?', self.showPicksCheck) # Add the showPicks checkbox to the form layout
        formLayout.addRow('--no-inventory?', self.noInventoryCheck)
        formLayout.addRow('--offline?', self.offlineCheck)

        # Add form layout to main layout
        layout.addLayout(formLayout, 1, 0, 1, 2)

        # Create buttons
        quitButton = QPushButton('Quit', self)
        quitButton.setToolTip('Click to quit the application')
        okButton = QPushButton('OK', self)
        okButton.setToolTip('Click to submit the form')

        # Connect signals
        quitButton.clicked.connect(self.quit)
        okButton.clicked.connect(self.ok)

        # Add buttons to layout
        layout.addWidget(quitButton, 2, 0)
        layout.addWidget(okButton, 2, 1)

        # Create a QLabel for the clock
        self.clock = QLabel()
        self.clock.setStyleSheet("background-color: yellow;")
        layout.addWidget(self.clock, 0, 1, Qt.AlignRight)

        # Create a QTimer, connect its timeout signal to the update_clock method, and start it
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)  # update every second

    def quit(self):
        QApplication.quit()

    def ok(self):
        # Parse Form Data
        form_end_time_str = self.endTimeEdit.text()

        # Validate Form Data
        try:
            form_end_time = datetime.strptime(form_end_time_str, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            logging.error("Invalid date or time format. Please use dd/MM/yyyy for date and HH:mm:ss for time. Exiting.")
            exit(1)

        if form_end_time > datetime.utcnow():
            QMessageBox.warning(self, 'Error', 'Selected date is in the future, Try again.')
        else:
            form_buffer = self.bufferSizeCombo.currentText()
            form_protocol = self.protocolCombo.currentText()
            form_showPicks = self.showPicksCheck.isChecked() # Get the showPicks status from the checkbox
            form_noInventory = self.noInventoryCheck.isChecked() # Get the noInventory status from the checkbox
            form_offline = self.offlineCheck.isChecked() # Get the offline status from the checkbox

            # Determine Endpoint
            if form_protocol == 'FDSNWS':
                endpoint = f"fdsnws://localhost:8081"
            elif form_protocol == 'SLINK':
                endpoint = f"slink://localhost:18000"
            elif form_protocol == 'ROUTER':
                endpoint = f"router:///opt/seiscomp/etc/router.conf"
            elif form_protocol == 'IRIS-FDSNWS':
                endpoint = f"fdsnws://service.iris.edu"
            elif form_protocol == 'CAPS-SERVER':
                endpoint = f"caps://localhost:18002"

            # Get the stream codes from the dropdown menu
            selected_stream_codes = self.streamsCombo.currentText()
            stream_codes = self.actual_stream_codes.get(selected_stream_codes, selected_stream_codes)

            # Determine Buffer Size
            buffer_size = int(float(form_buffer or 0) * 3600)

            # Calculate Buffer End Time
            form_buffer_end_time = form_end_time - timedelta(seconds=buffer_size)

            # Construct Command
            sc3cmd = f"scrttv --debug -u {random.randint(0, 10000)}-{getpass.getuser()} -H {self.remote_host} -d {self.db_strg} --maxDelay=0 -I \
                      {endpoint} --resortAutomatically=\"false\" --autoApplyFilter=\"true\" \
                      --buffer-size=\"{buffer_size}\"  --start-time=\"{form_buffer_end_time}\" --end-time=\"{form_end_time}\" --streams.codes=\"{stream_codes}\" \
                      --scheme.colors.records.foreground=\"000000\" \
                      --scheme.colors.records.background=\"ffffff\" \
                      --scheme.colors.records.alternateBackground=\"ffffff\" \
                      --scheme.colors.records.gaps=\"ff7f7f\" \
                      --showPicks={str(form_showPicks).lower()} \
                      {'--no-inventory' if form_noInventory else ''} \
                      {'--offline' if form_offline else ''} \
                      "

            # Execute Command
            try:
                subprocess.run(sc3cmd, shell=True)
                print("Command executed successfully!")
            except Exception as e:
                print(f"An error occurred: {e}")

    def change_streams(self):
        # Set the stream codes variable to the current text
        stream_codes = self.streamsCombo.currentText()

        # Print the stream codes for debugging
        print("Stream codes:", stream_codes)

    def reset_time_now(self):
        # Reset the end time to the current time
        self.endTimeEdit.setDateTime(QDateTime.currentDateTime().toUTC())
    def update_clock(self):
        # Update the clock label with the current time
        current_time = QDateTime.currentDateTimeUtc()
        self.clock.setText("Current Date and Time (UTC): " + current_time.toString('yyyy/MM/dd hh:mm:ss'))

if __name__ == '__main__':
    app = QApplication([])
    form = Form()
    form.show()
    app.exec_()
