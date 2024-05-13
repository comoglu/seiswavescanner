# SeisWaveScanner with scrttv

This Python application is a graphical user interface (GUI) for the SeisWaveScanner with scrttv. It allows users to specify parameters for the SeisWaveScanner and execute it with the click of a button.

## Dependencies

This application is written in Python 3 and uses the PyQt5 library for the GUI. Make sure you have the following dependencies installed:

- Python 3
- PyQt5

You can install these with pip:

    pip install PyQt5

## Usage

1. **Run the application**: To run the application, open your terminal and navigate to the directory containing `seiscwavescanner.py`. Then, execute the Python script using the following command:

    python3 seiswavescanner.py

2. **Enter the parameters**: The application presents a form where you can enter the following parameters:

    - **End Time (UTC)**: The end time for the SeisWaveScanner. You can also reset the time to the current time with the 'Reset Time Now' button.
    - **Buffer Length (hours)**: The buffer length for the SeisWaveScanner, in hours.
    - **Recordstream**: The protocol for the SeisWaveScanner. Options are 'FDSNWS', 'SLINK', 'ROUTER', and 'IRIS-FDSNWS'.
    - **Stream Codes**: The stream codes for the SeisWaveScanner. You can enter your own stream codes or select a predefined set of stations from the dropdown menu.
    - **Show Picks?**: A checkbox to include the `--showPicks` option in the SeisWaveScanner command.
    - **--no-inventory?**: A checkbox to include the `--no-inventory` option in the SeisWaveScanner command.
    - **--offline?**: A checkbox to include the `--offline` option in the SeisWaveScanner command.

3. **Execute the command**: After entering the parameters, click the 'OK' button to execute the SeisWaveScanner command.

4. **Quit the application**: The 'Quit' button will close the application.

