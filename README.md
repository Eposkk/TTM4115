# EV Charging Station Management System (TTM4115)

## Overview
This repository contains the code for a networked EV Charging Station Management System, which includes a Charging Booth, Charging Station, and a User App. The system uses MQTT for communication and features a Tkinter-based GUI for interaction.

## Components
- **Charging Booth**: Manages individual charging processes and communicates status.
- **Charging Station**: Oversees multiple charging booths and maintains overall status.
- **User App**: Allows users to interact with the system, start/stop charging, and view booth statuses.

Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
Run the different components using Python:
```
python booth.py
```
```
python station.py
```

```
python app.py
```

Ensure MQTT broker details are correctly set in the `env.py` file before starting the system.
