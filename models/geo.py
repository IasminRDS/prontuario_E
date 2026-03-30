# -*- coding: utf-8 -*-
"""
Model de Geolocalização e Análise Geográfica
Prontuário Único - SUS
"""

from database.db import db
from datetime import datetime


class Localizacao(db.Model):
    """Localização de Pacientes e Unidades"""
    __tablename__ = 'localizacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=True)
    
    # Dados geográficos
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    endereco = db.Column(db.String(500), nullable=True)
    cep = db.Column(db.String(20), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    
    # Detalhes
    tipo = db.Column(db.String(50), nullable=False)  # residencia, trabalho, unidade
    ativo = db.Column(db.Boolean, default=True)
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    paciente = db.relationship('Paciente', backref='localizacoes')
    unidade = db.relationship('Unidade', backref='localizacoes')

    def __repr__(self):
        return f'<Localizacao {self.tipo} ({self.latitude}, {self.longitude})>'


class AcessibilidadeRegiao(db.Model):
    """Avalia acessibilidade por região/município"""
    __tablename__ = 'acessibilidade_regiao'
    
    id = db.Column(db.Integer, primary_key=True)
    regiao = db.Column(db.String(100), nullable=False, unique=True)
    estado = db.Column(db.String(2), nullable=False)
    
    # Indicadores de acessibilidade
    distancia_media_unidade_km = db.Column(db.Float, nullable=True)
    tempo_medio_acesso_minutos = db.Column(db.Float, nullable=True)
    indice_acessibilidade = db.Column(db.Float, nullable=True)  # 0-100
    
    # População
    populacao_estimada = db.Column(db.Integer, nullable=True)
    populacao_atendida = db.Column(db.Integer, default=0)
    
    # Unidades disponíveis
    total_unidades = db.Column(db.Integer, default=0)
    unidades_basicas = db.Column(db.Integer, default=0)
    unidades_especializada = db.Column(db.Integer, default=0)
    
    # Recursos
    total_leitos = db.Column(db.Integer, default=0)
    total_profissionais = db.Column(db.Integer, default=0)
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def acessibilidade_label(self):
        """Classifica acessibilidade"""
        if not self.indice_acessibilidade:
            return ('Sem dados', 'cinza')
        if self.indice_acessibilidade >= 80:
            return ('Ótima', 'verde')
        elif self.indice_acessibilidade >= 60:
            return ('Boa', 'azul')
        elif self.indice_acessibilidade >= 40:
            return ('Regular', 'amarelo')
        else:
            return ('Ruim', 'vermelho')

    def __repr__(self):
        return f'<AcessibilidadeRegiao {self.regiao}>'


class DemandaPorRegiao(db.Model):
    """Análise de demanda por região"""
    __tablename__ = 'demanda_por_regiao'
    
    id = db.Column(db.Integer, primary_key=True)
    regiao = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    mes_ano = db.Column(db.String(7), nullable=False)  # YYYY-MM
    
    # Contadores de demanda
    total_pacientes = db.Column(db.Integer, default=0)
    total_atendimentos = db.Column(db.Integer, default=0)
    total_internacoes = db.Column(db.Integer, default=0)
    
    # Procedimentos
    procedimentos_basicos = db.Column(db.Integer, default=0)
    procedimentos_complexos = db.Column(db.Integer, default=0)
    
    # CIDs mais prevalentes
    cids_top_10 = db.Column(db.JSON, nullable=True)
    
    # Prognóstico
    demanda_prevista_proxima = db.Column(db.Integer, default=0)
    percentual_crescimento = db.Column(db.Float, nullable=True)
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DemandaPorRegiao {self.regiao} {self.mes_ano}>'