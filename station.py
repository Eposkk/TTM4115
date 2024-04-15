from stmpy import Driver, Machine
from threading import Thread
import json
import os
import random

import paho.mqtt.client as mqtt

from env import STATION_TOPIC, BOOTH_TOPIC, BROKER, PORT, DB_PATH


class DB:
    # Write a simple DB driver for reading and writing to a JSON file
    def __init__(self):
        self.charging_stations = {}
        self.database_file = os.path.join(os.getcwd(), str(DB_PATH))
        self.load()

    def load(self):
        try:
            with open(self.database_file, "r") as file:
                self.charging_stations = json.load(file)
        except FileNotFoundError:
            self.charging_stations = {}

    def save(self):
        with open(self.database_file, "w") as file:
            json.dump(self.charging_stations, file)

    def add_booth(self, booth_id):
        self.charging_stations[booth_id] = {"status": "free"}
        self.save()

    def remove_booth(self, booth_id):
        del self.charging_stations[booth_id]
        self.save()

    def set_booth_status(self, booth_id, status):
        self.charging_stations[booth_id]["status"] = status
        self.save()

    def get_booth_status(self, booth_id):
        return self.charging_stations[booth_id]["status"]

    def generate_sample_data(self, num):
        for i in range(num):
            self.add_booth(i)

    def generate_id(self):
        id = 0
        while str(id) in self.charging_stations:
            id += 1
        return str(id)


class Station:
    def __init__(self):
        self.DB = DB()
        self.stm = None
        self.mqtt_client = None

    def im_occupied(self, args):
        id = args[0]
        print("imOccupied triggered! id: " + id)
        self.DB.set_booth_status(id, "occupied")
        self.mqtt_client.publish(STATION_TOPIC, {"msg": "occupied", "id": id})

    def im_down(self, args):
        id = args[0]
        print("imDown triggered!")
        self.DB.set_booth_status(id, "occupied")
        self.mqtt_client.publish(STATION_TOPIC, {"msg": "down", "id": id})

    def im_ready(self, args):
        id = args[0]
        print("imReady triggered!")
        self.DB.set_booth_status(id, "ready")
        self.mqtt_client.publish(STATION_TOPIC, {"msg": "ready", "id": id})

    def im_error(self):
        print("Station has an error")
        self.mqtt_client.publish(STATION_TOPIC, {"msg": "Station is down"})

    def register_booth(self, args):
        one_time_id = args[0]
        id = self.DB.generate_id()
        self.DB.add_booth(id)
        self.mqtt_client.publish(
            BOOTH_TOPIC, {"msg": "registered", "id": id, "one_time_id": one_time_id}
        )


# initial transition
t0 = {"source": "initial", "target": "operative"}

t1 = {
    "trigger": "occupied",
    "source": "operative",
    "target": "operative",
    "effect": "im_occupied(*)",
}

t2 = {
    "trigger": "down",
    "source": "operative",
    "target": "operative",
    "effect": "im_down(*)",
}

t3 = {
    "trigger": "ready",
    "source": "operative",
    "target": "operative",
    "effect": "im_ready(*)",
}

t4 = {
    "trigger": "sys_err",
    "source": "operative",
    "target": "out_of_order",
    "effect": "im_error(*)",
}

t5 = {
    "trigger": "register_booth",
    "source": "operative",
    "target": "operative",
    "effect": "register_booth(*)",
}

s = {
    "name": "opeartive",
}

s1 = {
    "name": "out_of_order",
}


class MQTT_Client_1:
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
        if (
            payload["msg"] != "station"
            and payload["msg"] != "occupied"
            and payload["msg"] != "down"
            and payload["msg"] != "ready"
            and payload["msg"] != "register"
        ):
            print(payload["msg"] + " is not a valid message ignoring")

        else:

            if payload["msg"] == "occupied":
                self.stm_driver.send("occupied", "station", args=[payload["id"]])
            elif payload["msg"] == "down":
                self.stm_driver.send("down", "station", args=[payload["id"]])
            elif payload["msg"] == "ready":
                self.stm_driver.send("ready", "station", args=[payload["id"]])
            elif payload["msg"] == "register":
                self.stm_driver.send(
                    "register_booth", "station", args=[payload["one_time_id"]]
                )
            else:
                print("This should not happen")

    def start(self, broker, port):

        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe(STATION_TOPIC)

        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()


station = Station()
station_machine = Machine(
    transitions=[t0, t1, t2, t3, t4], states=[s, s1], obj=station, name="station"
)
station.stm = station_machine

driver = Driver()
driver.add_machine(station_machine)

myclient = MQTT_Client_1()
station.mqtt_client = myclient.client
myclient.stm_driver = driver

driver.start()
myclient.start(BROKER, PORT)
