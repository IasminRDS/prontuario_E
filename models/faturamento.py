# -*- coding: utf-8 -*-
"""
Model de Faturamento - AIH e APAC (SIH/SIA)
Prontuário Único - SUS
"""

from database.db import db
from datetime import datetime


class AIH(db.Model):
    """Autorização de Internação Hospitalar (SIH)"""
    __tablename__ = 'aih'
    
    id = db.Column(db.Integer, primary_key=True)
    internacao_id = db.Column(db.Integer, db.ForeignKey('internacoes.id'), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'), nullable=True)
    numero_aih = db.Column(db.String(20), nullable=True)
    tipo_aih = db.Column(db.String(5), default='1')
    competencia = db.Column(db.String(7), nullable=True)
    cid_principal = db.Column(db.String(10), nullable=True)
    cid_secundario = db.Column(db.String(10), nullable=True)
    cid_causa_obito = db.Column(db.String(10), nullable=True)
    carater_internacao = db.Column(db.String(2), default='01')
    procedimento_principal = db.Column(db.String(20), nullable=True)
    procedimento_secundario = db.Column(db.String(20), nullable=True)
    data_internacao = db.Column(db.Date, nullable=True)
    data_saida = db.Column(db.Date, nullable=True)
    dias_permanencia = db.Column(db.Integer, nullable=True)
    motivo_saida = db.Column(db.String(2), nullable=True)
    valor_total = db.Column(db.Float, nullable=True)
    valor_sh = db.Column(db.Float, nullable=True)
    valor_sp = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='rascunho')
    observacoes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    internacao = db.relationship('Internacao', backref='aih')
    unidade = db.relationship('Unidade', backref='aihs')
    paciente = db.relationship('Paciente', backref='aihs')
    medico = db.relationship('Medico', backref='aihs')

    STATUS_LABELS = {
        'rascunho': ('Rascunho', 'cinza'),
        'pronto': ('Pronto', 'azul'),
        'enviado': ('Enviado', 'amarelo'),
        'aprovado': ('Aprovado', 'verde'),
        'glosado': ('Glosado', 'vermelho'),
        'pago': ('Pago', 'verde'),
    }
    
    MOTIVO_SAIDA_LABELS = {
        '11': 'Alta curado', '12': 'Alta melhorado',
        '13': 'Alta a pedido', '14': 'Alta c/ retorno',
        '15': 'Evasão', '16': 'Transferência',
        '21': 'Óbito c/ declaração', '22': 'Óbito s/ declaração',
    }

    @property
    def status_label(self):
        """Retorna label e cor do status"""
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def motivo_saida_label(self):
        """Retorna label do motivo da saída"""
        return self.MOTIVO_SAIDA_LABELS.get(self.motivo_saida, self.motivo_saida or '—')

    def __repr__(self):
        return f'<AIH {self.numero_aih}>'


class APAC(db.Model):
    """Autorização de Procedimento de Alta Complexidade (SIA)"""
    __tablename__ = 'apac'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'), nullable=True)
    numero_apac = db.Column(db.String(20), nullable=True)
    tipo = db.Column(db.String(20), default='inicial')
    procedimento = db.Column(db.String(20), nullable=True)
    cid = db.Column(db.String(10), nullable=True)
    competencia = db.Column(db.String(7), nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)
    quantidade = db.Column(db.Integer, default=1)
    valor_total = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='rascunho')
    justificativa = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    paciente = db.relationship('Paciente', backref='apacs')
    unidade = db.relationship('Unidade', backref='apacs')
    medico = db.relationship('Medico', backref='apacs')

    STATUS_LABELS = {
        'rascunho': ('Rascunho', 'cinza'),
        'pronto': ('Pronto', 'azul'),
        'enviado': ('Enviado', 'amarelo'),
        'aprovado': ('Aprovado', 'verde'),
        'glosado': ('Glosado', 'vermelho'),
        'pago': ('Pago', 'verde'),
    }

    @property
    def status_label(self):
        """Retorna label e cor do status"""
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    def __repr__(self):
        return f'<APAC {self.numero_apac}>'


class ProcessoFaturamento(db.Model):
    """Processo de Faturamento - Controla AIH e APAC"""
    __tablename__ = 'processo_faturamento'
    
    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    competencia = db.Column(db.String(7), nullable=False)  # YYYY-MM
    tipo = db.Column(db.String(10), nullable=False)  # 'AIH' ou 'APAC'
    
    # Contadores
    total_registros = db.Column(db.Integer, default=0)
    total_aprovado = db.Column(db.Integer, default=0)
    total_glosado = db.Column(db.Integer, default=0)
    total_pago = db.Column(db.Integer, default=0)
    
    # Valores
    valor_total_registrado = db.Column(db.Float, default=0.0)
    valor_total_aprovado = db.Column(db.Float, default=0.0)
    valor_total_glosado = db.Column(db.Float, default=0.0)
    valor_total_pago = db.Column(db.Float, default=0.0)
    
    # Status do processo
    status = db.Column(db.String(20), default='em_preparacao')
    # em_preparacao | em_analise | enviado | aprovado | pago | encerrado
    
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_envio = db.Column(db.DateTime, nullable=True)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    
    # Audit
    criado_por = db.Column(db.String(200), nullable=True)
    atualizado_por = db.Column(db.String(200), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    observacoes = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    unidade = db.relationship('Unidade', backref='processos_faturamento')

    STATUS_LABELS = {
        'em_preparacao': ('Em Preparação', 'cinza'),
        'em_analise': ('Em Análise', 'azul'),
        'enviado': ('Enviado', 'amarelo'),
        'aprovado': ('Aprovado', 'verde'),
        'pago': ('Pago', 'verde escuro'),
        'encerrado': ('Encerrado', 'preto'),
    }

    @property
    def status_label(self):
        """Retorna label e cor do status"""
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    @property
    def percentual_aprovacao(self):
        """Calcula percentual de aprovação"""
        if self.total_registros == 0:
            return 0
        return round((self.total_aprovado / self.total_registros) * 100, 2)

    @property
    def percentual_glosado(self):
        """Calcula percentual de glosa"""
        if self.total_registros == 0:
            return 0
        return round((self.total_glosado / self.total_registros) * 100, 2)

    def __repr__(self):
        return f'<ProcessoFaturamento {self.tipo}/{self.competencia}>'