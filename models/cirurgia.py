# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime


class SalaCirurgica(db.Model):
    """Sala do centro cirúrgico."""
    __tablename__ = 'salas_cirurgicas'

    id      = db.Column(db.Integer, primary_key=True)
    nome    = db.Column(db.String(50), nullable=False)   # ex: CC-01, Sala de Urgência
    tipo    = db.Column(db.String(30), nullable=True)    # geral | ortopedia | cardiaca | urgencia
    status  = db.Column(db.String(20), default='livre')
    # livre | em_uso | em_limpeza | interditada
    ativo   = db.Column(db.Boolean, default=True)

    cirurgias = db.relationship('Cirurgia', backref='sala', lazy='dynamic')

    def __repr__(self):
        return f'<SalaCirurgica {self.nome}>'


class Cirurgia(db.Model):
    """Agendamento e registro de cirurgia."""
    __tablename__ = 'cirurgias'

    id              = db.Column(db.Integer, primary_key=True)
    paciente_id     = db.Column(db.Integer, db.ForeignKey('pacientes.id'),    nullable=False)
    internacao_id   = db.Column(db.Integer, db.ForeignKey('internacoes.id'),  nullable=True)
    sala_id         = db.Column(db.Integer, db.ForeignKey('salas_cirurgicas.id'), nullable=True)
    cirurgiao_id    = db.Column(db.Integer, db.ForeignKey('medicos.id'),      nullable=True)
    anestesista_id  = db.Column(db.Integer, db.ForeignKey('medicos.id'),      nullable=True)
    unidade_id      = db.Column(db.Integer, db.ForeignKey('unidades.id'),     nullable=False)
    criado_por      = db.Column(db.Integer, db.ForeignKey('users.id'),        nullable=True)

    # Procedimento
    procedimento    = db.Column(db.String(200), nullable=False)
    codigo_tuss     = db.Column(db.String(20),  nullable=True)   # código TUSS/SIGTAP
    cid             = db.Column(db.String(10),  nullable=True)
    tipo_anestesia  = db.Column(db.String(50),  nullable=True)
    # geral | raqui | peridural | local | sedacao | bloqueio

    # Classificação
    carater         = db.Column(db.String(20), default='eletiva')
    # eletiva | urgencia | emergencia
    especialidade   = db.Column(db.String(80), nullable=True)

    # Agendamento
    data_agendada   = db.Column(db.DateTime, nullable=True)
    duracao_prevista= db.Column(db.Integer,  nullable=True)   # minutos

    # Execução
    data_inicio     = db.Column(db.DateTime, nullable=True)
    data_fim        = db.Column(db.DateTime, nullable=True)

    status          = db.Column(db.String(20), default='agendada')
    # agendada | em_andamento | realizada | cancelada | suspensa

    # Relatório cirúrgico
    relatorio       = db.Column(db.Text, nullable=True)
    achados         = db.Column(db.Text, nullable=True)
    intercorrencias = db.Column(db.Text, nullable=True)
    materiais       = db.Column(db.Text, nullable=True)   # materiais e OPME usados
    cid_pos_op      = db.Column(db.String(10), nullable=True)

    # Pré-operatório
    checklist_pre   = db.Column(db.Text, nullable=True)   # JSON checklist
    observacoes     = db.Column(db.Text, nullable=True)

    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    paciente    = db.relationship('Paciente', backref='cirurgias')
    internacao  = db.relationship('Internacao', backref='cirurgias')
    cirurgiao   = db.relationship('Medico', foreign_keys=[cirurgiao_id],
                                   backref='cirurgias_como_cirurgiao')
    anestesista = db.relationship('Medico', foreign_keys=[anestesista_id],
                                   backref='cirurgias_como_anestesista')
    unidade     = db.relationship('Unidade', backref='cirurgias')

    STATUS_LABELS = {
        'agendada':     ('Agendada',     'cinza'),
        'em_andamento': ('Em andamento', 'amarelo'),
        'realizada':    ('Realizada',    'verde'),
        'cancelada':    ('Cancelada',    'vermelho'),
        'suspensa':     ('Suspensa',     'amarelo'),
    }

    CARATER_LABELS = {
        'eletiva':    ('Eletiva',    'azul'),
        'urgencia':   ('Urgência',   'amarelo'),
        'emergencia': ('Emergência', 'vermelho'),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def carater_label(self):
        return self.CARATER_LABELS.get(self.carater, (self.carater, 'cinza'))

    @property
    def duracao_real(self):
        if self.data_inicio and self.data_fim:
            return int((self.data_fim - self.data_inicio).total_seconds() / 60)
        return None

    def __repr__(self):
        return f'<Cirurgia {self.id} {self.procedimento[:30]}>'
