from dotenv import load_dotenv
import os

load_dotenv()

STATION_TOPIC = os.getenv("STATION_TOPIC")
BOOTH_TOPIC = os.getenv("BOOTH_TOPIC")
BROKER = os.getenv("BROKER")
PORT = int(os.getenv("PORT"))