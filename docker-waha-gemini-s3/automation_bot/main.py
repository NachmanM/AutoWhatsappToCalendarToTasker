from utils import process_messages
from utils import waha_session_check
from utils import waha_start_session
import time

try:
    time.sleep(15)
    waha_start_session.waha_start_session()

except Exception as e:
    print(e)

for s in range(120):
    try:
        session_status = waha_session_check.waha_session_check()
        if session_status == "WORKING":
            time.sleep(3)
            process_messages.process_messages()
            break
    except Exception as e:
        print(f"Error nach: {e}")

    time.sleep(2)
