import requests
import threading

def send_request(file_path, model):
    url = "http://35.224.215.210:8080/separar"
    files = {'file': open(file_path, 'rb')}
    data = {'model': model}
    
    response = requests.post(url, files=files, data=data)
    print(response.json())

file_path = "./teste.mp3"
model = "d6"

threads = []
for _ in range(1): 
    t = threading.Thread(target=send_request, args=(file_path, model))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
