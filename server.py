import json
import os
from threading import Thread
import paho.mqtt.client as mqtt

from env import STATION_TOPIC, BOOTH_TOPIC, BROKER, PORT, DB_PATH


# Construct the relative path to the JSON database file
database_file = os.path.join(os.getcwd(), str(DB_PATH))

# Load existing charging station data from JSON database
try:
    with open(database_file, "r") as file:
        charging_stations = json.load(file)
except FileNotFoundError:
    charging_stations = {}

"""
    def im_occupied(self, id):
        print("im_occupied triggered! id: " +id)
        self.mqtt_client.publish(BOOTH_TOPIC, {"msg": "occupied", "id": id})
    def im_down(self, id):
        print("im_down triggered!")
        self.mqtt_client.publish(BOOTH_TOPIC, {"msg": "down", "id": id})
    def im_ready(self, id):
        print("im_ready triggered!")
        self.mqtt_client.publish(BOOTH_TOPIC, {"msg": "ready", "id": id})
"""
class MQTT_Client:
    def __init__(self):
        self.count = 0
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        
        payload = json.loads(msg.payload)

        print("on_message(): topic: {}, message: {}".format(msg.topic, payload["msg"]))
        if(msg.topic == BOOTH_TOPIC):
            match payload["msg"]:
                case "occupied":
                    print("station")
                case "down":
                    print("station")
                case "ready":
                    print("station")


    def start(self, broker, port):

        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe(STATION_TOPIC)
        self.client.subscribe(BOOTH_TOPIC)

        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()


myclient = MQTT_Client()
myclient.start(BROKER, PORT)

# Main loop
while True:
    # Do something with the charging station data
    print("Charging station data:", charging_stations, end="\r")