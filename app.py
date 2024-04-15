import tkinter as tk
from tkinter import messagebox
import paho.mqtt.client as mqtt


# MQTT settings
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "charging_station/status"
MQTT_SEND_TOPIC = "charging_station/control"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)
    client.subscribe(MQTT_TOPIC)


# Callback when a message is received from the MQTT broker
def on_message(client, userdata, msg):
    # Update the UI based on the MQTT message
    message = str(msg.payload.decode("utf-8"))
    print(f"Received message '{message}' on topic '{msg.topic}'")

    # Here you should have logic to update the UI based on the message content
    # For now, we just print the message to the console


# Function to publish a message to start charging
def start_charging():
    client.publish(MQTT_SEND_TOPIC, "start")
    messagebox.showinfo("Start Charging", "Sent start command to charging station.")


# Function to publish a message to end the charging session
def end_session():
    client.publish(MQTT_SEND_TOPIC, "stop")
    messagebox.showinfo("End Session", "Sent stop command to charging station.")


# MQTT client setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message


# Connect to MQTT broker
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    messagebox.showerror("MQTT Connection", f"Failed to connect to MQTT Broker: {e}")
    exit(1)


# Initialize the main window
root = tk.Tk()
root.title("Charging App UI")


# UI elements
available_chargers_label = tk.Label(root, text="Available Chargers: 12/20")
out_of_order_label = tk.Label(root, text="#7 out of order", fg="red")
next_available_label = tk.Label(root, text="Next Available: 0 min")
charging_time_label = tk.Label(root, text="Time until charging complete:")
time_display = tk.Label(root, text="15 min")
details_label = tk.Label(root, text="See payment terminal after end session")


# Layout
available_chargers_label.grid(row=0, column=0, sticky="W")
out_of_order_label.grid(row=0, column=1, sticky="E")
next_available_label.grid(row=1, column=0, columnspan=2)
charging_time_label.grid(row=3, column=0, columnspan=2)
time_display.grid(row=4, column=0, columnspan=2)
details_label.grid(row=6, column=0, columnspan=2)


# Start and End session buttons
start_button = tk.Button(
    root, text="START CHARGING", command=start_charging, bg="green"
)
end_button = tk.Button(root, text="END SESSION", command=end_session, bg="red")
start_button.grid(row=5, column=0, pady=10)
end_button.grid(row=5, column=1, pady=10)


# Function to periodically call MQTT loop
def mqtt_loop():
    client.loop_start()
    root.after(100, mqtt_loop)


# Start the MQTT loop
mqtt_loop()


# Run the Tkinter main loop
root.mainloop()
