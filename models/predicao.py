# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime

class Predicao(db.Model):
    __tablename__ = 'predicao'
    
    id = db.Column(db.Integer, primary_key=True)

    unidade_id = db.Column(
        db.Integer,
        db.ForeignKey('unidades.id'),  # ✅ CORRIGIDO
        nullable=False
    )

    tipo = db.Column(db.String(50), nullable=False)
    data_predicao = db.Column(db.Date, nullable=False)
    valor_predito = db.Column(db.Float, nullable=False)
    valor_real = db.Column(db.Float)
    acuidade = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    unidade = db.relationship('Unidade', backref='predicoes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'unidade_id': self.unidade_id,
            'tipo': self.tipo,
            'data_predicao': str(self.data_predicao),
            'valor_predito': self.valor_predito,
            'valor_real': self.valor_real,
            'acuidade': self.acuidade,
        }