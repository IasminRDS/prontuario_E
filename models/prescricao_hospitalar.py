# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime


class PrescricaoHospitalar(db.Model):
    """Prescrição médica hospitalar — válida por 24h, renovada diariamente."""
    __tablename__ = 'prescricoes_hospitalares'

    id              = db.Column(db.Integer, primary_key=True)
    internacao_id   = db.Column(db.Integer, db.ForeignKey('internacoes.id'),  nullable=False)
    medico_id       = db.Column(db.Integer, db.ForeignKey('medicos.id'),      nullable=True)
    unidade_id      = db.Column(db.Integer, db.ForeignKey('unidades.id'),     nullable=False)

    data_prescricao = db.Column(db.DateTime, default=datetime.utcnow)
    validade_ate    = db.Column(db.DateTime, nullable=True)   # normalmente +24h
    status          = db.Column(db.String(20), default='ativa')
    # ativa | suspensa | expirada | cancelada

    dieta           = db.Column(db.String(100), nullable=True)
    # ex: "Dieta oral hipossódica", "NPO", "SNE"
    decubito        = db.Column(db.String(80),  nullable=True)
    # ex: "Cabeceira 30°", "Decúbito lateral D"
    sinais_vitais   = db.Column(db.String(80),  nullable=True)
    # ex: "PA, FC, Tax a cada 4h"
    observacoes     = db.Column(db.Text,        nullable=True)

    assinado        = db.Column(db.Boolean, default=False)
    assinado_em     = db.Column(db.DateTime, nullable=True)

    internacao      = db.relationship('Internacao', backref='prescricoes_hosp')
    medico          = db.relationship('Medico',     backref='prescricoes_hosp')
    itens           = db.relationship('ItemPrescricaoHosp', backref='prescricao',
                                      cascade='all, delete-orphan')

    def assinar(self):
        self.assinado    = True
        self.assinado_em = datetime.utcnow()

    def __repr__(self):
        return f'<PrescricaoHospitalar {self.id}>'


class ItemPrescricaoHosp(db.Model):
    """Item individual de uma prescrição hospitalar."""
    __tablename__ = 'itens_prescricao_hosp'

    id              = db.Column(db.Integer, primary_key=True)
    prescricao_id   = db.Column(db.Integer, db.ForeignKey('prescricoes_hospitalares.id'), nullable=False)
    medicamento_id  = db.Column(db.Integer, db.ForeignKey('medicamentos.id'), nullable=True)

    nome_livre      = db.Column(db.String(200), nullable=True)
    dose            = db.Column(db.String(50),  nullable=True)   # ex: 500mg
    concentracao    = db.Column(db.String(50),  nullable=True)   # ex: 500mg/100mL
    diluicao        = db.Column(db.String(100), nullable=True)   # ex: SF 0,9% 100mL
    via             = db.Column(db.String(40),  nullable=True)   # EV, VO, SC, IM, SL
    velocidade      = db.Column(db.String(50),  nullable=True)   # ex: 21 gts/min, em 30min
    frequencia      = db.Column(db.String(60),  nullable=True)   # ex: 6/6h, 1x/dia às 8h
    horarios        = db.Column(db.String(100), nullable=True)   # ex: 8h - 14h - 20h
    duracao         = db.Column(db.String(50),  nullable=True)   # ex: 7 dias, ATÉ ALTA
    observacoes     = db.Column(db.Text,        nullable=True)
    ordem           = db.Column(db.Integer,     default=0)

    medicamento     = db.relationship('Medicamento')
    administracoes  = db.relationship('AdministracaoMed', backref='item',
                                      lazy='dynamic', cascade='all, delete-orphan')

    @property
    def nome_exibicao(self):
        if self.medicamento:
            return self.medicamento.nome_generico
        return self.nome_livre or '—'

    def __repr__(self):
        return f'<ItemPrescricaoHosp {self.nome_exibicao}>'


class AdministracaoMed(db.Model):
    """Registro de cada administração de medicamento pela enfermagem."""
    __tablename__ = 'administracoes_med'

    id              = db.Column(db.Integer, primary_key=True)
    item_id         = db.Column(db.Integer, db.ForeignKey('itens_prescricao_hosp.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    data_hora       = db.Column(db.DateTime, default=datetime.utcnow)
    status          = db.Column(db.String(20), default='administrado')
    # administrado | recusado | suspenso | paciente_ausente
    observacoes     = db.Column(db.String(200), nullable=True)

    profissional    = db.relationship('User', backref='administracoes_med')

    def __repr__(self):
        return f'<AdministracaoMed {self.id} {self.status}>'
