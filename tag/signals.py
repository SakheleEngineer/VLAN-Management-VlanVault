from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import VlanActivity

@receiver(post_save, sender=VlanActivity)
def broadcast_vlan_log(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    print(channel_layer)

    async_to_sync(channel_layer.group_send)(
        "vlan_logs",
        {
            "type": "send_vlan_log",
            "data": {
                "vlan_id": "instance.vlan_id",
                "message": "instance.message",
                "level": "instance.level",
                "timestamp": "instance.timestamp.isoformat()",
            }
        }
    )
