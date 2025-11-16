"""
WebSocket Consumers pour les notifications en temps réel
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications en temps réel
    
    URL: ws://localhost:8000/ws/notifications/<user_id>/
    
    Flow:
    1. Client se connecte avec son user_id
    2. Consumer vérifie l'authentification
    3. Client est ajouté au groupe "notifications_<user_id>"
    4. Serveur peut envoyer des notifications à ce groupe
    """
    
    async def connect(self):
        """
        Connexion du client WebSocket
        """
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'notifications_{self.user_id}'
        
        # Vérifier l'authentification
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        # Vérifier que l'user_id correspond à l'utilisateur authentifié
        if str(user.id) != self.user_id:
            await self.close()
            return
        
        # Rejoindre le groupe de notifications
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer un message de confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté aux notifications en temps réel'
        }))
    
    async def disconnect(self, close_code):
        """
        Déconnexion du client WebSocket
        """
        # Quitter le groupe de notifications
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Recevoir un message du client (optionnel)
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Répondre au ping (keep-alive)
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except json.JSONDecodeError:
            pass
    
    async def notification_message(self, event):
        """
        Recevoir une notification depuis le channel layer et l'envoyer au client
        
        Args:
            event: Dict contenant les données de notification
        """
        # Envoyer la notification au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

