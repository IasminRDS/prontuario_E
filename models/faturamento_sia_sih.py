# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime
from enum import Enum

class TipoFaturamento(Enum):
    SIA = 'sia'  # Serviços de Atenção Ambulatorial
    SIH = 'sih'  # Sistema de Informações Hospitalares
    AIH = 'aih'  # Autorização de Internação Hospitalar

class StatusFaturamento(Enum):
    PENDENTE = 'pendente'
    PROCESSADO = 'processado'
    ENVIADO = 'enviado'
    APROVADO = 'aprovado'
    RECUSADO = 'recusado'

class Faturamento(db.Model):
    """Registro de faturamento SIA/SIH"""
    __tablename__ = 'faturamento'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), default=TipoFaturamento.SIH.value)
    status = db.Column(db.String(20), default=StatusFaturamento.PENDENTE.value)
    
    # Referências
    atendimento_id = db.Column(db.Integer, nullable=True)  # Sem FK
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)  # ← CORRIJA: 'pacientes'
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    
    # Dados SIA/SIH
    numero_aih = db.Column(db.String(20), unique=True)
    cbo_profissional = db.Column(db.String(10))
    codigo_procedimento = db.Column(db.String(20), nullable=False)
    descricao_procedimento = db.Column(db.String(255))
    
    # Valores
    valor_tabela = db.Column(db.Float)
    valor_cobrado = db.Column(db.Float)
    valor_apurado = db.Column(db.Float)
    
    # Diagnósticos (ICD-10)
    diagnostico_principal = db.Column(db.String(10))
    diagnosticos_secundarios = db.Column(db.JSON)
    
    # Procedimentos associados
    procedimentos_executados = db.Column(db.JSON)
    
    # Datas
    data_competencia = db.Column(db.Date, nullable=False)
    data_atendimento = db.Column(db.DateTime)
    data_processamento = db.Column(db.DateTime)
    data_envio = db.Column(db.DateTime)
    data_aprovacao = db.Column(db.DateTime)
    
    # Justificativa de recusa
    motivo_recusa = db.Column(db.Text)
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.now)
    atualizado_em = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    paciente = db.relationship('Paciente', backref='faturamentos')
    unidade = db.relationship('Unidade', backref='faturamentos')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'status': self.status,
            'numero_aih': self.numero_aih,
            'codigo_procedimento': self.codigo_procedimento,
            'valor_cobrado': self.valor_cobrado,
            'data_competencia': str(self.data_competencia),
            'paciente': self.paciente.nome if self.paciente else None,
            'unidade': self.unidade.nome if self.unidade else None,
        }

class ProcessoFaturamento(db.Model):
    """Processo de geração de lotes SIA/SIH"""
    __tablename__ = 'processo_faturamento'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    mes_competencia = db.Column(db.Integer, nullable=False)
    ano_competencia = db.Column(db.Integer, nullable=False)
    
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    
    status = db.Column(db.String(20), default='em_processamento')
    total_registros = db.Column(db.Integer, default=0)
    registros_processados = db.Column(db.Integer, default=0)
    valor_total = db.Column(db.Float, default=0)
    
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_conclusao = db.Column(db.DateTime)
    
    observacoes = db.Column(db.Text)
    
    unidade = db.relationship('Unidade', backref='processos_faturamento')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'mes_ano': f'{self.mes_competencia:02d}/{self.ano_competencia}',
            'status': self.status,
            'total': self.total_registros,
            'processados': self.registros_processados,
            'valor': self.valor_total,
        }