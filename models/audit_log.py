# -*- coding: utf-8 -*-
"""
Model de Auditoria - Log de todas as ações
Prontuário Único - SUS
"""

from database.db import db
from datetime import datetime


class AuditLog(db.Model):
    """Registro de Auditoria - Rastreia todas as ações do sistema"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    usuario_nome = db.Column(db.String(200), nullable=True)
    
    # Ação realizada
    acao = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    tabela = db.Column(db.String(100), nullable=False)
    registro_id = db.Column(db.Integer, nullable=True)
    
    # Dados anteriores e novos
    dados_anterior = db.Column(db.JSON, nullable=True)
    dados_novo = db.Column(db.JSON, nullable=True)
    
    # Informações técnicas
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Status
    sucesso = db.Column(db.Boolean, default=True)
    mensagem_erro = db.Column(db.Text, nullable=True)
    
    # Data/hora
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamento
    usuario = db.relationship('User', backref='audit_logs')

    ACAO_LABELS = {
        'CREATE': ('Criado', 'verde'),
        'UPDATE': ('Atualizado', 'azul'),
        'DELETE': ('Deletado', 'vermelho'),
        'VIEW': ('Visualizado', 'cinza'),
    }

    @property
    def acao_label(self):
        """Retorna label e cor da ação"""
        return self.ACAO_LABELS.get(self.acao, (self.acao, 'cinza'))

    def __repr__(self):
        return f'<AuditLog {self.acao} {self.tabela}({self.registro_id})>'