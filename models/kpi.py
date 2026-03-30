# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime

class KPI(db.Model):
    __tablename__ = 'kpi'

    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)

    atendimentos     = db.Column(db.Integer, default=0)
    internacoes      = db.Column(db.Integer, default=0)
    altas            = db.Column(db.Integer, default=0)
    obitos           = db.Column(db.Integer, default=0)
    cirurgias        = db.Column(db.Integer, default=0)
    taxa_ocupacao    = db.Column(db.Float,   default=0)
    taxa_mortalidade = db.Column(db.Float,   default=0)
    taxa_altas       = db.Column(db.Float,   default=0)
    ps_atendimentos  = db.Column(db.Integer, default=0)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    unidade = db.relationship('Unidade', backref='kpis')

    def to_dict(self):
        return {
            'id':               self.id,
            'unidade_id':       self.unidade_id,
            'data':             str(self.data),
            'atendimentos':     self.atendimentos,
            'internacoes':      self.internacoes,
            'altas':            self.altas,
            'obitos':           self.obitos,
            'cirurgias':        self.cirurgias,
            'taxa_ocupacao':    self.taxa_ocupacao,
            'taxa_mortalidade': self.taxa_mortalidade,
            'taxa_altas':       self.taxa_altas,
            'ps_atendimentos':  self.ps_atendimentos,
        }