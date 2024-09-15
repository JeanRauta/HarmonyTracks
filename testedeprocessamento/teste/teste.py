import requests
import threading

def send_request(audio_url, model):
    url = "http://localhost:5000/separar"
    data = {'url': audio_url, 'model': model}
    response = requests.post(url, data=data)
    print(response.json())

audio_url = "https://youtube.com/shorts/dBUMHplAzhA?si=ovhSzCwte5o4E5jB"
model = "d4"

threads = []
for _ in range(2): 
    t = threading.Thread(target=send_request, args=(audio_url, model))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
