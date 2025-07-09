import requests
def get_current_time() -> int:
    response = requests.get("https://127.0.0.1:2999/replay/playback", verify=False)
    return response.json()["time"]*1000



def set_time(time: int) -> None:
    body = {
        "length": 0,
        "paused": False,
        "seeking": True,
        "speed": 1,
        "time": time
    }
    response = requests.post("https://127.0.0.1:2999/replay/playback", json=body, verify=False)
    return response.json()
