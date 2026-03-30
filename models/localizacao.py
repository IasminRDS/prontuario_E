# -*- coding: utf-8 -*-
"""
Model de Localização e Análise Geográfica
"""
from database.db import db
from datetime import datetime

class Localizacao(db.Model):
    """Coordenadas geográficas e informações de localização"""
    __tablename__ = 'localizacao'
    
    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), unique=True, nullable=False)
    
    # Coordenadas
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Endereço
    endereco = db.Column(db.String(255))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    
    # Dados geográficos
    regiao_saude = db.Column(db.String(100))
    drs = db.Column(db.String(100))
    mesorregiao = db.Column(db.String(100))
    microrregiao = db.Column(db.String(100))
    
    # Referência
    ponto_referencia = db.Column(db.String(255))
    
    # Dados de acesso
    tempo_medio_ambulancia = db.Column(db.Integer)
    cobertura_celular = db.Column(db.String(50))
    
    # Auditoria
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    unidade = db.relationship('Unidade', backref='localizacao')
    
    def get_coordenadas(self):
        """Retorna coordenadas como tupla"""
        return (self.latitude, self.longitude)
    
    def to_dict(self):
        return {
            'id': self.id,
            'unidade_id': self.unidade_id,
            'unidade_nome': self.unidade.nome if self.unidade else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'endereco': f"{self.endereco}, {self.numero}",
            'bairro': self.bairro,
            'municipio': self.municipio,
            'estado': self.estado,
            'regiao_saude': self.regiao_saude,
            'drs': self.drs,
        }

class AcessibilidadeRegiao(db.Model):
    """Análise de acessibilidade por região"""
    __tablename__ = 'acessibilidade_regiao'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    regiao_saude = db.Column(db.String(100))
    
    # População
    populacao_total = db.Column(db.Integer)
    populacao_risco = db.Column(db.Integer)
    
    # Unidades de saúde
    total_unidades = db.Column(db.Integer, default=0)
    postos_saude = db.Column(db.Integer, default=0)
    clinicas = db.Column(db.Integer, default=0)
    hospitais = db.Column(db.Integer, default=0)
    
    # Indicadores de saúde
    taxa_mortalidade = db.Column(db.Float)
    taxa_internacao = db.Column(db.Float)
    taxa_ocupacao_media = db.Column(db.Float)
    tempo_resposta_ambulancia = db.Column(db.Integer)
    
    # Cobertura
    cobertura_celular = db.Column(db.String(50))
    conexao_internet = db.Column(db.String(50))
    
    # Demanda estimada
    demanda_diaria = db.Column(db.Integer)
    demanda_semanal = db.Column(db.Integer)
    
    # Dados geográficos
    area_km2 = db.Column(db.Float)
    densidade_populacional = db.Column(db.Float)
    
    # Auditoria
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('municipio', 'estado'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'estado': self.estado,
            'regiao_saude': self.regiao_saude,
            'populacao': self.populacao_total,
            'total_unidades': self.total_unidades,
            'taxa_ocupacao': self.taxa_ocupacao_media,
            'demanda_diaria': self.demanda_diaria,
            'area_km2': self.area_km2,
        }

class DemandaPorRegiao(db.Model):
    """Análise de demanda por região em tempo real"""
    __tablename__ = 'demanda_por_regiao'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Integer)
    
    # Demanda atual
    atendimentos_ps = db.Column(db.Integer, default=0)
    internacoes_solicitadas = db.Column(db.Integer, default=0)
    transferencias_pendentes = db.Column(db.Integer, default=0)
    
    # Capacidade
    vagas_disponiveis = db.Column(db.Integer, default=0)
    taxa_ocupacao = db.Column(db.Float, default=0)
    
    # Score de urgência
    score_urgencia = db.Column(db.Integer)
    
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('municipio', 'estado', 'data', 'hora'),)
    
    def to_dict(self):
        return {
            'municipio': self.municipio,
            'estado': self.estado,
            'data': str(self.data),
            'hora': self.hora,
            'atendimentos_ps': self.atendimentos_ps,
            'internacoes_solicitadas': self.internacoes_solicitadas,
            'transferencias_pendentes': self.transferencias_pendentes,
            'vagas_disponiveis': self.vagas_disponiveis,
            'taxa_ocupacao': self.taxa_ocupacao,
            'score_urgencia': self.score_urgencia,
        }