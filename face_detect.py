import cv2
import os
import urllib.request
from picamera2 import Picamera2
from flask import Flask, Response

# URL du modèle Haar cascade fourni par OpenCV (visages frontaux)
CASCADE_URL = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'
# Nom de fichier local pour sauvegarder le cascade après téléchargement
CASCADE_FILENAME = 'haarcascade_frontalface_default.xml'


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
picam2 = None
face_cascade = None
scaleFactor_global = 1.1
minNeighbors_global = 5

def generate_frames():
    """Génère les frames pour le streaming."""
    global picam2, face_cascade
    previous_face_count = 0

    while True:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=scaleFactor_global, minNeighbors=minNeighbors_global)
        current_face_count = len(faces)

        # Dessiner les rectangles autour des visages
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, 'Coucou', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        if current_face_count > 0 and previous_face_count == 0:
            print('Nouveau visage détecté!')
        previous_face_count = current_face_count

        # Encoder en JPEG pour le streaming
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', frame_bgr)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return '<h1>Camera Pi</h1><img src="/video" width="640">'

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def detect_from_camera(scaleFactor=1.1, minNeighbors=5):
    """Lance le serveur de streaming avec détection de visages."""
    global picam2, face_cascade, scaleFactor_global, minNeighbors_global

    scaleFactor_global = scaleFactor
    minNeighbors_global = minNeighbors

    ensure_cascade()
    face_cascade = cv2.CascadeClassifier(CASCADE_FILENAME)

    # Initialiser la caméra Raspberry Pi
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
    picam2.start()

    print("Serveur démarré sur http://0.0.0.0:5000")
    print("Ouvrez cette adresse dans votre navigateur (remplacez par l'IP de la Pi)")

    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        picam2.stop()


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
