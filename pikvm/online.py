import json, sys, urllib.request, socket, http.client
class C(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX); self.sock.connect("/run/kvmd/kvmd.sock")
try:
    c = C("localhost", timeout=5); c.request("GET", "/streamer"); s = json.load(c.getresponse())["result"]["streamer"]
    print(bool(s and s["source"]["online"]))
except Exception:
    print("unknown")
