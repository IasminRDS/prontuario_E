# -*- coding: utf-8 -*-
"""
Model de Vagas e Transferências
Versão simplificada sem foreign keys desnecessárias
"""
from database.db import db
from datetime import datetime
from enum import Enum

class StatusVaga(Enum):
    DISPONIVEL = 'disponivel'
    RESERVADA = 'reservada'
    OCUPADA = 'ocupada'
    INDISPONIVEL = 'indisponivel'

class NivelUrgencia(Enum):
    ELETIVA = 'eletiva'
    NORMAL = 'normal'
    URGENTE = 'urgente'
    EMERGENCIA = 'emergencia'

class StatusTransferencia(Enum):
    PENDENTE = 'pendente'
    ACEITA = 'aceita'
    RECUSADA = 'recusada'
    TRANSFERIDO = 'transferido'
    CANCELADA = 'cancelada'

class Vaga(db.Model):
    """Model simplificado de Vaga de Leito"""
    __tablename__ = 'vaga'
    
    id = db.Column(db.Integer, primary_key=True)
    leito_id = db.Column(db.Integer, nullable=False)  # Apenas ID, sem FK
    setor_id = db.Column(db.Integer, nullable=False)  # Apenas ID, sem FK
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default=StatusVaga.DISPONIVEL.value)
    tipo_paciente = db.Column(db.String(50))
    isolamento = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    
    # Paciente atual (se ocupada)
    paciente_id = db.Column(db.Integer, nullable=True)
    data_ocupacao = db.Column(db.DateTime)
    dias_ocupado = db.Column(db.Integer, default=0)
    
    # Reserva
    paciente_reservado_id = db.Column(db.Integer, nullable=True)
    data_reserva = db.Column(db.DateTime)
    tempo_reserva_minutos = db.Column(db.Integer, default=120)
    
    # Controle
    motivo_indisponivel = db.Column(db.String(255))
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento
    unidade = db.relationship('Unidade', backref='vagas')
    
    def pode_reservar(self):
        """Verifica se a vaga pode ser reservada"""
        return self.status == StatusVaga.DISPONIVEL.value and self.ativo
    
    def pode_ocupar(self):
        """Verifica se a vaga pode ser ocupada"""
        return self.status in [StatusVaga.DISPONIVEL.value, StatusVaga.RESERVADA.value] and self.ativo
    
    def reservar(self, paciente_id, tempo_minutos=120):
        """Reserva a vaga para um paciente"""
        if not self.pode_reservar():
            return False
        
        self.status = StatusVaga.RESERVADA.value
        self.paciente_reservado_id = paciente_id
        self.data_reserva = datetime.now()
        self.tempo_reserva_minutos = tempo_minutos
        db.session.commit()
        return True
    
    def ocupar(self, paciente_id):
        """Marca a vaga como ocupada"""
        if not self.pode_ocupar():
            return False
        
        self.status = StatusVaga.OCUPADA.value
        self.paciente_id = paciente_id
        self.data_ocupacao = datetime.now()
        self.paciente_reservado_id = None
        db.session.commit()
        return True
    
    def liberar_reserva(self):
        """Libera a reserva se expirou"""
        if self.status == StatusVaga.RESERVADA.value:
            tempo_decorrido = (datetime.now() - self.data_reserva).total_seconds() / 60
            if tempo_decorrido > self.tempo_reserva_minutos:
                self.status = StatusVaga.DISPONIVEL.value
                self.paciente_reservado_id = None
                db.session.commit()
                return True
        return False
    
    def liberar(self):
        """Libera a vaga"""
        self.status = StatusVaga.DISPONIVEL.value
        self.paciente_id = None
        self.data_ocupacao = None
        self.paciente_reservado_id = None
        db.session.commit()
    
    def indisponibilizar(self, motivo):
        """Marca vaga como indisponível"""
        self.status = StatusVaga.INDISPONIVEL.value
        self.motivo_indisponivel = motivo
        db.session.commit()
    
    def disponibilizar(self):
        """Marca vaga como disponível novamente"""
        self.status = StatusVaga.DISPONIVEL.value
        self.motivo_indisponivel = None
        db.session.commit()
    
    def calcular_dias_ocupado(self):
        """Calcula dias que a vaga está ocupada"""
        if self.data_ocupacao:
            self.dias_ocupado = (datetime.now() - self.data_ocupacao).days
            db.session.commit()
    
    def to_dict(self):
        self.calcular_dias_ocupado()
        return {
            'id': self.id,
            'leito_id': self.leito_id,
            'setor_id': self.setor_id,
            'unidade_id': self.unidade_id,
            'unidade_nome': self.unidade.nome if self.unidade else None,
            'status': self.status,
            'tipo_paciente': self.tipo_paciente,
            'isolamento': self.isolamento,
            'dias_ocupado': self.dias_ocupado,
            'ativo': self.ativo,
            'data_ocupacao': self.data_ocupacao.isoformat() if self.data_ocupacao else None,
        }

