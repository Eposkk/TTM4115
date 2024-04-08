from stmpy import Driver, Machine
from threading import Thread
import json 

import paho.mqtt.client as mqtt

STATION_TOPIC = "ntnu/group_10/station"
BOOTH_TOPIC = "ntnu/group_10/booth"


class Station:
    def im_occupied(self, id):
        print("imOccupied triggered! id: " +id)
        self.mqtt_client.publish("group_10_quiz_answers", "buzzed was triggered!"+ id + " was first")
    def on_question(self, id):
        print("onQuestion triggered!")
        #self.mqtt_client.publish("group_10_quiz_answers", "QuizMaster asked a question be the first to station")
    def on_idle(self, id):
        print("onIdle triggered!")
        #self.mqtt_client.publish("group_10_quiz_answers", "QuizMaster is idle")

# initial transition
t0 = {"source": "initial", "target": "operative"}

t1 = {
    "trigger": "occupied",
    "source": "operative",
    "target": "operative",
    "effect": "im_occupied(*)"
}

t2 = {
    "trigger": "down",
    "source": "operative",
    "target": "operative",
    "effect" : "im_down(*)"
}

t3 = {
    "trigger": "ready",
    "source": "operative",
    "target": "operative",
    "effect" : "im_ready(*)"
}

t4 = {
    "trigger": "sys_err",
    "source": "operative",
    "target": "operative"
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
        if(payload["msg"] != "station" and payload["msg"] != "occupied" and payload["msg"] != "down" and payload["msg"] != "ready"):
            print(payload["msg"] + " is not a valid message ignoring")
        
        else:

            if(payload["msg"] == "occupied"):
                self.stm_driver.send("occupied", "station", args=[payload["id"]])
            elif(payload["msg"] == "down"):
                self.stm_driver.send("down", "station", args=[payload["id"]])
            elif(payload["msg"] == "ready"):
                self.stm_driver.send("ready", "station", args=[payload["id"]])
            else:
                print("This should not happen")
        #self.stm_driver.send(payload["msg"],"buzzer")


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

broker, port = "broker.hivemq.com", 1883

station = Station()
station_machine = Machine(transitions=[t0, t1, t2, t3, t4], states=[s, s1], obj=station, name="station")
station.stm = station_machine

driver = Driver()
driver.add_machine(station_machine)

myclient = MQTT_Client_1()
station.mqtt_client = myclient.client
myclient.stm_driver = driver

driver.start()
myclient.start(broker, port)