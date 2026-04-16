# Projet Robot - Atmos Arena

## Branchement des servos MG996R (Oreilles)

**Oreille gauche (Pin 32 = GPIO12) :**

| Fil servo    | Pin RPi      |
|--------------|--------------|
| Marron/Noir  | Pin 6 (GND)  |
| Rouge        | Pin 2 (5V)   |
| Orange/Jaune | Pin 32       |

**Oreille droite (Pin 33 = GPIO13) :**

| Fil servo    | Pin RPi      |
|--------------|--------------|
| Marron/Noir  | Pin 14 (GND) |
| Rouge        | Pin 4 (5V)   |
| Orange/Jaune | Pin 33       |

Pinout Raspberry Pi : https://pinout.xyz/

---

## Connexion SSH

```bash
ssh creativelab@creativelab.local
```

---

## Transferer les fichiers

Depuis votre ordinateur (pas en SSH) :

```bash
scp face_detect.py creativelab@creativelab.local:~/
```

---

## Mode 1 : Tout sur le Pi (camera Pi)

1. Se connecter en SSH
2. Lancer le script :
   ```bash
   python3 face_detect.py
   ```
3. Ouvrir un navigateur : `http://creativelab.local:5002`
4. Pour arreter : `Ctrl+C`

---

## Comportement des oreilles

| Evenement                | Reaction                    |
|--------------------------|-----------------------------|
| Nouveau visage detecte   | Wiggle joyeux (cooldown 5s) |
| Visage toujours visible  | Oreilles restent levees     |
| Visage disparu depuis 3s | Oreilles redescendent       |

---

## Configuration

`face_detect.py` :
```python
SERVO_PIN_LEFT  = 32       # Pin 32 = GPIO12
SERVO_PIN_RIGHT = 33       # Pin 33 = GPIO13
EARS_DOWN       = 90       # Position repos
EARS_UP         = 30       # Position alerte
EAR_TIMEOUT     = 3.0      # Secondes avant de baisser
WIGGLE_COOLDOWN = 5.0      # Secondes entre wiggle
```

---

## Depannage

**SSH refuse :**
- Verifier que Pi et ordi sont sur le meme WiFi
- Attendre 2-3 min apres demarrage du Pi

**Servo ne bouge pas :**
- Verifier le branchement des pins 32 et 33
- Tester le pin avec une LED + résistance 330Ω

**Servo fait des 360 :**
- Les MG996R ne doivent pas faire de tour complet
- Verifier les valeurs PWM (plage correcte : 5% a 10%)

**Page web ne charge pas :**
- Verifier que le script tourne sans erreur dans le terminal

**Port 5000 occupe (Mac) :**
- AirPlay utilise ce port, le script utilise 5002

---

## Fichiers

| Fichier             | Description                                      |
|---------------------|--------------------------------------------------|
| `face_detect.py`    | Detection de visages + streaming video + servos  |
| `petitrobot.service`| Service systemd pour lancement automatique au boot |

Pour activer le lancement automatique :
```bash
sudo cp petitrobot.service /etc/systemd/system/
sudo systemctl enable petitrobot
```

---

## Implementation actuelle

- Detection de visage avec Haar Cascade (`haarcascade_frontalface_alt2`)
- Streaming video via Flask (port 5002)
- Oreilles reactives (2 servos MG996R) avec wiggle
- Cooldown de 5 secondes entre les wiggle
