import time

import requests
from PyQt6.QtWidgets import QMessageBox


def get_access_token(username, password):
    print(username, password)
    url = "https://bsky.social/xrpc/com.atproto.server.createSession"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "identifier": username,
        "password": password,
    }
    response = requests.post(url, json=data, headers=headers)
    print(response)
    if response.status_code == 200:
        return response.json().get('accessJwt')
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        QMessageBox.critical(None, "Error", "Account with username: " + username +"  Invalid username or password.")
        return None


def search_bluesky_users(query, access_token, limit=100, cursor=200):
    url = "https://bsky.social/xrpc/app.bsky.actor.searchActors"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        "term": query,
        "limit": limit,
        "cursor": cursor,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None
