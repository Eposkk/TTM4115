from stmpy import Driver, Machine
from threading import Thread
import json

import paho.mqtt.client as mqtt
from env import STATION_TOPIC, BOOTH_TOPIC, BROKER, PORT
import uuid
import atexit


class Booth:
    def __init__(self):
        self.Id = None
        self.one_time_id = uuid.uuid4()
        self.mqtt_client = None
        print("onetimeid" + str(self.one_time_id))

    def send_message(self, msg):
        match msg:
            case "ready":
                print("im_ready triggered!")
                self.mqtt_client.publish(
                    STATION_TOPIC, json.dumps({"msg": "ready", "id": self.Id})
                )
            case "occupied":
                print("im_occupied triggered! id: " + str(id))
                self.mqtt_client.publish(
                    STATION_TOPIC, json.dumps({"msg": "occupied", "id": self.Id})
                )
            case "down":
                print("im_down triggered!")
                self.mqtt_client.publish(
                    STATION_TOPIC, json.dumps({"msg": "down", "id": self.Id})
                )

    def registered(self, *args):
        one_time_id = args[0]
        id = args[1]
        print(
            "registered triggered! with id: " + id + " and one_time_id: " + one_time_id
        )
        if str(self.one_time_id) == one_time_id:
            self.Id = id
        else:
            print(
                "Invalid one_time_id, not ours"
                + "Self one time: "
                + str(self.one_time_id)
                + " Gotten one time: "
                + str(one_time_id)
            )
        self.mqtt_client.subscribe(str(BOOTH_TOPIC) + "/" + str(self.Id))
        print("subscribed to: " + str(BOOTH_TOPIC) + "/" + str(self.Id))
        atexit.register(self.reset_booth)

    def register(self):
        print("register triggered!")
        self.mqtt_client.publish(
            STATION_TOPIC,
            json.dumps({"msg": "register_booth", "one_time_id": str(self.one_time_id)}),
        )

    def releasePwR(self):
        print("releasePwR triggered!")

    def reset_booth(self):
        self.mqtt_client.publish(
            STATION_TOPIC, json.dumps({"msg": "remove_booth", "id": str(self.Id)})
        )


# initial transition
t0 = {"source": "initial", "target": "waiting", "effect": "register"}

te = {
    "trigger": "err",
    "source": "standby",
    "target": "out_of_order",
}

te1 = {
    "trigger": "err",
    "source": "connecting",
    "target": "out_of_order",
}

te2 = {
    "trigger": "err",
    "source": "charging",
    "target": "out_of_order",
}

te3 = {
    "trigger": "err",
    "source": "goal_reached",
    "target": "out_of_order",
}

t4 = {"trigger": "req", "source": "standby", "target": "connecting"}

t5 = {"trigger": "ce", "source": "connecting", "target": "charging"}

t6 = {"trigger": "gn", "source": "charging", "target": "goal_reached"}

t7 = {"trigger": "cl", "source": "goal_reached", "target": "standby"}

t8 = {
    "trigger": "registered",
    "source": "waiting",
    "target": "standby",
    "effect": "registered(*)",
}

t9 = {
    "trigger": "reset",
    "source": "out_of_order",
    "target": "standby",
    "effect": "reset_booth",
}

s = {
    "name": "standby",
    "entry": "send_message('ready')",
}

s0 = {
    "name": "waiting",
}

s1 = {
    "name": "out_of_order",
    "entry": "send_message('down')",
}

s2 = {
    "name": "charging",
    "entry": "send_message('occupied'); start_timer('gn', 5000)",
}

s3 = {"name": "connecting", "entry": "start_timer('ce', 5000)"}

s4 = {"name": "goal_reached", "entry": "releasePwR"}


class MQTT_Client_1:
    def __init__(self, topic_id=""):
        self.count = 0
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.topic_id = topic_id

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):

        print(msg)
        payload = json.loads(msg.payload)

        print("on_message(): topic: {}, message: {}".format(msg.topic, payload["msg"]))
        if (
            payload["msg"] != "registered"
            and payload["msg"] != "req"
            and payload["msg"] != "ce"  # maybe should be a timer
            and payload["msg"] != "gn"
            and payload["msg"] != "cl"
            and payload["msg"] != "err"
            and payload["msg"] != "reset"
        ):
            print(payload["msg"] + " is not a valid message ignoring")
        elif (msg.topic == str(BOOTH_TOPIC) + str(self.topic_id)):
            match payload["msg"]:
                case "registered":
                    print("registered")
                    self.stm_driver.send(
                        "registered",
                        "booth",
                        args=[payload["one_time_id"], payload["id"]],
                    )
                case _:
                    print("Error, this topic only lists to registered")
        else:
            match payload["msg"]:
                case "req":
                    print("request")
                    self.stm_driver.send("req", "booth")
                case "ce":
                    print("comlink established")
                    self.stm_driver.send("ce", "booth")
                case "gn":
                    print("goal notifcation")
                    self.stm_driver.send("gn", "booth")
                case "cl":
                    print("comlink lost")
                    self.stm_driver.send("cl", "booth")
                case "registered":
                    print("registered")
                    self.stm_driver.send(
                        "registered",
                        "booth",
                        args=[payload["one_time_id"], payload["id"]],
                    )
                case "err":
                    self.stm_driver.send("err", "booth")
                case "reset":
                    print("reset")
                    self.stm_driver.send("reset", "booth")
                case _:
                    print("This topic does not listen to that msg")

    def start(self, broker, port):

        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe(str(BOOTH_TOPIC) + str(self.topic_id))

        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()


booth = Booth()
booth_machine = Machine(
    transitions=[t0, te, te1, te2, te3, t4, t5, t6, t7, t8, t9],
    states=[s, s1, s2, s3, s4],
    obj=booth,
    name="booth",
)
booth.stm = booth_machine

driver = Driver()
driver.add_machine(booth_machine)

myclient = MQTT_Client_1()
booth.mqtt_client = myclient.client

myclient.stm_driver = driver

myclient.start(BROKER, PORT)
driver.start()
