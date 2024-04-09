from stmpy import Driver, Machine
from threading import Thread
import json 

import paho.mqtt.client as mqtt
from env import STATION_TOPIC, BOOTH_TOPIC, BROKER, PORT


class Booth:
    def im_occupied(self, id):
        print("im_occupied triggered! id: " +id)
        self.mqtt_client.publish(BOOTH_TOPIC, {"msg": "occupied", "id": id})
    def im_down(self, id):
        print("im_down triggered!")
        self.mqtt_client.publish(BOOTH_TOPIC, {"msg": "down", "id": id})
    def im_ready(self, id):
        print("im_ready triggered!")
        self.mqtt_client.publish(BOOTH_TOPIC, {"msg": "ready", "id": id})

# initial transition
t0 = {"source": "initial", "target": "operative", "effect": "register(*)"}

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
    "target": "out_of_order"
}

s = {
    "name": "operative",
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
        if(payload["msg"] != "booth" and payload["msg"] != "occupied" and payload["msg"] != "down" and payload["msg"] != "ready"):
            print(payload["msg"] + " is not a valid message ignoring")
        
        else:

            if(payload["msg"] == "occupied"):
                self.stm_driver.send("occupied", "booth", args=[payload["id"]])
            elif(payload["msg"] == "down"):
                self.stm_driver.send("down", "booth", args=[payload["id"]])
            elif(payload["msg"] == "ready"):
                self.stm_driver.send("ready", "booth", args=[payload["id"]])
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


booth = Booth()
booth_machine = Machine(transitions=[t0, t1, t2, t3, t4], states=[s, s1], obj=booth, name="booth")
booth.stm = booth_machine

driver = Driver()
driver.add_machine(booth_machine)

myclient = MQTT_Client_1()
booth.mqtt_client = myclient.client
myclient.stm_driver = driver

driver.start()
myclient.start(BROKER, PORT)