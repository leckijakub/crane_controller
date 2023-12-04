# import time

# while True:
#     print("Hello World")
#     time.sleep(1)

import usocket as socket
from uselect import select
import uasyncio as asyncio
import network
import esp
import gc
from captive_dns_server.server import CaptiveDNSServer


def client_handler(client):
    html = """<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body><h1>Hello, MicroPython!</h1></body></html>"""
    response = html
    print('Got a connection from %s' % str(client))
    client.send(response)
    client.close()

async def web_server():
    try:
        # addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        # s = socket.socket()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        s.bind(('', 80))
        # s.bind(addr)
        s.listen(1)
    except Exception as e:
        print(f"Failed to bind to port: {e}")
        return
    while True:
        r, w, err = select((s,), (), (), 0)
        if r:
            for readable in r:
                cl, addr = s.accept()
                try:
                    client_handler(cl)
                except OSError as e:
                    pass
        # conn, addr = s.accept()
        # print('Got a connection from %s' % str(addr))
        # request = conn.recv(1024)
        # print('Content = %s' % str(request))
        # response = web_page()
        # conn.send(response)
        # conn.close()


from microdot_asyncio import Microdot, redirect, Response
from microdot_asyncio_websocket import with_websocket
from microdot_utemplate import init_templates, render_template
from machine import Pin

enA = Pin(7, Pin.OUT)#D5
in1 = Pin(6, Pin.OUT)#D4
in2 = Pin(5, Pin.OUT)#D3

DOMAIN = "CRANE.local"

app = Microdot()
Response.default_content_type = 'text/html'


def crane_stop():
  print("Crane stop.")
  enA.off()# analogWrite(enA, 0)
  in1.off()#digitalWrite(in1, LOW);
  in2.off()#digitalWrite(in2, LOW);


def crane_left():
  print("Crane left.")
  in1.on()#digitalWrite(in1, HIGH);
  in2.off()#digitalWrite(in2, LOW);
  enA.on()#analogWrite(enA, 255);


def crane_right():
  print("Crane right.")
  in1.off()#digitalWrite(in1, LOW);
  in2.on()#digitalWrite(in2, HIGH);
  enA.on()#analogWrite(enA, 255);


@app.route('/')
async def index(request):
    print('Got a connection from %s' % str(request))
    return render_template('index.html')

# windows call home
@app.get("/ncsi.txt")
async def hotspot(request):
    print("AP ncsi.txt request received")
    return redirect(f"http://{DOMAIN}/", 302)

# windows 11 captive portal workaround
@app.get("/connecttest.txt")
async def hotspot(request):
    print("AP connecttest.txt request received")
    return redirect(f"http://logout.net", 302)

# microsoft redirect
@app.get("/redirect")
async def hotspot(request):
    print("AP redirect request received")
    return redirect(f"http://{DOMAIN}/", 302)

# android redirect
@app.get("/generate_204")
async def hotspot(request):
    print("AP generate_204 request received")
    return redirect(f"http://{DOMAIN}/", 302)

# apple redirect
@app.get("/hotspot-detect.html")
async def hotspot(request):
    print("AP hotspot-detect.html request received")
    return redirect(f"http://{DOMAIN}/", 302)

@app.route('/control')
@with_websocket
async def echo(request, ws):
    while True:
        data = await ws.receive()
        print(f"Received from WS: {data}")
        if data == "0":
            crane_stop()
        elif data == "1":
            crane_left()
        elif data == "2":
            crane_right()
        else:
            print(f"Unknown command: {data}")
        await ws.send(data)

async def main():
    gc.collect()

    ssid = 'MicroPython-AP'
    password = '123456789'


    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)

    while ap.active() == False:
        pass

    dns_server = CaptiveDNSServer()
    # await app.start_server(port=80, debug=True)
    web_server_thread = asyncio.create_task(app.start_server(port=80, debug=True))
    dns_thread = asyncio.create_task(dns_server.run("192.168.4.1"))

    await dns_thread
    await web_server_thread

asyncio.run(main())
