#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

def angle_to_percent(angle):
    start = 4
    end = 12.5
    ratio = (end - start) / 180
    return start + (angle * ratio)

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Configuration des 2 servos
GPIO.setup(12, GPIO.OUT)  # Servo 1
GPIO.setup(33, GPIO.OUT)  # Servo 2

pwm1 = GPIO.PWM(12, 50)
pwm2 = GPIO.PWM(33, 50)

print("Test 2 servos...")

try:
    # Démarrage à 90°
    pwm1.start(angle_to_percent(90))
    pwm2.start(angle_to_percent(90))
    time.sleep(1)
    
    # Mouvement symétrique
    print("Mouvement symétrique")
    pwm1.ChangeDutyCycle(angle_to_percent(0))
    pwm2.ChangeDutyCycle(angle_to_percent(0))
    time.sleep(1)
    
    pwm1.ChangeDutyCycle(angle_to_percent(180))
    pwm2.ChangeDutyCycle(angle_to_percent(180))
    time.sleep(1)
    
    # Mouvement miroir
    print("Mouvement miroir")
    for i in range(3):
        pwm1.ChangeDutyCycle(angle_to_percent(0))
        pwm2.ChangeDutyCycle(angle_to_percent(180))
        time.sleep(0.5)
        
        pwm1.ChangeDutyCycle(angle_to_percent(180))
        pwm2.ChangeDutyCycle(angle_to_percent(0))
        time.sleep(0.5)
    
    # Retour au centre
    pwm1.ChangeDutyCycle(angle_to_percent(90))
    pwm2.ChangeDutyCycle(angle_to_percent(90))
    time.sleep(1)
    
    print("✅ Terminé")

except KeyboardInterrupt:
    print("Interrompu")

finally:
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()