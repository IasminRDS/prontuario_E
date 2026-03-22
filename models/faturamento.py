# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime


class AIH(db.Model):
    __tablename__ = 'aih'
    id               = db.Column(db.Integer, primary_key=True)
    internacao_id    = db.Column(db.Integer, db.ForeignKey('internacoes.id'),  nullable=False)
    unidade_id       = db.Column(db.Integer, db.ForeignKey('unidades.id'),     nullable=False)
    paciente_id      = db.Column(db.Integer, db.ForeignKey('pacientes.id'),    nullable=False)
    medico_id        = db.Column(db.Integer, db.ForeignKey('medicos.id'),      nullable=True)
    numero_aih       = db.Column(db.String(20), nullable=True)
    tipo_aih         = db.Column(db.String(5),  default='1')
    competencia      = db.Column(db.String(7),  nullable=True)
    cid_principal    = db.Column(db.String(10), nullable=True)
    cid_secundario   = db.Column(db.String(10), nullable=True)
    cid_causa_obito  = db.Column(db.String(10), nullable=True)
    carater_internacao = db.Column(db.String(2), default='01')
    procedimento_principal  = db.Column(db.String(20), nullable=True)
    procedimento_secundario = db.Column(db.String(20), nullable=True)
    data_internacao  = db.Column(db.Date, nullable=True)
    data_saida       = db.Column(db.Date, nullable=True)
    dias_permanencia = db.Column(db.Integer, nullable=True)
    motivo_saida     = db.Column(db.String(2), nullable=True)
    valor_total      = db.Column(db.Float, nullable=True)
    valor_sh         = db.Column(db.Float, nullable=True)
    valor_sp         = db.Column(db.Float, nullable=True)
    status           = db.Column(db.String(20), default='rascunho')
    observacoes      = db.Column(db.Text, nullable=True)
    criado_em        = db.Column(db.DateTime, default=datetime.utcnow)
    internacao = db.relationship('Internacao', backref='aih')
    unidade    = db.relationship('Unidade',    backref='aihs')
    paciente   = db.relationship('Paciente',   backref='aihs')
    medico     = db.relationship('Medico',     backref='aihs')

    STATUS_LABELS = {
        'rascunho': ('Rascunho', 'cinza'),
        'pronto':   ('Pronto',   'azul'),
        'enviado':  ('Enviado',  'amarelo'),
        'aprovado': ('Aprovado', 'verde'),
        'glosado':  ('Glosado',  'vermelho'),
        'pago':     ('Pago',     'verde'),
    }
    MOTIVO_SAIDA_LABELS = {
        '11': 'Alta curado',    '12': 'Alta melhorado',
        '13': 'Alta a pedido',  '14': 'Alta c/ retorno',
        '15': 'Evasão',         '16': 'Transferência',
        '21': 'Óbito c/ declaração', '22': 'Óbito s/ declaração',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def motivo_saida_label(self):
        return self.MOTIVO_SAIDA_LABELS.get(self.motivo_saida, self.motivo_saida or '—')


class APAC(db.Model):
    __tablename__ = 'apac'
    id           = db.Column(db.Integer, primary_key=True)
    paciente_id  = db.Column(db.Integer, db.ForeignKey('pacientes.id'),  nullable=False)
    unidade_id   = db.Column(db.Integer, db.ForeignKey('unidades.id'),   nullable=False)
    medico_id    = db.Column(db.Integer, db.ForeignKey('medicos.id'),    nullable=True)
    numero_apac  = db.Column(db.String(20), nullable=True)
    tipo         = db.Column(db.String(20), default='inicial')
    procedimento = db.Column(db.String(20), nullable=True)
    cid          = db.Column(db.String(10), nullable=True)
    competencia  = db.Column(db.String(7),  nullable=True)
    data_inicio  = db.Column(db.Date, nullable=True)
    data_fim     = db.Column(db.Date, nullable=True)
    quantidade   = db.Column(db.Integer, default=1)
    valor_total  = db.Column(db.Float, nullable=True)
    status       = db.Column(db.String(20), default='rascunho')
    justificativa= db.Column(db.Text, nullable=True)
    observacoes  = db.Column(db.Text, nullable=True)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)
    paciente = db.relationship('Paciente', backref='apacs')
    unidade  = db.relationship('Unidade',  backref='apacs')
    medico   = db.relationship('Medico',   backref='apacs')

    STATUS_LABELS = {
        'rascunho': ('Rascunho', 'cinza'),
        'pronto':   ('Pronto',   'azul'),
        'enviado':  ('Enviado',  'amarelo'),
        'aprovado': ('Aprovado', 'verde'),
        'glosado':  ('Glosado',  'vermelho'),
        'pago':     ('Pago',     'verde'),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))