from database.db import db
from datetime import datetime

class Atendimento(db.Model):
    __tablename__ = 'atendimentos'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'), nullable=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)

    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(50), nullable=False, default='consulta')
    # tipo: consulta | urgencia | retorno | exame | vacina | procedimento

    status = db.Column(db.String(20), default='agendado')
    # status: agendado | em_atendimento | finalizado | cancelado

    queixa_principal = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    unidade = db.relationship('Unidade', backref='atendimentos')
    prontuario = db.relationship('Prontuario', backref='atendimento', uselist=False)

    def __repr__(self):
        return f'<Atendimento {self.id} - {self.paciente_id}>'
