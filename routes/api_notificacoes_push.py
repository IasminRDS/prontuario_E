# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.user import User
from database.db import db
from datetime import datetime

api_notif_push_bp = Blueprint('api_notif_push', __name__, url_prefix='/api/notif-push')

class SubscricaoPush(db.Model):
    """Subscrição push para notificações"""
    __tablename__ = 'subscricao_push'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # ← CORRIJA: 'users'
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    auth = db.Column(db.String(255))
    p256dh = db.Column(db.String(255))
    
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    ultima_uso = db.Column(db.DateTime)
    
    usuario = db.relationship('User', backref='subscricoes_push')

@api_notif_push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Registra device para notificações push"""
    
    dados = request.get_json()
    
    # Verificar se já existe
    sub_existente = SubscricaoPush.query.filter_by(
        usuario_id=current_user.id,
        endpoint=dados['endpoint']
    ).first()
    
    if sub_existente:
        sub_existente.ativo = True
        sub_existente.ultima_uso = datetime.now()
    else:
        subscricao = SubscricaoPush(
            usuario_id=current_user.id,
            endpoint=dados['endpoint'],
            auth=dados.get('keys', {}).get('auth'),
            p256dh=dados.get('keys', {}).get('p256dh'),
        )
        db.session.add(subscricao)
    
    db.session.commit()
    
    return jsonify({'status': 'subscrito', 'usuario_id': current_user.id}), 201

@api_notif_push_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Remove device das notificações push"""
    
    dados = request.get_json()
    
    sub = SubscricaoPush.query.filter_by(
        usuario_id=current_user.id,
        endpoint=dados['endpoint']
    ).first()
    
    if sub:
        sub.ativo = False
        db.session.commit()
    
    return jsonify({'status': 'desscrito'})

def enviar_notificacao_push(usuario_id, titulo, corpo, dados=None):
    """Envia notificação push para usuário"""
    try:
        from pywebpush import webpush
        
        subscricoes = SubscricaoPush.query.filter_by(
            usuario_id=usuario_id,
            ativo=True
        ).all()
        
        payload = {
            'titulo': titulo,
            'corpo': corpo,
            'dados': dados or {},
            'timestamp': datetime.now().isoformat()
        }
        
        for sub in subscricoes:
            try:
                webpush(
                    subscription_info={
                        'endpoint': sub.endpoint,
                        'keys': {
                            'auth': sub.auth,
                            'p256dh': sub.p256dh,
                        }
                    },
                    data=str(payload),
                    vapid_private_key='sua_chave_privada_vapid',
                    vapid_claims={'sub': 'mailto:seu_email@exemplo.com'}
                )
                sub.ultima_uso = datetime.now()
            except Exception as e:
                print(f"Erro ao enviar push: {e}")
                sub.ativo = False
        
        db.session.commit()
        return True
    except ImportError:
        print("pywebpush não instalado. Install: pip install pywebpush")
        return False