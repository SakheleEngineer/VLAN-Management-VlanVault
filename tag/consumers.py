"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class VlanConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = "vlan_updates"

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Receive message from frontend (optional)
    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")

        # echo back (optional)
        self.send(text_data=json.dumps({
            "message": message
        }))

    # ✅ Receive message from Django (signals / views)
    def vlan_message(self, event):
        self.send(text_data=json.dumps(event["data"]))