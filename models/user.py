# -*- coding: utf-8 -*-
"""
Model de Usuário do Sistema
"""
from database.db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """Modelo de usuário do sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=True)
    perfil = db.Column(db.String(50), default='usuario')  # admin, medico, enfermeiro, gestor_estadual, etc
    senha_hash = db.Column(db.String(255), nullable=False)
    
    # Foreign key para unidade
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=True)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    unidade = db.relationship('Unidade', backref='usuarios')
    
    # ========== MÉTODOS DE AUTENTICAÇÃO ==========
    
    def set_password(self, senha):
        """Define a senha com hash seguro"""
        self.senha_hash = generate_password_hash(senha)
    
    def check_password(self, senha):
        """Verifica se a senha está correta"""
        return check_password_hash(self.senha_hash, senha)
    
    def set_ultimo_acesso(self):
        """Atualiza data/hora do último acesso"""
        self.ultimo_acesso = datetime.utcnow()
        db.session.commit()
    
    # ========== MÉTODOS DE PERMISSÃO ==========
    
    def is_admin(self):
        """Verifica se é administrador"""
        return self.perfil == 'admin'
    
    def is_medico(self):
        """Verifica se é médico"""
        return self.perfil == 'medico'
    
    def is_enfermeiro(self):
        """Verifica se é enfermeiro"""
        return self.perfil == 'enfermeiro'
    
    def is_gestor_estadual(self):
        """Verifica se é gestor estadual"""
        return self.perfil == 'gestor_estadual'
    
    def is_gestor_unidade(self):
        """Verifica se é gestor de unidade"""
        return self.perfil == 'gestor_unidade'
    
    def is_recepcionista(self):
        """Verifica se é recepcionista"""
        return self.perfil == 'recepcionista'
    
    def is_gestor_financeiro(self):
        """Verifica se é gestor financeiro"""
        return self.perfil == 'gestor_financeiro'
    
    def pode_ver_unidade(self, unidade_id):
        """Verifica se pode acessar uma unidade"""
        if self.is_admin() or self.is_gestor_estadual():
            return True
        if self.unidade_id == int(unidade_id):
            return True
        return False
    
    def pode_ver_estadual(self):
        """Verifica se pode ver dados estaduais"""
        return self.is_admin() or self.is_gestor_estadual()
    
    def tem_permissao(self, nome_permissao):
        """Verifica se tem uma permissão específica"""
        # Mapeamento simples de perfis a permissões
        permissoes_por_perfil = {
            'admin': [
                'paciente_criar', 'paciente_ler', 'paciente_editar', 'paciente_deletar',
                'atendimento_criar', 'atendimento_ler', 'atendimento_editar',
                'prontuario_ler', 'prontuario_editar', 'prontuario_exportar',
                'relatorio_ler', 'relatorio_exportar', 'relatorio_estadual',
                'financeiro_ler', 'financeiro_editar',
                'admin_usuarios', 'admin_permissoes', 'admin_unidades', 'admin_backup',
                'vaga_visualizar', 'vaga_gerenciar',
                'transferencia_solicitar', 'transferencia_aceitar', 'transferencia_recusar'
            ],
            'gestor_estadual': [
                'paciente_ler', 'prontuario_ler', 'atendimento_ler',
                'vaga_visualizar', 'relatorio_estadual',
                'relatorio_ler', 'relatorio_exportar',
                'transferencia_solicitar', 'financeiro_ler'
            ],
            'gestor_unidade': [
                'paciente_criar', 'paciente_ler', 'paciente_editar',
                'prontuario_ler', 'prontuario_editar',
                'atendimento_criar', 'atendimento_ler', 'atendimento_editar',
                'vaga_visualizar', 'vaga_gerenciar',
                'transferencia_solicitar', 'transferencia_aceitar',
                'relatorio_ler', 'relatorio_exportar',
                'financeiro_ler', 'financeiro_editar'
            ],
            'medico': [
                'paciente_ler', 'prontuario_ler', 'prontuario_editar',
                'atendimento_criar', 'atendimento_ler', 'atendimento_editar',
                'vaga_visualizar', 'relatorio_ler',
                'transferencia_solicitar'
            ],
            'enfermeiro': [
                'paciente_ler', 'prontuario_ler', 'prontuario_editar',
                'atendimento_ler', 'atendimento_editar',
                'vaga_visualizar', 'relatorio_ler'
            ],
            'recepcionista': [
                'paciente_ler', 'paciente_criar',
                'prontuario_ler',
                'atendimento_ler',
                'vaga_visualizar'
            ],
            'gestor_financeiro': [
                'paciente_ler',
                'atendimento_ler',
                'relatorio_ler',
                'relatorio_exportar',
                'financeiro_ler',
                'financeiro_editar'
            ]
        }
        
        perms = permissoes_por_perfil.get(self.perfil, [])
        return nome_permissao in perms
    
    def pode_editar_paciente(self, paciente_id):
        """Verifica se pode editar dados de um paciente"""
        if self.is_admin() or self.is_gestor_estadual():
            return True
        if self.is_gestor_unidade() or self.is_medico() or self.is_enfermeiro():
            return self.pode_ver_unidade(self.unidade_id)
        return False
    
    def pode_ver_financeiro(self):
        """Verifica se pode ver dados financeiros"""
        return self.is_admin() or self.is_gestor_estadual() or self.is_gestor_financeiro()
    
    def pode_editar_financeiro(self):
        """Verifica se pode editar dados financeiros"""
        return self.is_admin() or self.is_gestor_financeiro()
    
    def pode_gerenciar_vagas(self):
        """Verifica se pode gerenciar vagas"""
        return self.is_admin() or self.is_gestor_estadual() or self.is_gestor_unidade()
    
    def pode_aceitar_transferencia(self):
        """Verifica se pode aceitar transferências"""
        return self.is_admin() or self.is_gestor_estadual() or self.is_gestor_unidade()
    
    # ========== MÉTODOS DE VALIDAÇÃO ==========
    
    def validar_cpf(self):
        """Valida CPF (básico)"""
        if not self.cpf:
            return True
        
        # Remove caracteres especiais
        cpf = self.cpf.replace('.', '').replace('-', '')
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        return True
    
    def validar_email(self):
        """Valida e-mail"""
        if not self.email:
            return False
        
        return '@' in self.email and '.' in self.email.split('@')[1]
    
    # ========== MÉTODOS DE REPRESENTAÇÃO ==========
    
    def __repr__(self):
        return f'<User {self.nome} ({self.perfil})>'
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'cpf': self.cpf,
            'perfil': self.perfil,
            'unidade_id': self.unidade_id,
            'unidade': self.unidade.nome if self.unidade else None,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
        }
    
    def to_dict_completo(self):
        """Retorna dados completos do usuário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'cpf': self.cpf,
            'perfil': self.perfil,
            'unidade_id': self.unidade_id,
            'unidade': {
                'id': self.unidade.id,
                'nome': self.unidade.nome,
                'cnes': self.unidade.cnes,
                'municipio': self.unidade.municipio,
                'uf': self.unidade.uf
            } if self.unidade else None,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            'permissoes': {
                'is_admin': self.is_admin(),
                'is_medico': self.is_medico(),
                'is_enfermeiro': self.is_enfermeiro(),
                'is_gestor_estadual': self.is_gestor_estadual(),
                'is_gestor_unidade': self.is_gestor_unidade(),
                'pode_ver_estadual': self.pode_ver_estadual(),
                'pode_ver_financeiro': self.pode_ver_financeiro(),
                'pode_editar_financeiro': self.pode_editar_financeiro(),
                'pode_gerenciar_vagas': self.pode_gerenciar_vagas(),
            }
        }