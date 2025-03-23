import _thread
import time
from machine import Pin, PWM, time_pulse_us
import network
import espnow

# Activer Wi-Fi en mode station
sta = network.WLAN(network.STA_IF)
sta.active(True)

# Initialiser ESP-NOW
esp = espnow.ESPNow()
esp.active(True)

# Définition des broches ESP32 pour le contrôle du driver moteur
MOTOR_LEFT_FORWARD = PWM(Pin(25), freq=1000)
MOTOR_LEFT_BACKWARD = PWM(Pin(26), freq=1000)
MOTOR_RIGHT_FORWARD = PWM(Pin(32), freq=1000)
MOTOR_RIGHT_BACKWARD = PWM(Pin(33), freq=1000)

# Configuration du capteur HC-SR04
TRIGGER_PIN = Pin(27, Pin.OUT)
ECHO_PIN = Pin(13, Pin.IN)

# Constantes
DISTANCE_OBSTACLE = 15  # Distance en cm pour détecter un obstacle
CHECK_INTERVAL = 0.05   # Vérification toutes les 50ms

# Variables globales pour le multithreading
obstacle_detected = False
running = True  # Permet de stopper proprement le thread

# Fonction pour mesurer la distance avec le capteur HC-SR04
def mesurer_distance():
    TRIGGER_PIN.value(0)
    time.sleep_us(2)
    TRIGGER_PIN.value(1)
    time.sleep_us(10)
    TRIGGER_PIN.value(0)
    
    try:
        duree = time_pulse_us(ECHO_PIN, 1, 30000)  # Timeout de 30ms
        if duree < 0:
            return float('inf')  # Valeur infinie si timeout
        
        distance = (duree / 2) / 29.1
        return distance
    except:
        return float('inf')

# Thread de surveillance des obstacles
def surveiller_obstacles():
    global obstacle_detected, running
    while running:
        distance = mesurer_distance()
        if distance < DISTANCE_OBSTACLE:
            if not obstacle_detected:
                print("🚨 Obstacle détecté ! Arrêt du véhicule.")
            obstacle_detected = True
        else:
            if obstacle_detected:
                print("✅ Obstacle retiré. Reprise du mouvement.")
            obstacle_detected = False
        time.sleep(CHECK_INTERVAL)

# Fonctions de contrôle des moteurs
def avancer(vitesse=65535):
    MOTOR_LEFT_FORWARD.duty_u16(vitesse)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(vitesse)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def reculer(vitesse=65535):
    MOTOR_LEFT_FORWARD.duty_u16(0)
    MOTOR_LEFT_BACKWARD.duty_u16(vitesse)
    MOTOR_RIGHT_FORWARD.duty_u16(0)
    MOTOR_RIGHT_BACKWARD.duty_u16(vitesse)

def tourner_gauche(vitesse=65535):
    MOTOR_LEFT_FORWARD.duty_u16(vitesse)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(0)
    MOTOR_RIGHT_BACKWARD.duty_u16(vitesse)

def tourner_droite(vitesse=65535):
    MOTOR_LEFT_FORWARD.duty_u16(0)
    MOTOR_LEFT_BACKWARD.duty_u16(vitesse)
    MOTOR_RIGHT_FORWARD.duty_u16(vitesse)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def avancer_gauche(vitesse=65535, tournant=32768, tournant_fort=0):
    MOTOR_LEFT_FORWARD.duty_u16(vitesse)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(tournant)
    MOTOR_RIGHT_BACKWARD.duty_u16(tournant_fort)

def avancer_droite(vitesse=65535, tournant=32768, tournant_fort=0):
    MOTOR_LEFT_FORWARD.duty_u16(tournant)
    MOTOR_LEFT_BACKWARD.duty_u16(tournant_fort)
    MOTOR_RIGHT_FORWARD.duty_u16(vitesse)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def stop():
    MOTOR_LEFT_FORWARD.duty_u16(0)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(0)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

# Fonction principale de la course avec vérification en thread
def course():
    global obstacle_detected
    mouvements = [
        (avancer, [65535], 0.9),
        (avancer_droite, [65535], 0.55),
        (tourner_droite, [65535], 0.28),
        (avancer, [65535], 0.95),
        (avancer_droite, [65535, 14336], 0.45),
        (avancer, [65535], 0.15),
        (avancer_gauche, [65535, 14336], 0.45),
        (avancer, [65535], 0.4),
        (avancer_droite, [59392, 13312], 1.25),
        (avancer, [65535], 0.4),
        (avancer_gauche, [59392, 13312], 1.28),
        (avancer, [65535], 0.42),
        (avancer_droite, [59392, 13312], 1.25),
        (avancer, [65535], 0.5),
        (avancer_droite, [65535, 16384], 0.28),
        (avancer, [65535], 1.0)
    ]
    
    for mouvement, args, duree in mouvements:
        mouvement(*args)
        temps_debut = time.time()
        
        while time.time() - temps_debut < duree:
            if obstacle_detected:
                stop()
                print("⏸️ Pause... Attente que l'obstacle disparaisse.")
                while obstacle_detected:
                    time.sleep(0.1)  # Réduit la consommation CPU
                print("▶️ Reprise du mouvement.")
                mouvement(*args)  # Reprendre le mouvement
                temps_debut = time.time()  # Recalcule le temps restant
        
        stop()  # Assure un arrêt après chaque mouvement
    
    print("🏁 Course terminée !")

# Fonction principale
def main():
    global running
    try:
        print("🟢 Démarrage de la voiture ESP32")

        # Vérifier qu'aucun obstacle n'est détecté au départ
        distance = mesurer_distance()
        if distance < DISTANCE_OBSTACLE:
            print("🔴 Obstacle détecté avant le départ ! Attente...")
            while distance < DISTANCE_OBSTACLE:
                distance = mesurer_distance()
                time.sleep(0.05)
            print("🟢 Départ !")

        # Lancer le thread **seulement si nécessaire**
        _thread.start_new_thread(surveiller_obstacles, ())

        # Exécuter la course
        course()
        
    except KeyboardInterrupt:
        print("⛔ Programme interrompu.")
    finally:
        running = False  # Arrête proprement le thread
        stop()

# Lancer le programme
main()
print("🚗 Programme terminé.")