from gradio_client import Client

client = Client("darkjwr/yt_dlp")

result = client.predict(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    api_name="/download"
)

print(result)
