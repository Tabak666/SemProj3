
from .api_client.models import Desk
from .api_client.calls import loadDesks

import threading
import time
from django.core.cache import cache


def updater_thread():

    print("Background API updater started!")
    while True:
        time.sleep(3) 
        try:
                data = loadDesks()
                cache.set("latest_desk_data", data, timeout=None) 
                
                print(f"API data updated at {time.strftime('%H:%M:%S')} | {len(data)} desks")
        
        except Exception as e:
            print(f"API failed: {e}")


thread = threading.Thread(target=updater_thread, daemon=True)
thread.start()