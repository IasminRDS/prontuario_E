# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime


class AtendimentoPS(db.Model):
    __tablename__ = 'atendimentos_ps'
    id               = db.Column(db.Integer, primary_key=True)
    paciente_id      = db.Column(db.Integer, db.ForeignKey('pacientes.id'),  nullable=False)
    unidade_id       = db.Column(db.Integer, db.ForeignKey('unidades.id'),   nullable=False)
    medico_id        = db.Column(db.Integer, db.ForeignKey('medicos.id'),    nullable=True)
    triagem_id       = db.Column(db.Integer, db.ForeignKey('triagens.id'),   nullable=True)
    criado_por       = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=True)
    data_entrada     = db.Column(db.DateTime, default=datetime.utcnow)
    queixa_principal = db.Column(db.String(200), nullable=True)
    modo_chegada     = db.Column(db.String(30), default='espontaneo')
    classificacao    = db.Column(db.String(20), default='verde')
    status           = db.Column(db.String(30), default='aguardando_triagem')
    data_triagem     = db.Column(db.DateTime, nullable=True)
    data_chamada     = db.Column(db.DateTime, nullable=True)
    data_atendimento = db.Column(db.DateTime, nullable=True)
    data_desfecho    = db.Column(db.DateTime, nullable=True)
    desfecho         = db.Column(db.String(30), nullable=True)
    cid              = db.Column(db.String(10), nullable=True)
    hipotese_diag    = db.Column(db.String(200), nullable=True)
    conduta          = db.Column(db.Text, nullable=True)
    observacoes      = db.Column(db.Text, nullable=True)
    paciente = db.relationship('Paciente', backref='atendimentos_ps')
    medico   = db.relationship('Medico',   backref='atendimentos_ps')
    triagem  = db.relationship('Triagem',  backref='atendimento_ps')

    COR_INFO = {
        'vermelho': ('Emergência',    '#C0392B', 'Imediato'),
        'laranja':  ('Muito urgente', '#E67E22', '10 min'),
        'amarelo':  ('Urgente',       '#F1C40F', '60 min'),
        'verde':    ('Pouco urgente', '#27AE60', '120 min'),
        'azul':     ('Não urgente',   '#2980B9', '240 min'),
    }
    STATUS_LABELS = {
        'aguardando_triagem':     ('Aguardando triagem',    'cinza'),
        'triagem_realizada':      ('Triagem realizada',     'azul'),
        'aguardando_atendimento': ('Aguardando atendimento','amarelo'),
        'em_atendimento':         ('Em atendimento',        'azul'),
        'em_observacao':          ('Em observação',         'amarelo'),
        'alta':                   ('Alta',                  'verde'),
        'internado':              ('Internado',             'verde'),
        'transferido':            ('Transferido',           'cinza'),
        'obito':                  ('Óbito',                 'vermelho'),
        'evasao':                 ('Evasão',                'vermelho'),
    }

    @property
    def cor_info(self):
        return self.COR_INFO.get(self.classificacao, ('Indefinido', '#888888', '—'))

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def tempo_espera_min(self):
        ref = self.data_atendimento or datetime.utcnow()
        return int((ref - self.data_entrada).total_seconds() / 60)

    @property
    def tempo_total_min(self):
        if self.data_desfecho:
            return int((self.data_desfecho - self.data_entrada).total_seconds() / 60)
        return None