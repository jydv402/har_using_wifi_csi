from fastapi import FastAPI
from pydantic import BaseModel
from firebase_admin import credentials, messaging
import firebase_admin

import os
import json
import sys
import time

# ---------------- FASTAPI ----------------

app = FastAPI()

# ---------------- FIREBASE ----------------


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# ---------------- TOKENS ----------------

with open("tokens.txt") as f:
    DEVICE_TOKENS = [line.strip() for line in f if line.strip()]

# ---------------- STATE ----------------

current_state = "normal"
fall_locked = False   # VERY IMPORTANT


# ---------------- FCM ----------------

def send_push_notification():
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="⚠ Fall Detected",
            body="Possible fall detected"
        ),
        tokens=DEVICE_TOKENS,
    )

    messaging.send_each_for_multicast(message)
    print("NOTIFICATION SENT")


class StatusUpdate(BaseModel):
    status: str

# ---------------- API ----------------

@app.post("/predictions")
def update_status(update: StatusUpdate):
    global current_state, fall_locked

    if fall_locked:
        return {"status": "ignored_fall_locked"}

    if update.status == "fall":
        current_state = "fall"
        fall_locked = True
        print("MODEL → FALL detected (LOCKED)")
        send_push_notification()
    elif update.status == "normal":
        current_state = "normal"
        # Optional to print, but doing it on carriage return
        # sys.stdout.write(f"\rMODEL → NORMAL")
        # sys.stdout.flush()

    return {"status": "updated"}


# ---------------- API ----------------

@app.get("/status")
def get_status():
    return {"status": current_state}


# MANUAL FALL TRIGGER 
@app.post("/trigger_fall")
def trigger_fall():
    global current_state, fall_locked

    if not fall_locked:
        current_state = "fall"
        fall_locked = True
        print("MANUAL FALL TRIGGERED")
        send_push_notification()

    return {"status": "fall triggered"}


# USER ACKNOWLEDGE
@app.post("/acknowledge")
def acknowledge():
    global current_state, fall_locked

    current_state = "normal"
    fall_locked = False

    print("\nFALL RESET BY USER")

    return {"status": "reset"}
