import cv2
import os
import urllib.request
import time
from flask import Flask, Response
from picamera2 import Picamera2, MappedArray

# Essayer d'importer GPIO, sinon mode distant (controle via HTTP)
try:
    import RPi.GPIO as GPIO
    REMOTE_MODE = False
except ImportError:
    GPIO = None
    REMOTE_MODE = True
    import requests
    print("Mode distant active - les commandes seront envoyees au Pi via HTTP")

# Adresse du serveur de servos sur le Pi (a modifier selon votre config)
PI_SERVER_URL = "http://creativelab.local:5001"

# URL du modèle Haar cascade fourni par OpenCV (visages frontaux)
CASCADE_URL = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_alt2.xml'
# Nom de fichier local pour sauvegarder le cascade après téléchargement
CASCADE_FILENAME = 'haarcascade_frontalface_alt2.xml'

# Configuration des servos pour les oreilles (pins GPIO en mode BOARD)
SERVO_PIN_LEFT = 12   # Oreille gauche
SERVO_PIN_RIGHT = 33  # Oreille droite

# Positions des oreilles (angles en degres)
EARS_DOWN = 90      # Position repos - oreilles basses
EARS_UP = 30        # Position alerte - oreilles levees


def ensure_cascade(path=CASCADE_FILENAME):
    """
    Vérifie que le fichier de cascade existe localement.
    S'il est absent, le télécharge depuis CASCADE_URL et le place dans le dossier courant.

    Paramètres:
        path (str): chemin local du fichier cascade (par défaut CASCADE_FILENAME)
    """
    if not os.path.exists(path):
        print(f"Téléchargement du cascade depuis {CASCADE_URL} ...")
        try:
            # urllib.request.urlretrieve télécharge l'URL et écrit dans 'path'
            urllib.request.urlretrieve(CASCADE_URL, path)
            print(f"Cascade téléchargé: {path}")
        except Exception as e:
            # On affiche l'erreur puis on la propage pour être gérée en amont si besoin
            print("Échec du téléchargement du cascade:", e)
            raise

app = Flask(__name__)

# Variables globales pour la caméra et la détection
camera = None
face_cascade = None
scaleFactor_global = 1.1
minNeighbors_global = 5

# Variables globales pour les oreilles
pwm_left = None
pwm_right = None
ears_are_up = False
last_face_time = 0
last_wiggle_time = 0
EAR_TIMEOUT = 3.0  # Secondes avant de baisser les oreilles
WIGGLE_COOLDOWN = 5.0  # Secondes minimum entre deux wiggle


def angle_to_percent(angle):
    """Convertit un angle (0-180) en pourcentage PWM."""
    start = 4
    end = 12.5
    ratio = (end - start) / 180
    return start + (angle * ratio)


def init_ears():
    """Initialise les servos des oreilles."""
    global pwm_left, pwm_right
    if REMOTE_MODE:
        print(f"Mode distant - servos controles via {PI_SERVER_URL}")
        try:
            requests.get(f"{PI_SERVER_URL}/ears/down", timeout=2)
            print("Connexion au Pi OK - oreilles en position repos")
        except Exception as e:
            print(f"Attention: impossible de joindre le Pi ({e})")
        return
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(SERVO_PIN_LEFT, GPIO.OUT)
    GPIO.setup(SERVO_PIN_RIGHT, GPIO.OUT)
    pwm_left = GPIO.PWM(SERVO_PIN_LEFT, 50)
    pwm_right = GPIO.PWM(SERVO_PIN_RIGHT, 50)
    pwm_left.start(angle_to_percent(EARS_DOWN))
    pwm_right.start(angle_to_percent(EARS_DOWN))
    time.sleep(0.5)
    # Arreter le signal pour eviter les vibrations
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    print("Oreilles initialisees en position repos")


def ears_up():
    """Leve les oreilles - position alerte."""
    global ears_are_up
    print("Oreilles levees!")
    if REMOTE_MODE:
        try:
            requests.get(f"{PI_SERVER_URL}/ears/up", timeout=2)
        except Exception:
            pass
        ears_are_up = True
        return
    # Mouvement miroir pour un effet naturel
    pwm_left.ChangeDutyCycle(angle_to_percent(EARS_UP))
    pwm_right.ChangeDutyCycle(angle_to_percent(180 - EARS_UP))
    time.sleep(0.3)
    # Arreter le signal pour eviter les vibrations
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    ears_are_up = True


def ears_down():
    """Baisse les oreilles - position repos."""
    global ears_are_up
    print("Oreilles baissees")
    if REMOTE_MODE:
        try:
            requests.get(f"{PI_SERVER_URL}/ears/down", timeout=2)
        except Exception:
            pass
        ears_are_up = False
        return
    pwm_left.ChangeDutyCycle(angle_to_percent(EARS_DOWN))
    pwm_right.ChangeDutyCycle(angle_to_percent(EARS_DOWN))
    time.sleep(0.3)
    # Arreter le signal pour eviter les vibrations
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    ears_are_up = False


