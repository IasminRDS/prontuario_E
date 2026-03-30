# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime


class Alerta(db.Model):
    __tablename__ = 'alerta'
    
    id = db.Column(db.Integer, primary_key=True)

    unidade_id = db.Column(
        db.Integer,
        db.ForeignKey('unidades.id'),  # ✅ corrigido
        nullable=False
    )

    tipo = db.Column(db.String(50), nullable=False)
    nivel = db.Column(db.Integer, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)
    lido = db.Column(db.Boolean, default=False)
    dados_json = db.Column(db.JSON)

    unidade = db.relationship('Unidade', backref='alertas')

    def to_dict(self):
        return {
            'id': self.id,
            'unidade_id': self.unidade_id,
            'tipo': self.tipo,
            'nivel': self.nivel,
            'titulo': self.titulo,
            'mensagem': self.mensagem,
            'timestamp': self.timestamp.isoformat(),
            'lido': self.lido,
        }


class ConfiguradorAlerta(db.Model):
    __tablename__ = 'configurador_alerta'
    
    id = db.Column(db.Integer, primary_key=True)

    unidade_id = db.Column(
        db.Integer,
        db.ForeignKey('unidades.id'),  # ✅ corrigido
        nullable=False
    )

    tipo = db.Column(db.String(50), nullable=False)
    limiar_minimo = db.Column(db.Float)
    limiar_maximo = db.Column(db.Float)

    ativo = db.Column(db.Boolean, default=True)
    notificar_email = db.Column(db.Boolean, default=True)

    unidade = db.relationship('Unidade', backref='config_alertas')