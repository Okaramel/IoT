import cv2
import os
import urllib.request

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

def detect_from_camera(scaleFactor=1.1, minNeighbors=5):
    """
    Lance la détection en temps réel depuis la webcam.

    Paramètres:
        scaleFactor (float): paramètre pour detectMultiScale
        minNeighbors (int): paramètre pour detectMultiScale
    """
    ensure_cascade()
    face_cascade = cv2.CascadeClassifier(CASCADE_FILENAME)

    # Ouvrir la première caméra disponible (index 0).
    # Avec l'autre caméra, changer le 0 par 1.
    cap = cv2.VideoCapture(0)
    previous_face_count = 0
    if not cap.isOpened():
        raise RuntimeError("Impossible d'ouvrir la caméra (index 0). Vérifiez la connexion ou les permissions)")
    print("Appuyez sur 'q' pour quitter")
    while True:
        # Lire une frame
        ret, frame = cap.read()
        if not ret:
            break
        # Convertir la frame en gris pour la détection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=scaleFactor, minNeighbors=minNeighbors)
        current_face_count = len(faces)

        # Dessiner les rectangles autour des visages détectés et message
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, 'Coucou', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        if current_face_count > 0 and previous_face_count == 0:
            print('hi coucou - nouveau visage détecté!')
        previous_face_count = current_face_count

        # Afficher la frame annotée
        cv2.imshow('Camera - Press q to quit', frame)

        # Attendre 1ms et vérifier si l'utilisateur a appuyé sur 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libérer la caméra et fermer toutes les fenêtres OpenCV
    cap.release()
    cv2.destroyAllWindows()


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
