import requests

url = "http://localhost:8000/auth/token"

data = {
    "username": "test_admin",
    "password": "12345678",
    "grant_type": "",
    "scope": "",
    "client_id": "",
    "client_secret": ""
}

response = requests.post(url, data=data)

print(response.status_code)
print(response.json())
