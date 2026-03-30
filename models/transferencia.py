# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime


class TransferenciaPaciente(db.Model):
    __tablename__ = 'transferencias_pacientes'

    id                  = db.Column(db.Integer, primary_key=True)
    paciente_id         = db.Column(db.Integer, db.ForeignKey('pacientes.id'),    nullable=False)
    internacao_id       = db.Column(db.Integer, db.ForeignKey('internacoes.id'),  nullable=True)
    unidade_origem_id   = db.Column(db.Integer, db.ForeignKey('unidades.id'),     nullable=False)
    unidade_destino_id  = db.Column(db.Integer, db.ForeignKey('unidades.id'),     nullable=False)
    solicitado_por      = db.Column(db.Integer, db.ForeignKey('users.id'),        nullable=True)

    motivo              = db.Column(db.Text,        nullable=False)
    cid                 = db.Column(db.String(10),  nullable=True)
    condicao_transporte = db.Column(db.String(50),  nullable=True)
    # maca | cadeira | ambulatorio | uti_movel | helicoptero
    prioridade          = db.Column(db.String(20),  default='eletiva')
    # eletiva | urgente | emergencia

    status              = db.Column(db.String(20),  default='solicitada')
    # solicitada | aceita | recusada | em_transito | concluida | cancelada

    data_solicitacao    = db.Column(db.DateTime, default=datetime.utcnow)
    data_prevista       = db.Column(db.DateTime, nullable=True)
    data_saida          = db.Column(db.DateTime, nullable=True)
    data_chegada        = db.Column(db.DateTime, nullable=True)

    resumo_clinico      = db.Column(db.Text, nullable=True)
    motivo_recusa       = db.Column(db.Text, nullable=True)
    observacoes         = db.Column(db.Text, nullable=True)

    paciente        = db.relationship('Paciente',  backref='transferencias')
    internacao      = db.relationship('Internacao', backref='transferencias')
    unidade_origem  = db.relationship('Unidade',   foreign_keys=[unidade_origem_id],
                                       backref='transferencias_enviadas')
    unidade_destino = db.relationship('Unidade',   foreign_keys=[unidade_destino_id],
                                       backref='transferencias_recebidas')
    solicitante     = db.relationship('User',       backref='transferencias')

    STATUS_LABELS = {
        'solicitada':  ('Solicitada',   'cinza'),
        'aceita':      ('Aceita',       'azul'),
        'recusada':    ('Recusada',     'vermelho'),
        'em_transito': ('Em trânsito',  'amarelo'),
        'concluida':   ('Concluída',    'verde'),
        'cancelada':   ('Cancelada',    'vermelho'),
    }
    PRIORIDADE_LABELS = {
        'eletiva':    ('Eletiva',    'cinza'),
        'urgente':    ('Urgente',    'amarelo'),
        'emergencia': ('Emergência', 'vermelho'),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def prioridade_label(self):
        return self.PRIORIDADE_LABELS.get(self.prioridade, (self.prioridade, 'cinza'))

    def __repr__(self):
        return f'<Transferencia {self.id}>'