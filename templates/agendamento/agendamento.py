from database.db import db
from datetime import datetime

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'

    id           = db.Column(db.Integer, primary_key=True)
    paciente_id  = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    medico_id    = db.Column(db.Integer, db.ForeignKey('medicos.id'),   nullable=True)
    unidade_id   = db.Column(db.Integer, db.ForeignKey('unidades.id'),  nullable=False)
    criado_por   = db.Column(db.Integer, db.ForeignKey('users.id'),     nullable=True)

    data_hora    = db.Column(db.DateTime, nullable=False)
    tipo         = db.Column(db.String(30), default='consulta')
    # consulta | retorno | exame | vacina | procedimento | urgencia

    status       = db.Column(db.String(20), default='agendado')
    # agendado | confirmado | em_atendimento | finalizado | cancelado | falta

    observacoes  = db.Column(db.Text,    nullable=True)
    motivo_cancel= db.Column(db.String(200), nullable=True)

    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em= db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paciente = db.relationship('Paciente',  backref='agendamentos')
    medico   = db.relationship('Medico',    backref='agendamentos')
    unidade  = db.relationship('Unidade',   backref='agendamentos')

    STATUS_LABELS = {
        'agendado':        ('Agendado',        'cinza'),
        'confirmado':      ('Confirmado',       'azul'),
        'em_atendimento':  ('Em atendimento',   'amarelo'),
        'finalizado':      ('Finalizado',       'verde'),
        'cancelado':       ('Cancelado',        'vermelho'),
        'falta':           ('Falta',            'vermelho'),
    }

    TIPO_LABELS = {
        'consulta':     'Consulta',
        'retorno':      'Retorno',
        'exame':        'Exame',
        'vacina':       'Vacinação',
        'procedimento': 'Procedimento',
        'urgencia':     'Urgência',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def tipo_label(self):
        return self.TIPO_LABELS.get(self.tipo, self.tipo.capitalize())

    def __repr__(self):
        return f'<Agendamento {self.id} {self.data_hora}>'
