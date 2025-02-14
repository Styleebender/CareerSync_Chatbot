import os
import random
from dotenv import load_dotenv

load_dotenv()

def get_scrapin_random_api_key():
    keys = os.getenv("SCRAPIN_API_KEY")
    key_list = keys.split(",")
    return random.choice(key_list)

# print(get_scrapin_random_api_key())