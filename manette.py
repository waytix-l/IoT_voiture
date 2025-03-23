from machine import Pin
import espnow
import network

# Désactiver le Wi-Fi (pas besoin d'internet)
sta = network.WLAN(network.STA_IF)
sta.active(True)

# Initialiser ESP-NOW
esp = espnow.ESPNow()
esp.active(True)

# Adresse MAC de la voiture (remplace avec l'adresse réelle)
car_mac = b'\xCC\xDB\xA7\x30\xD7\x08'  # Exemple
esp.add_peer(car_mac)

# Boutons sur GPIO
forward = Pin(33, Pin.IN, Pin.PULL_UP)
backward = Pin(25, Pin.IN, Pin.PULL_UP)
left = Pin(26, Pin.IN, Pin.PULL_UP)
right = Pin(27, Pin.IN, Pin.PULL_UP)

while True:
    try:
        if forward.value() == 0 and right.value() == 0:
            print("fr")
            esp.send(car_mac, "FR")
        elif forward.value() == 0 and left.value() == 0:
            print("fl")
            esp.send(car_mac, "FL")
        elif forward.value() == 0:
            print("f")
            esp.send(car_mac, "F")
        elif backward.value() == 0:
            print("b")
            esp.send(car_mac, "B")
        elif left.value() == 0:
            print("l")
            esp.send(car_mac, "L")
        elif right.value() == 0:
            print("r")
            esp.send(car_mac, "R")
        else:
            esp.send(car_mac, "S")  # Stop par défaut
    except keyboardInterrupt:
        break