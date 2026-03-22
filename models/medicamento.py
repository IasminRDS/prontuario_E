# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime

class Medicamento(db.Model):
    """Catálogo de medicamentos (RENAME = tabela de referência)."""
    __tablename__ = 'medicamentos'

    id          = db.Column(db.Integer, primary_key=True)
    nome_generico = db.Column(db.String(150), nullable=False)
    nome_comercial= db.Column(db.String(150), nullable=True)
    classe      = db.Column(db.String(100), nullable=True)
    apresentacao= db.Column(db.String(100), nullable=True)  # ex: comp. 500mg, sol. inj. 1mg/mL
    via_admin   = db.Column(db.String(50),  nullable=True)  # oral, EV, IM, SC, tópico
    controlado  = db.Column(db.Boolean, default=False)
    lista_rename= db.Column(db.String(10),  nullable=True)  # A1, A2, B1, C1 etc.
    ativo       = db.Column(db.Boolean, default=True)

    prescricoes = db.relationship('ItemPrescricao', backref='medicamento', lazy='dynamic')

    def __repr__(self):
        return f'<Medicamento {self.nome_generico}>'


class Prescricao(db.Model):
    """Cabeçalho de uma prescrição — pode ter vários itens."""
    __tablename__ = 'prescricoes'

    id              = db.Column(db.Integer, primary_key=True)
    paciente_id     = db.Column(db.Integer, db.ForeignKey('pacientes.id'),   nullable=False)
    prontuario_id   = db.Column(db.Integer, db.ForeignKey('prontuarios.id'), nullable=True)
    medico_id       = db.Column(db.Integer, db.ForeignKey('medicos.id'),     nullable=True)
    unidade_id      = db.Column(db.Integer, db.ForeignKey('unidades.id'),    nullable=False)

    tipo            = db.Column(db.String(20), default='ambulatorial')
    # ambulatorial | hospitalar | continuo

    status          = db.Column(db.String(20), default='ativa')
    # ativa | suspensa | concluida | cancelada

    observacoes     = db.Column(db.Text,    nullable=True)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)
    validade_dias   = db.Column(db.Integer,  nullable=True)  # para ambulatorial
    criado_por      = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=True)

    paciente  = db.relationship('Paciente',  backref='prescricoes')
    prontuario= db.relationship('Prontuario',backref='prescricoes')
    medico    = db.relationship('Medico',    backref='prescricoes')
    unidade   = db.relationship('Unidade',   backref='prescricoes')
    itens     = db.relationship('ItemPrescricao', backref='prescricao',
                                 cascade='all, delete-orphan')

    STATUS_LABELS = {
        'ativa':     ('Ativa',     'verde'),
        'suspensa':  ('Suspensa',  'amarelo'),
        'concluida': ('Concluída', 'cinza'),
        'cancelada': ('Cancelada', 'vermelho'),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    def __repr__(self):
        return f'<Prescricao {self.id}>'


class ItemPrescricao(db.Model):
    """Um medicamento dentro de uma prescrição."""
    __tablename__ = 'itens_prescricao'

    id              = db.Column(db.Integer, primary_key=True)
    prescricao_id   = db.Column(db.Integer, db.ForeignKey('prescricoes.id'),   nullable=False)
    medicamento_id  = db.Column(db.Integer, db.ForeignKey('medicamentos.id'),  nullable=True)

    nome_livre      = db.Column(db.String(200), nullable=True)  # se não vinculado ao catálogo
    dose            = db.Column(db.String(50),  nullable=True)  # ex: 500mg
    via             = db.Column(db.String(50),  nullable=True)  # ex: oral
    frequencia      = db.Column(db.String(80),  nullable=True)  # ex: 8/8h, 1x/dia
    duracao         = db.Column(db.String(50),  nullable=True)  # ex: 7 dias, uso contínuo
    quantidade      = db.Column(db.String(30),  nullable=True)  # ex: 21 comprimidos
    instrucoes      = db.Column(db.Text,        nullable=True)  # orientações especiais

    @property
    def nome_exibicao(self):
        if self.medicamento:
            return self.medicamento.nome_generico
        return self.nome_livre or '—'

    def __repr__(self):
        return f'<ItemPrescricao {self.nome_exibicao}>'
