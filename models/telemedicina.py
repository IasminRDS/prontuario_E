# -*- coding: utf-8 -*-
"""
Model de Telemedicina e Monitoramento
"""
from database.db import db
from datetime import datetime
from enum import Enum

class StatusConsulta(Enum):
    AGENDADA = 'agendada'
    EM_ANDAMENTO = 'em_andamento'
    CONCLUIDA = 'concluida'
    CANCELADA = 'cancelada'

class TipoMidia(Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    TEXTO = 'texto'

class ConsultaTelemedicina(db.Model):
    """Consultas via telemedicina"""
    __tablename__ = 'consulta_telemedicina'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)  # ← CORRIJA: 'pacientes'
    profissional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    data_agendada = db.Column(db.DateTime, nullable=False)
    data_inicio = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)
    
    status = db.Column(db.String(20), default=StatusConsulta.AGENDADA.value)
    tipo_midia = db.Column(db.String(20), default=TipoMidia.VIDEO.value)
    
    # Sala de conferência
    room_id = db.Column(db.String(100))
    link_acesso = db.Column(db.String(255))
    senha_acesso = db.Column(db.String(50))
    
    # Consulta
    queixa_principal = db.Column(db.String(255))
    diagnostico = db.Column(db.String(255))
    prescricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    
    # Gravação
    gravado = db.Column(db.Boolean, default=False)
    arquivo_gravacao = db.Column(db.String(255))
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.now)
    
    paciente = db.relationship('Paciente', backref='consultas_telemedicina')
    profissional = db.relationship('User', backref='consultas_telemedicina')
    
    def gerar_sala_conferencia(self):
        """Gera sala de conferência para consulta"""
        self.room_id = f"prontuario_{self.id}_{datetime.now().timestamp()}"
        self.link_acesso = f"https://meet.jit.si/{self.room_id}"
        db.session.commit()
        return self.link_acesso

class MonitoramentoPaciente(db.Model):
    """Monitoramento remoto de pacientes"""
    __tablename__ = 'monitoramento_paciente'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)  # ← CORRIJA: 'pacientes'
    profissional_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    
    # Sinais vitais
    frequencia_cardiaca = db.Column(db.Integer)
    pressao_arterial = db.Column(db.String(20))
    saturacao_oxigenio = db.Column(db.Float)
    temperatura = db.Column(db.Float)
    frequencia_respiratoria = db.Column(db.Integer)
    glicemia = db.Column(db.Float)
    
    # Ativo?
    ativo = db.Column(db.Boolean, default=True)
    
    paciente = db.relationship('Paciente', backref='monitoramentos')
    profissional = db.relationship('User', backref='monitoramentos')