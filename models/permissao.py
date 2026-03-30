# -*- coding: utf-8 -*-
from database.db import db
from datetime import datetime
from enum import Enum

class TipoAcesso(Enum):
    """Tipos de acesso no sistema"""
    NACIONAL = 'nacional'
    ESTADUAL = 'estadual'
    REGIONAL = 'regional'
    MUNICIPAL = 'municipal'
    UNIDADE = 'unidade'
    PROFISSIONAL = 'profissional'
    PACIENTE = 'paciente'

class Permissao(db.Model):
    """Permissões do sistema"""
    __tablename__ = 'permissao'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.String(255))
    modulo = db.Column(db.String(50))
    acao = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Permissao {self.nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'modulo': self.modulo,
            'acao': self.acao,
        }

class Role(db.Model):
    """Funções/Papéis do sistema"""
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(255))
    tipo_acesso = db.Column(db.String(20), default=TipoAcesso.UNIDADE.value)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    # Relacionamentos (SEM usuarios - remover)
    permissoes_rel = db.relationship('RolePermissao', backref='role', lazy=True, cascade='all, delete-orphan')
    
    def tem_permissao(self, nome_permissao):
        """Verifica se a role tem uma permissão"""
        return any(rp.permissao.nome == nome_permissao for rp in self.permissoes_rel)
    
    def tem_modulo(self, modulo):
        """Verifica se a role tem acesso a um módulo"""
        return any(rp.permissao.modulo == modulo for rp in self.permissoes_rel)
    
    def adicionar_permissao(self, permissao):
        """Adiciona permissão à role"""
        if not self.tem_permissao(permissao.nome):
            rp = RolePermissao(role=self, permissao=permissao)
            db.session.add(rp)
    
    def remover_permissao(self, permissao):
        """Remove permissão da role"""
        rp = RolePermissao.query.filter_by(
            role_id=self.id,
            permissao_id=permissao.id
        ).first()
        if rp:
            db.session.delete(rp)
    
    def __repr__(self):
        return f'<Role {self.nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'tipo_acesso': self.tipo_acesso,
            'ativo': self.ativo,
            'permissoes': [rp.permissao.to_dict() for rp in self.permissoes_rel],
        }

class RolePermissao(db.Model):
    """Associação entre Roles e Permissões"""
    __tablename__ = 'role_permissao'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permissao_id = db.Column(db.Integer, db.ForeignKey('permissao.id'), nullable=False)
    
    permissao = db.relationship('Permissao')
    
    __table_args__ = (db.UniqueConstraint('role_id', 'permissao_id'),)

class AcessoEstadual(db.Model):
    """Controle granular de acesso por estado/região/município"""
    __tablename__ = 'acesso_estadual'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Localização
    estado = db.Column(db.String(2), nullable=False)
    tipo_acesso = db.Column(db.String(20), nullable=False)
    
    # Regiões
    regiao = db.Column(db.String(100))
    
    # Municípios, Unidades, Setores (JSON)
    municipios = db.Column(db.JSON)
    unidades = db.Column(db.JSON)
    setores = db.Column(db.JSON)
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    motivo_inativacao = db.Column(db.String(255))
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    
    # Auditoria
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'))
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    usuario = db.relationship('User', foreign_keys=[usuario_id], backref='acesso_estadual')
    criador = db.relationship('User', foreign_keys=[criado_por])
    
    def pode_acessar_estado(self, estado):
        """Verifica se pode acessar um estado"""
        if self.tipo_acesso == TipoAcesso.NACIONAL.value:
            return True
        return self.estado == estado
    
    def pode_acessar_municipio(self, municipio):
        """Verifica se pode acessar um município"""
        if self.tipo_acesso in [TipoAcesso.NACIONAL.value, TipoAcesso.ESTADUAL.value]:
            return True
        if self.municipios:
            return municipio in self.municipios
        return False
    
    def pode_acessar_unidade(self, unidade_id):
        """Verifica se pode acessar uma unidade"""
        if self.tipo_acesso in [TipoAcesso.NACIONAL.value, TipoAcesso.ESTADUAL.value]:
            return True
        if self.unidades:
            return int(unidade_id) in self.unidades
        return False
    
    def pode_acessar_setor(self, unidade_id, setor_id):
        """Verifica se pode acessar um setor"""
        if self.tipo_acesso in [TipoAcesso.NACIONAL.value, TipoAcesso.ESTADUAL.value]:
            return True
        if self.setores:
            setores_unidade = self.setores.get(str(unidade_id), [])
            return int(setor_id) in setores_unidade
        return False
    
    def __repr__(self):
        return f'<AcessoEstadual {self.usuario.nome} - {self.estado}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'estado': self.estado,
            'tipo_acesso': self.tipo_acesso,
            'municipios': self.municipios,
            'unidades': self.unidades,
            'ativo': self.ativo,
            'data_inicio': self.data_inicio.isoformat(),
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
        }