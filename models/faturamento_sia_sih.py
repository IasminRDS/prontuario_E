# -*- coding: utf-8 -*-
"""
Model de Faturamento SIA/SIH - Controle de Processo de Faturamento
Prontuário Único - SUS
"""

from database.db import db
from datetime import datetime


class Faturamento(db.Model):
    """Registro base de faturamento (herança para AIH e APAC)"""
    __tablename__ = 'faturamento_base'
    
    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'), nullable=True)
    
    tipo = db.Column(db.String(10), nullable=False)  # AIH, APAC
    numero_processo = db.Column(db.String(30), nullable=True)
    competencia = db.Column(db.String(7), nullable=True)  # YYYY-MM
    
    # Valores
    valor_total = db.Column(db.Float, default=0.0)
    valor_glosa = db.Column(db.Float, default=0.0)
    valor_aprovado = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='rascunho')
    # rascunho | pronto | enviado | aprovado | glosado | pago
    
    # Datas
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    unidade = db.relationship('Unidade', backref='faturamentos_base')
    paciente = db.relationship('Paciente', backref='faturamentos_base')
    medico = db.relationship('Medico', backref='faturamentos_base')

    STATUS_LABELS = {
        'rascunho': ('Rascunho', 'cinza'),
        'pronto': ('Pronto', 'azul'),
        'enviado': ('Enviado', 'amarelo'),
        'aprovado': ('Aprovado', 'verde'),
        'glosado': ('Glosado', 'vermelho'),
        'pago': ('Pago', 'verde escuro'),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'cinza'))

    def __repr__(self):
        return f'<Faturamento {self.tipo}/{self.numero_processo}>'


class ProcessoFaturamentoSIH(db.Model):
    """Processo de Faturamento SIH - Controla lotes de AIH"""
    __tablename__ = 'processo_faturamento_sih'
    
    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    competencia = db.Column(db.String(7), nullable=False)  # YYYY-MM
    numero_lote = db.Column(db.String(30), nullable=True)
    
    # Contadores AIH
    total_aih = db.Column(db.Integer, default=0)
    total_aih_aprovado = db.Column(db.Integer, default=0)
    total_aih_glosado = db.Column(db.Integer, default=0)
    total_aih_pago = db.Column(db.Integer, default=0)
    
    # Valores AIH
    valor_total_aih = db.Column(db.Float, default=0.0)
    valor_aih_aprovado = db.Column(db.Float, default=0.0)
    valor_aih_glosado = db.Column(db.Float, default=0.0)
    valor_aih_pago = db.Column(db.Float, default=0.0)
    
    # Status do processo
    status = db.Column(db.String(20), default='em_preparacao')
    # em_preparacao | em_analise | enviado | aprovado | pago | encerrado
    
    # Datas
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
    
    # Relacionamento
    unidade = db.relationship('Unidade', backref='processos_sih')

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
        if self.total_aih == 0:
            return 0
        return round((self.total_aih_aprovado / self.total_aih) * 100, 2)

    @property
    def percentual_glosado(self):
        """Calcula percentual de glosa"""
        if self.total_aih == 0:
            return 0
        return round((self.total_aih_glosado / self.total_aih) * 100, 2)

    def __repr__(self):
        return f'<ProcessoFaturamentoSIH {self.competencia}>'


class ProcessoFaturamentoSIA(db.Model):
    """Processo de Faturamento SIA - Controla lotes de APAC"""
    __tablename__ = 'processo_faturamento_sia'
    
    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    competencia = db.Column(db.String(7), nullable=False)  # YYYY-MM
    numero_lote = db.Column(db.String(30), nullable=True)
    
    # Contadores APAC
    total_apac = db.Column(db.Integer, default=0)
    total_apac_aprovado = db.Column(db.Integer, default=0)
    total_apac_glosado = db.Column(db.Integer, default=0)
    total_apac_pago = db.Column(db.Integer, default=0)
    
    # Valores APAC
    valor_total_apac = db.Column(db.Float, default=0.0)
    valor_apac_aprovado = db.Column(db.Float, default=0.0)
    valor_apac_glosado = db.Column(db.Float, default=0.0)
    valor_apac_pago = db.Column(db.Float, default=0.0)
    
    # Status do processo
    status = db.Column(db.String(20), default='em_preparacao')
    # em_preparacao | em_analise | enviado | aprovado | pago | encerrado
    
    # Datas
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
    
    # Relacionamento
    unidade = db.relationship('Unidade', backref='processos_sia')

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
        if self.total_apac == 0:
            return 0
        return round((self.total_apac_aprovado / self.total_apac) * 100, 2)

    @property
    def percentual_glosado(self):
        """Calcula percentual de glosa"""
        if self.total_apac == 0:
            return 0
        return round((self.total_apac_glosado / self.total_apac) * 100, 2)

    def __repr__(self):
        return f'<ProcessoFaturamentoSIA {self.competencia}>'