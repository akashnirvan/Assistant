import tkinter as tk
import speech_recognition as sr
import webbrowser
import pyttsx3
import threading
#Ai Search
import requests

API_KEY = "AIzaSyAEey2pCZn7pnWMsI1lEZ0UivR39l_9dhs"
GEMINI_MODEL = "models/gemini-2.0-flash"
import re

def clean_gemini_text(text):
    # Remove *, **, lists like 1., -, etc.
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'^\s*[-•]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def ask_gemini(prompt):
    short_prompt = f"{prompt}. Keep the answer short and clear in 3-4 lines only."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyAEey2pCZn7pnWMsI1lEZ0UivR39l_9dhs"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": short_prompt}
                ]
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()
        response = res.json()
        return clean_gemini_text(response["candidates"][0]["content"]["parts"][0]["text"])
    except Exception as e:
        return f"Gemini error: {e}"

#Gemini Function to get response


# --- Setup GUI ---
root = tk.Tk()
root.title("Assistant Chat UI")
root.geometry("400x500")
root.configure(bg="#111")

frame = tk.Frame(root, bg="#111")
frame.pack(fill="both", expand=True)

canvas = tk.Canvas(frame, bg="#111", highlightthickness=0)
scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#111")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- Message Bubble Function ---
# 💬 Keep track of all message bubbles
message_bubbles = []
MAX_MESSAGES = 8  # max messages to keep visible

def add_message(message, is_user=False, disappear=False):
    bubble = tk.Label(
        scrollable_frame,
        text=message,
        bg="#00BFFF" if not is_user else "#444",
        fg="white",
        wraplength=300,
        justify="left" if not is_user else "right",
        anchor="w" if not is_user else "e",
        padx=10,
        pady=5,
        font=("Helvetica", 11),
        relief="ridge",
        bd=5
    )
    bubble.pack(anchor="w" if not is_user else "e", pady=4, padx=10)

    # Add to tracking list
    message_bubbles.append(bubble)

    # Remove old messages if too many
    if len(message_bubbles) > MAX_MESSAGES:
        old = message_bubbles.pop(0)
        old.destroy()

    if disappear:
        bubble.after(6000, lambda: (bubble.destroy(), message_bubbles.remove(bubble)))


# --- Voice Assistant Functions ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    add_message(text)
    engine.say(text)
    engine.runAndWait()

def listen(timeout=5, phrase_time_limit=None):
    try:
        with sr.Microphone() as source:
            add_message("🎤 Adjusting for noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            add_message("🎙️ Listening for speech...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return audio
    except sr.WaitTimeoutError:
        add_message("❌ No speech detected (timeout).")
        return None
    except Exception as e:
        add_message(f"⚠️ Microphone error: {e}")
        return None

def recognize(audio):
    if not audio:
        return None
    try:
        text = recognizer.recognize_google(audio)
        add_message(text, is_user=True)
        return text.lower()
    except sr.UnknownValueError:
        add_message("❌ Could not understand the audio.")
        return None
    except sr.RequestError as e:
        add_message(f"⚠️ Google API error: {e}")
        speak("Speech service is unavailable.")
        return None

def handle_command(command):
    if "open" in command:
        website = command.replace("open", "").strip()
        if "." not in website:
            url = f"https://www.google.com/search?q={website}"
        else:
            url = f"https://{website}"
        webbrowser.open(url)
        speak(f"Opening {website}")
    elif command.startswith("answer me"):
        query = command.replace("answer me", "").strip()
        if query:
            add_message(f"🤔 Asking Gemini: {query}")
            answer = ask_gemini(query)
            add_message(answer)
            speak(answer)
        else:
            speak("Please provide a question after 'answer me'.")



    elif "search" in command:
        query = command.replace("search", "").strip()
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        speak(f"Searching for {query}")

    elif "stop" in command:
        speak("Goodbye!")
        root.destroy()

    else:
        speak("I didn’t understand that command.")

# --- Assistant Loop (Runs in Thread) ---
def Assistant_loop():
    speak("Initializing Assistant")
    while True:
        add_message(f"🔍 Waiting for wake word: {waker}")
        wake_audio = listen(timeout=5, phrase_time_limit=5)
        s = recognize(wake_audio)
        wake_command=s.lower() if s else None

        if wake_command and {waker} in wake_command:
            speak("How can I help you?")
            
            # 🌀 Give user 1 or 2 chances to respond before resetting
            for attempt in range(2):
                command_audio = listen(timeout=5)
                user_command = recognize(command_audio)

                if user_command:
                    handle_command(user_command)
                    break  # break after successful command
                else:
                    speak("Sorry, I didn’t catch that.")
            continue  # Go back to wake word after responding

        elif wake_command and "stop" in wake_command:
            speak("Goodbye!")
            break
# --- Run Assistant in background thread ---
threading.Thread(target=Assistant_loop, daemon=True).start()

root.mainloop()
