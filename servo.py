#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time

# Fonction pour convertir angle en duty cycle
def angle_to_percent(angle):
    if angle > 180 or angle < 0:
        return False
    
    start = 4
    end = 12.5
    ratio = (end - start) / 180
    angle_as_percent = angle * ratio
    
    return start + angle_as_percent

# Configuration GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Configurer 2 pins PWM
pwm_gpio_1 = 12  # Pin physique 12 (GPIO 18)
pwm_gpio_2 = 33  # Pin physique 33 (GPIO 13)

frequence = 50

# Setup des deux pins
GPIO.setup(pwm_gpio_1, GPIO.OUT)
GPIO.setup(pwm_gpio_2, GPIO.OUT)

# Créer les objets PWM pour les 2 servos
pwm1 = GPIO.PWM(pwm_gpio_1, frequence)
pwm2 = GPIO.PWM(pwm_gpio_2, frequence)

print("🔧 Démarrage des 2 servos")

# Initialiser les 2 servos à 0°
pwm1.start(angle_to_percent(0))
pwm2.start(angle_to_percent(0))
time.sleep(1)

# Mouvement simultané à 90°
print("→ 90°")
pwm1.ChangeDutyCycle(angle_to_percent(90))
pwm2.ChangeDutyCycle(angle_to_percent(90))
time.sleep(1)

# Mouvement simultané à 180°
print("→ 180°")
pwm1.ChangeDutyCycle(angle_to_percent(180))
pwm2.ChangeDutyCycle(angle_to_percent(180))
time.sleep(1)

# Retour à 90°
print("→ 90°")
pwm1.ChangeDutyCycle(angle_to_percent(90))
pwm2.ChangeDutyCycle(angle_to_percent(90))
time.sleep(1)

# Nettoyage
pwm1.stop()
pwm2.stop()
GPIO.cleanup()

print("✅ Terminé")