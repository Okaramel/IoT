"""
Serveur de controle des servos pour le Raspberry Pi.
A executer sur le Pi. Ecoute les commandes HTTP pour bouger les oreilles.
"""
from flask import Flask, jsonify
import RPi.GPIO as GPIO
import time

app = Flask(__name__)

# Configuration des servos
SERVO_PIN_LEFT = 12
SERVO_PIN_RIGHT = 33
EARS_DOWN = 90
EARS_UP = 30

pwm_left = None
pwm_right = None
ears_are_up = False


def angle_to_percent(angle):
    """Convertit un angle (0-180) en pourcentage PWM pour MG996R."""
    # MG996R: 2.5% = 0°, 7.5% = 90°, 12.5% = 180°
    start = 2.5
    end = 12.5
    ratio = (end - start) / 180
    return start + (angle * ratio)


def init_servos():
    """Initialise les servos."""
    global pwm_left, pwm_right
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(SERVO_PIN_LEFT, GPIO.OUT)
    GPIO.setup(SERVO_PIN_RIGHT, GPIO.OUT)
    pwm_left = GPIO.PWM(SERVO_PIN_LEFT, 50)
    pwm_right = GPIO.PWM(SERVO_PIN_RIGHT, 50)
    pwm_left.start(angle_to_percent(EARS_DOWN))
    pwm_right.start(angle_to_percent(EARS_DOWN))
    time.sleep(0.5)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    print("Servos initialises")


@app.route('/ears/up', methods=['GET', 'POST'])
def ears_up():
    """Leve les oreilles."""
    global ears_are_up
    print("Commande: oreilles levees")
    pwm_left.ChangeDutyCycle(angle_to_percent(EARS_UP))
    pwm_right.ChangeDutyCycle(angle_to_percent(180 - EARS_UP))
    time.sleep(0.3)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    ears_are_up = True
    return jsonify({"status": "ok", "ears": "up"})


@app.route('/ears/down', methods=['GET', 'POST'])
def ears_down():
    """Baisse les oreilles."""
    global ears_are_up
    print("Commande: oreilles baissees")
    pwm_left.ChangeDutyCycle(angle_to_percent(EARS_DOWN))
    pwm_right.ChangeDutyCycle(angle_to_percent(EARS_DOWN))
    time.sleep(0.3)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    ears_are_up = False
    return jsonify({"status": "ok", "ears": "down"})


@app.route('/ears/wiggle', methods=['GET', 'POST'])
def wiggle_ears():
    """Wiggle des oreilles - petits mouvements pour MG996R."""
    global ears_are_up
    print("Commande: wiggle!")
    # Petits mouvements autour de 90° (+/- 5°)
    for _ in range(3):
        pwm_left.ChangeDutyCycle(angle_to_percent(85))
        pwm_right.ChangeDutyCycle(angle_to_percent(95))
        time.sleep(0.15)
        pwm_left.ChangeDutyCycle(angle_to_percent(95))
        pwm_right.ChangeDutyCycle(angle_to_percent(85))
        time.sleep(0.15)
    # Retour position repos (90°)
    pwm_left.ChangeDutyCycle(angle_to_percent(90))
    pwm_right.ChangeDutyCycle(angle_to_percent(90))
    time.sleep(0.3)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    ears_are_up = False
    return jsonify({"status": "ok", "action": "wiggle"})


@app.route('/status', methods=['GET'])
def status():
    """Retourne l'etat des oreilles."""
    return jsonify({"ears_up": ears_are_up})


if __name__ == '__main__':
    try:
        init_servos()
        print("Serveur de servos demarre sur http://0.0.0.0:5001")
        print("Endpoints: /ears/up, /ears/down, /ears/wiggle, /status")
        app.run(host='0.0.0.0', port=5001)
    finally:
        pwm_left.stop()
        pwm_right.stop()
        GPIO.cleanup()
