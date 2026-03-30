# -*- coding: utf-8 -*-
"""
Model de Notificações - Push Notifications
Prontuário Único - SUS
"""

from database.db import db
from datetime import datetime


class SubscricaoPush(db.Model):
    """Subscrição para Push Notifications"""
    __tablename__ = 'subscricoes_push'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Token de push (Web Push)
    endpoint = db.Column(db.Text, nullable=False)
    auth_secret = db.Column(db.String(255), nullable=False)
    p256dh = db.Column(db.String(255), nullable=False)
    
    # Informações do navegador/dispositivo
    user_agent = db.Column(db.String(500), nullable=True)
    browser = db.Column(db.String(100), nullable=True)  # Chrome, Firefox, Safari
    sistema_operacional = db.Column(db.String(100), nullable=True)  # Windows, Linux, iOS, Android
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Datas
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_uso = db.Column(db.DateTime, nullable=True)
    
    # Relacionamento
    usuario = db.relationship('User', backref='subscricoes_push')

    def __repr__(self):
        return f'<SubscricaoPush user_id={self.usuario_id}>'