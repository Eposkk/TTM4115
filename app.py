import tkinter as tk
from tkinter import messagebox
import paho.mqtt.client as mqtt
import json

from env import STATION_TOPIC, BOOTH_TOPIC, BROKER, PORT

default_message = "See payment terminal after end session"
after_id = None
selected_charger_id = None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)
    client.subscribe(STATION_TOPIC)
    print("Connecting to {}:{}".format(STATION_TOPIC, PORT))


# Callback when a message is received from the MQTT broker
def on_message(client, userdata, msg):
    global selected_charger_id
    # Update the UI based on the MQTT message
    print(f"Received message: {msg}")
    payload = json.loads(msg.payload)
    print(f"Payload: {payload}")

    if (msg.topic == STATION_TOPIC):
        match payload["msg"]:
            case "available_chargers":
                data = payload['data']
                print(data)
                ready_chargers = sorted(
                        [charger['id'] for charger in data if charger['status'] == 'ready'],
                        key=lambda x: int(x)
                    )
                    
                out_of_order_chargers = sorted(
                        [charger['id'] for charger in data if charger['status'] == 'down'],
                        key=lambda x: int(x)
                    )
                
               # Extract valid charging times into a list
                valid_charging_times = [
                    int(float(charger['charging_time'])) 
                    for charger in data 
                    if charger['status'] != 'down' and 'charging_time' in charger
                ]

                # Find the minimum charging time or set to None if no valid chargers are available
                time_to_available = min(valid_charging_times) if valid_charging_times else 0

                update_next_available_label(f"Next Available: {time_to_available / 1000 / 60} min")

                print(ready_chargers, out_of_order_chargers)
                update_available_chargers_label(f"Available Chargers: {len(ready_chargers)}/{len(data)}")
                update_charger_options(ready_chargers)
                update_out_of_order_label('Chargers down (id): ' + ', '.join(out_of_order_chargers))
                
    elif (str(msg.topic).startswith(BOOTH_TOPIC)):
        match payload["msg"]:
            case "charging_started":
                update_charging_label(round(float(payload["charging_time"]) / 1000, 2)) 
            case "goal_reached":
                update_details_label("Charging completed")
                charger_selecter.config(state="normal")

# Function to publish a message to start charging
def start_charging():
    global selected_charger_id
    charger_id = selected_charger.get()
    client.publish(BOOTH_TOPIC + "/" + charger_id, json.dumps({"msg": "req", "percentage": number_entry.get(), "kWh": 100}))
    update_details_label("Waiting for charging to start")
    print("Start Charging", "Sent start command to Booth.")
    client.subscribe(BOOTH_TOPIC + "/" + charger_id)
    charger_selecter.config(state="disabled")
    selected_charger_id = charger_id
    



# Function to publish a message to end the charging session
def end_session():
    client.publish(BOOTH_TOPIC + "/" + selected_charger.get(), json.dumps({"msg": "gn"}))
    charger_selecter.config(state="normal")
    update_details_label(default_message)
    cancel_charging_update()


def request_stations():
    print("Requesting stations...")
    client.publish(
            STATION_TOPIC,
            json.dumps({"msg": "status"}),
        )


def update_charging_label(time_remaining):
    global after_id
    if time_remaining > 0:
        update_details_label(f"Charging started")
        time_display.config(text=f"{time_remaining} sec")
        after_id = root.after(1000, update_charging_label, time_remaining - 1)
    else:
        update_details_label("Charging complete. " + default_message)
        time_display.config(text="-- min")

def cancel_charging_update():
    global after_id
    if after_id:
        root.after_cancel(after_id)
        update_details_label("Charging stopped.")
        time_display.config(text="-- min")
        after_id = None  

# MQTT client setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message



try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    messagebox.showerror("MQTT Connection", f"Failed to connect to MQTT Broker: {e}")
    exit(1)

client.loop_start()  # Start the loop once

# Initialize and run the Tkinter main loop
root = tk.Tk()
root.title("Charging App UI")

selected_charger = tk.StringVar(root)

# UI elements
next_available_label = tk.Label(root, text="Next Available: 0 min")
available_chargers_label = tk.Label(root, text="Available Chargers: 12/20")
out_of_order_label = tk.Label(root, text="#7 out of order", fg="red")
charging_time_label = tk.Label(root, text="Time until charging complete:")
time_display = tk.Label(root, text="-- min")
details_label = tk.Label(root, text=default_message)
input_label = tk.Label(root, text="Insert percentage")
charger_selecter = tk.OptionMenu(root, selected_charger, "No chargers available")
charger_selecter.config(state="disabled")

def validate_number(P):
    """ Validate the entry field to accept only numbers between 0 and 100. """
    if P.strip() == "":  # Allow the entry to be cleared
        return True
    try:
        value = int(P)
        if 0 <= value <= 100:
            return True
    except ValueError:
        pass
    return False

# Register the validator function with the Tkinter window
validate_command = root.register(validate_number)

# Create and grid the Entry widget with validation for number input
number_entry = tk.Entry(root, validate="key", validatecommand=(validate_command, '%P'))
number_entry.insert(0, "50") 


# Start and End session buttons
start_button = tk.Button(
    root, text="START CHARGING", command=start_charging, bg="green"
)
end_button = tk.Button(root, text="END SESSION", command=end_session, bg="red")




# Layout
available_chargers_label.grid(row=0, column=0, sticky="W")
out_of_order_label.grid(row=0, column=1, sticky="E")
charging_time_label.grid(row=3, column=0, columnspan=2)
next_available_label.grid(row=1, column=0, columnspan=2)
time_display.grid(row=4, column=0, columnspan=2)
input_label.grid(row=5, column=0, padx=10)
number_entry.grid(row=5, column=1)
start_button.grid(row=6, column=0, pady=10)
end_button.grid(row=6, column=1, pady=10)
details_label.grid(row=7, column=0, columnspan=2)
charger_selecter.grid(row=2, column=0, columnspan=2)


# Set default value
selected_charger.set("Charger 1")

def update_next_available_label(text):
    next_available_label.config(text=text)

def update_out_of_order_label(text):
    out_of_order_label.config(text=text)

# Function to update the details label
def update_details_label(text):
    details_label.config(text=text)

def update_available_chargers_label(text):
    available_chargers_label.config(text=text)

def update_charger_options(new_options):
    # Clear the current options
    charger_selecter['menu'].delete(0, 'end')
    
    # If no new options provided, revert to default list
    if not new_options:
        new_options = ["No chargers available"]
        charger_selecter.config(state="disabled")

        
    # Add new options
    for option in new_options:
        charger_selecter['menu'].add_command(label=option, command=lambda value=option: selected_charger.set(value))
    
    # Set the first option as default if new options are provided
    if new_options:
        selected_charger.set(new_options[0])
        charger_selecter.config(state="active")

def on_shutdown():
    # Code to run before shutting down
    print("Shutting down...")
    client.publish(BOOTH_TOPIC + "/" + selected_charger.get(), "err")
    client.disconnect()
    root.destroy()
    # Add your code here

root.protocol("WM_DELETE_WINDOW", on_shutdown)

root.after(10, request_stations)
# Run the Tkinter main loop
root.mainloop()

