import requests

headers = {"AccessToken": "8b2be529-0afc-43a2-b8c7-27dfebcfeb81"}
response = requests.get(
    "https://api-community-diamond-club.io/api/admin/events/", headers=headers
)
print(response.json())