class SolicitacaoTransferencia(db.Model):
    """Model simplificado de Solicitações de Transferência"""
    __tablename__ = 'solicitacao_transferencia'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    
    # Origem e Destino (apenas IDs, sem FK)
    unidade_origem_id = db.Column(db.Integer, nullable=False)
    setor_origem_id = db.Column(db.Integer, nullable=True)
    unidade_destino_id = db.Column(db.Integer, nullable=True)
    setor_destino_id = db.Column(db.Integer, nullable=True)
    
    # Detalhes da Solicitação
    motivo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    urgencia = db.Column(db.String(20), default=NivelUrgencia.NORMAL.value)
    prioridade = db.Column(db.Integer, default=0)
    
    # Requisitos
    especialidade_necessaria = db.Column(db.String(100))
    tipo_isolamento = db.Column(db.String(50))
    tipo_leito_necessario = db.Column(db.String(50))
    observacoes_clinicas = db.Column(db.Text)
    
    # Status e Resposta
    status = db.Column(db.String(20), default=StatusTransferencia.PENDENTE.value)
    motivo_recusa = db.Column(db.String(255))
    data_solicitacao = db.Column(db.DateTime, default=datetime.now)
    data_resposta = db.Column(db.DateTime)
    resposta_usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Vaga Sugerida
    vaga_sugerida_id = db.Column(db.Integer, nullable=True)
    vagas_alternativas = db.Column(db.JSON)
    
    # Auditoria
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'))
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_transferencia = db.Column(db.DateTime)
    
    # Relacionamentos
    paciente = db.relationship('Paciente', backref='solicitacoes_transferencia')
    resposta_usuario = db.relationship('User', foreign_keys=[resposta_usuario_id])
    criador = db.relationship('User', foreign_keys=[criado_por])
    
    def calcular_prioridade(self):
        """Calcula prioridade baseado em urgência e tempo"""
        prioridade_base = {
            'emergencia': 100,
            'urgente': 75,
            'normal': 50,
            'eletiva': 25
        }
        
        base = prioridade_base.get(self.urgencia, 50)
        horas_decorridas = (datetime.now() - self.data_solicitacao).total_seconds() / 3600
        ajuste = min(horas_decorridas, 25)
        
        self.prioridade = min(base + ajuste, 100)
        db.session.commit()
        return self.prioridade
    
    def aceitar(self, vaga_id, usuario_id):
        """Aceita a transferência"""
        self.status = StatusTransferencia.ACEITA.value
        self.vaga_sugerida_id = vaga_id
        self.data_resposta = datetime.now()
        self.resposta_usuario_id = usuario_id
        db.session.commit()
    
    def recusar(self, motivo, usuario_id):
        """Recusa a transferência"""
        self.status = StatusTransferencia.RECUSADA.value
        self.motivo_recusa = motivo
        self.data_resposta = datetime.now()
        self.resposta_usuario_id = usuario_id
        db.session.commit()
    
    def transferir(self):
        """Marca como transferido"""
        self.status = StatusTransferencia.TRANSFERIDO.value
        self.data_transferencia = datetime.now()
        db.session.commit()
    
    def cancelar(self):
        """Cancela a transferência"""
        self.status = StatusTransferencia.CANCELADA.value
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'paciente_nome': self.paciente.nome if self.paciente else None,
            'unidade_origem_id': self.unidade_origem_id,
            'unidade_destino_id': self.unidade_destino_id,
            'motivo': self.motivo,
            'urgencia': self.urgencia,
            'prioridade': self.prioridade,
            'status': self.status,
            'data_solicitacao': self.data_solicitacao.isoformat(),
            'vaga_sugerida_id': self.vaga_sugerida_id,
        }