def wiggle_ears():
    """Fait bouger les oreilles de facon joyeuse."""
    global ears_are_up
    print("Wiggle des oreilles!")
    if REMOTE_MODE:
        try:
            requests.get(f"{PI_SERVER_URL}/ears/wiggle", timeout=2)
        except Exception:
            pass
        ears_are_up = True
        return
    for _ in range(2):
        pwm_left.ChangeDutyCycle(angle_to_percent(60))
        pwm_right.ChangeDutyCycle(angle_to_percent(120))
        time.sleep(0.15)
        pwm_left.ChangeDutyCycle(angle_to_percent(120))
        pwm_right.ChangeDutyCycle(angle_to_percent(60))
        time.sleep(0.15)
    # Arreter le signal apres le wiggle
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    ears_up()


def cleanup_ears():
    """Nettoie les ressources GPIO."""
    ears_down()
    if REMOTE_MODE:
        print("Mode distant - pas de GPIO a nettoyer")
        return
    time.sleep(0.3)
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    print("GPIO nettoye")

def generate_frames():
    """Génère les frames pour le streaming."""
    global camera, face_cascade, ears_are_up, last_face_time, last_wiggle_time
    previous_face_count = 0

    while True:
        start_time = time.time()
        
        ret, frame = camera.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=scaleFactor_global, minNeighbors=minNeighbors_global)
        current_face_count = len(faces)

        # Dessiner les rectangles autour des visages
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, 'Coucou', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Logique des oreilles
        if current_face_count > 0:
            last_face_time = time.time()
            if previous_face_count == 0:
                # Nouveau visage - wiggle seulement si cooldown expire
                if (time.time() - last_wiggle_time) > WIGGLE_COOLDOWN:
                    print('Nouveau visage détecté!')
                    wiggle_ears()
                    last_wiggle_time = time.time()
                elif not ears_are_up:
                    ears_up()
            elif not ears_are_up:
                ears_up()
        else:
            # Plus de visage - verifier timeout pour baisser les oreilles
            if ears_are_up and (time.time() - last_face_time) > EAR_TIMEOUT:
                ears_down()

        previous_face_count = current_face_count

        # Encoder en JPEG pour le streaming
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        elapsed = time.time() - start_time
        sleep_time = max(0, (1/20) - elapsed)
        time.sleep(sleep_time)

@app.route('/')
def index():
    return '<h1>Camera Pi</h1><img src="/video" width="640">'

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def detect_from_camera(scaleFactor=1.1, minNeighbors=5):
    """Lance le serveur de streaming avec détection de visages et oreilles reactives."""
    global camera, face_cascade, scaleFactor_global, minNeighbors_global

    scaleFactor_global = scaleFactor
    minNeighbors_global = minNeighbors

    ensure_cascade()
    face_cascade = cv2.CascadeClassifier(CASCADE_FILENAME)

    # Initialiser les oreilles (servos)
    init_ears()

    # Initialiser la caméra avec OpenCV (compatible legacy camera)
    camera = setup_cam()
    if(camera[0] == "Picamera2"):
        read_picamera(camera[1])
    else:
        camera = camera[1]

    print("Camera en cours de capture...")
    print("Serveur démarré sur http://0.0.0.0:5002")
    print("Les oreilles bougent quand un visage est détecté!")

    try:
        app.run(host='0.0.0.0', port=5002, threaded=True)
    finally:
        camera.release()
        cleanup_ears()

def setup_cam():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 20)
    

    if not camera.isOpened():
        cam = Picamera2()
        config = cam.create_preview_configuration(
            main={"size": (640, 480)},
            controls={"FrameRate": 20}
        )
        cam.configure(config)

        def preview(request):
            with MappedArray(request, "main") as m:
                pass

        cam.pre_callback = preview

        time.sleep(5)

        cam.start(show_preview=True)
        
        

        return ["Picamera2",cam]
    else:
        return ["Legacy",camera]

def read_picamera(cam):
    frame = cam.capture_array()
    height, width, _ = frame.shape
    middle = (int(width / 2), int(height / 2))

    while True:
            frame = cam.capture_array()
            cv2.circle(frame, middle, 10, (255, 0 , 255), -1)
            cv2.imshow('f', frame)
            print("ping")
            cv2.waitKey(1)
            print("ping")

if __name__ == '__main__':
    # Interface en ligne de commande simple
    import argparse
    parser = argparse.ArgumentParser(description='Détection de visages simple avec OpenCV')
    parser.add_argument('--image', '-i', help='Chemin vers une image à traiter')
    parser.add_argument('--output', '-o', help='Fichier de sortie (si --image)')
    parser.add_argument('--scale', type=float, default=1.1, help='scaleFactor pour detectMultiScale')
    parser.add_argument('--neighbors', type=int, default=5, help='minNeighbors pour detectMultiScale')
    args = parser.parse_args()
    
    detect_from_camera(args.scale, args.neighbors)
