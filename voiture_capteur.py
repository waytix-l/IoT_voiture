import _thread
import time
from machine import Pin, PWM, time_pulse_us
import network
import espnow

# Initialisation du WiFi en mode station
sta = network.WLAN(network.STA_IF)
sta.active(True)

# Initialisation d'ESP-NOW
esp = espnow.ESPNow()
esp.active(True)

# Configuration des broches pour les moteurs
MOTOR_LEFT_FORWARD = PWM(Pin(25), freq=1000)
MOTOR_LEFT_BACKWARD = PWM(Pin(26), freq=1000)
MOTOR_RIGHT_FORWARD = PWM(Pin(32), freq=1000)
MOTOR_RIGHT_BACKWARD = PWM(Pin(33), freq=1000)

# Configuration du capteur ultrasonique HC-SR04
TRIGGER_PIN = Pin(27, Pin.OUT)
ECHO_PIN = Pin(13, Pin.IN)

# Constantes pour la détection d'obstacles
DISTANCE_OBSTACLE = 15  # Distance en cm
CHECK_INTERVAL = 0.05   # Intervalle de vérification en secondes

# Variables globales pour le multithreading
obstacle_detected = False
running = True

def mesurer_distance():
    """
    Mesure la distance avec le capteur HC-SR04.
    
    Returns:
        float: Distance en centimètres. Retourne une valeur infinie en cas d'erreur ou de timeout.
    """
    TRIGGER_PIN.value(0)
    time.sleep_us(2)
    TRIGGER_PIN.value(1)
    time.sleep_us(10)
    TRIGGER_PIN.value(0)
    
    try:
        duree = time_pulse_us(ECHO_PIN, 1, 30000)  # Timeout de 30ms
        if duree < 0:
            return float('inf')
        
        # Conversion du temps en distance (cm)
        distance = (duree / 2) / 29.1
        return distance
    except:
        return float('inf')

def surveiller_obstacles():
    """
    Thread de surveillance en continu des obstacles.
    Met à jour la variable globale obstacle_detected selon la distance détectée.
    S'exécute jusqu'à ce que la variable running soit mise à False.
    """
    global obstacle_detected, running
    while running:
        distance = mesurer_distance()
        if distance < DISTANCE_OBSTACLE:
            if not obstacle_detected:
                print("Obstacle détecté ! Arrêt du véhicule.")
            obstacle_detected = True
        else:
            if obstacle_detected:
                print("Obstacle retiré. Reprise du mouvement.")
            obstacle_detected = False
        time.sleep(CHECK_INTERVAL)

def avancer(vitesse=65535):
    """
    Fait avancer le véhicule en ligne droite.
    
    Args:
        vitesse (int): Valeur PWM pour la vitesse des moteurs (0-65535).
    """
    MOTOR_LEFT_FORWARD.duty_u16(vitesse)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(vitesse)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def reculer(vitesse=65535):
    """
    Fait reculer le véhicule en ligne droite.
    
    Args:
        vitesse (int): Valeur PWM pour la vitesse des moteurs (0-65535).
    """
    MOTOR_LEFT_FORWARD.duty_u16(0)
    MOTOR_LEFT_BACKWARD.duty_u16(vitesse)
    MOTOR_RIGHT_FORWARD.duty_u16(0)
    MOTOR_RIGHT_BACKWARD.duty_u16(vitesse)

def tourner_gauche(vitesse=65535):
    """
    Fait tourner le véhicule vers la gauche sur place.
    
    Args:
        vitesse (int): Valeur PWM pour la vitesse des moteurs (0-65535).
    """
    MOTOR_LEFT_FORWARD.duty_u16(vitesse)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(0)
    MOTOR_RIGHT_BACKWARD.duty_u16(vitesse)

def tourner_droite(vitesse=65535):
    """
    Fait tourner le véhicule vers la droite sur place.
    
    Args:
        vitesse (int): Valeur PWM pour la vitesse des moteurs (0-65535).
    """
    MOTOR_LEFT_FORWARD.duty_u16(0)
    MOTOR_LEFT_BACKWARD.duty_u16(vitesse)
    MOTOR_RIGHT_FORWARD.duty_u16(vitesse)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def avancer_gauche(vitesse=65535, tournant=32768, tournant_fort=0):
    """
    Fait avancer le véhicule en tournant vers la gauche.
    
    Args:
        vitesse (int): Valeur PWM pour la vitesse du moteur principal (0-65535).
        tournant (int): Valeur PWM réduite pour le moteur secondaire (0-65535).
        tournant_fort (int): Valeur PWM pour accentuer le virage si nécessaire (0-65535).
    """
    MOTOR_LEFT_FORWARD.duty_u16(vitesse)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(tournant)
    MOTOR_RIGHT_BACKWARD.duty_u16(tournant_fort)

def avancer_droite(vitesse=65535, tournant=32768, tournant_fort=0):
    """
    Fait avancer le véhicule en tournant vers la droite.
    
    Args:
        vitesse (int): Valeur PWM pour la vitesse du moteur principal (0-65535).
        tournant (int): Valeur PWM réduite pour le moteur secondaire (0-65535).
        tournant_fort (int): Valeur PWM pour accentuer le virage si nécessaire (0-65535).
    """
    MOTOR_LEFT_FORWARD.duty_u16(tournant)
    MOTOR_LEFT_BACKWARD.duty_u16(tournant_fort)
    MOTOR_RIGHT_FORWARD.duty_u16(vitesse)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def stop():
    """
    Arrête tous les moteurs du véhicule.
    """
    MOTOR_LEFT_FORWARD.duty_u16(0)
    MOTOR_LEFT_BACKWARD.duty_u16(0)
    MOTOR_RIGHT_FORWARD.duty_u16(0)
    MOTOR_RIGHT_BACKWARD.duty_u16(0)

def course():
    """
    Exécute une séquence prédéfinie de mouvements formant un parcours.
    S'interrompt et reprend en cas de détection d'obstacle.
    """
    global obstacle_detected
    # Séquence de mouvements: (fonction, [arguments], durée en secondes)
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
        
        # Surveille les obstacles pendant l'exécution de chaque mouvement
        while time.time() - temps_debut < duree:
            if obstacle_detected:
                stop()
                print("Pause... Attente que l'obstacle disparaisse.")
                while obstacle_detected:
                    time.sleep(0.1)  # Réduit la consommation CPU pendant l'attente
                print("Reprise du mouvement.")
                mouvement(*args)  # Reprend le mouvement interrompu
                temps_debut = time.time()  # Réinitialise le chronomètre
        
        stop()  # Arrêt après chaque mouvement
    
    print("Course terminée !")

def main():
    """
    Fonction principale du programme.
    Initialise le système, vérifie l'absence d'obstacles,
    lance le thread de surveillance et exécute la course.
    """
    global running
    try:
        print("Démarrage de la voiture ESP32")

        # Vérification d'obstacle avant le départ
        distance = mesurer_distance()
        if distance < DISTANCE_OBSTACLE:
            print("Obstacle détecté avant le départ ! Attente...")
            while distance < DISTANCE_OBSTACLE:
                distance = mesurer_distance()
                time.sleep(0.05)
            print("Départ !")

        # Démarrage du thread de surveillance des obstacles
        _thread.start_new_thread(surveiller_obstacles, ())

        # Exécution du parcours
        course()
        
    except KeyboardInterrupt:
        print("Programme interrompu.")
    finally:
        running = False  # Arrête proprement le thread
        stop()  # Arrête les moteurs

# Point d'entrée du programme
main()
print("Programme terminé.")