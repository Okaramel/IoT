Projet Robot pour Atmos Arena

============================================================
BRANCHEMENT DES SERVOS MG996R (Oreilles)
============================================================

Oreille gauche (Pin 12) :
| Fil servo      | Pin RPi      |
|----------------|--------------|
| Marron/Noir    | Pin 6 (GND)  |
| Rouge          | Pin 2 (5V)   |
| Orange/Jaune   | Pin 12       |

Oreille droite (Pin 33) :
| Fil servo      | Pin RPi      |
|----------------|--------------|
| Marron/Noir    | Pin 14 (GND) |
| Rouge          | Pin 4 (5V)   |
| Orange/Jaune   | Pin 33       |

Pinout Raspberry Pi : https://pinout.xyz/

============================================================
CONNEXION SSH
============================================================

ssh creativelab@creativelab.local

============================================================
TRANSFERER LES FICHIERS
============================================================

Depuis votre ordinateur (pas en SSH) :

scp face_detect.py creativelab@creativelab.local:~/
scp servo_server.py creativelab@creativelab.local:~/

============================================================
MODE 1 : TOUT SUR LE PI (camera Pi)
============================================================

1. Se connecter en SSH

2. Lancer le script :
   python3 face_detect.py

3. Ouvrir un navigateur :
   http://creativelab.local:5002

4. Pour arreter : Ctrl+C

============================================================
MODE 2 : CAMERA ORDI + SERVOS PI (mode distant)
============================================================

Terminal 1 (Mac) - Transferer les fichiers :
   scp /chemin/vers/servo_server.py creativelab@creativelab.local:~/

Terminal 2 (SSH vers Pi) - Lancer le serveur de servos :
   ssh creativelab@creativelab.local
   python3 servo_server.py

Terminal 3 (Mac) - Lancer la detection :
   python3 face_detect.py

Navigateur :
   http://localhost:5002

============================================================
COMPORTEMENT DES OREILLES
============================================================

| Evenement                  | Reaction                          |
|----------------------------|-----------------------------------|
| Nouveau visage detecte     | Wiggle joyeux (cooldown 5s)       |
| Visage toujours visible    | Oreilles restent levees           |
| Visage disparu depuis 3s   | Oreilles redescendent             |

============================================================
CONFIGURATION
============================================================

face_detect.py :
  PI_SERVER_URL = "http://creativelab.local:5001"  (adresse du Pi)
  EARS_DOWN = 90      (position repos)
  EARS_UP = 30        (position alerte)
  EAR_TIMEOUT = 3.0   (secondes avant de baisser)
  WIGGLE_COOLDOWN = 5.0  (secondes entre wiggle)

servo_server.py :
  SERVO_PIN_LEFT = 12
  SERVO_PIN_RIGHT = 33
  Port serveur : 5001

============================================================
DEPANNAGE
============================================================

SSH refused :
  - Verifier que Pi et ordi sont sur le meme WiFi
  - Attendre 2-3 min apres demarrage de la Pi

Servo ne bouge pas :
  - Verifier branchement des pins
  - Verifier que servo_server.py tourne sur le Pi

Servo fait des 360 :
  - Les MG996R ne doivent pas faire de tour complet
  - Verifier les valeurs PWM dans servo_server.py

Camera Mac non autorisee :
  - Reglages Systeme > Confidentialite > Camera > Activer Terminal

Port 5000 occupe (Mac) :
  - AirPlay utilise ce port, le script utilise 5002

Page web ne charge pas :
  - Verifier que le script tourne sans erreur dans le terminal

============================================================
FICHIERS
============================================================

face_detect.py      - Detection de visages + streaming video
servo_server.py     - Serveur HTTP pour controler les servos (Pi)
petitrobot.service  - Systemd service à déplacer dans le dossier /etc/systemd/system/ et activer avec "sudo systemctl enable petitrobot"

============================================================
IMPLEMENTATION ACTUELLE
============================================================

- Detection de visage avec Haar Cascade (haarcascade_frontalface_alt2)
- Streaming video via Flask (port 5002)
- Oreilles reactives (2 servos MG996R) avec wiggle
- Mode distant : camera ordi + servos Pi
- Cooldown de 5 secondes entre les wiggle
