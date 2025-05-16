import pyaudio
pa = pyaudio.PyAudio()
for i in range(pa.get_device_count()):
    print(f"{i}: {pa.get_device_info_by_index(i)}")


import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone(device_index=0) as source:
    print("Listening with Logi USB Headset...")
    r.adjust_for_ambient_noise(source)
    audio = r.listen(source, timeout=5)

print("Recognizing...")
print(r.recognize_google(audio))
