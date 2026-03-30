# -*- coding: utf-8 -*-
"""
Seed de permissões e roles padrão do SUS
Popula o banco com estrutura de controle de acesso
"""

from models.permissao import Permissao, Role
from database.db import db

def seed_permissoes():
    """Popula banco com permissões padrão do SUS"""
    
    print("\n🔐 Carregando estrutura de permissões...\n")
    
    # ========== CRIAR PERMISSÕES ==========
    permissoes = [
        # Pacientes
        Permissao(nome='paciente_criar', descricao='Criar novo paciente', modulo='pacientes', acao='criar'),
        Permissao(nome='paciente_ler', descricao='Visualizar dados do paciente', modulo='pacientes', acao='ler'),
        Permissao(nome='paciente_editar', descricao='Editar dados do paciente', modulo='pacientes', acao='editar'),
        Permissao(nome='paciente_deletar', descricao='Deletar paciente', modulo='pacientes', acao='deletar'),
        
        # Prontuário
        Permissao(nome='prontuario_ler', descricao='Visualizar prontuário', modulo='prontuario', acao='ler'),
        Permissao(nome='prontuario_editar', descricao='Editar prontuário', modulo='prontuario', acao='editar'),
        Permissao(nome='prontuario_exportar', descricao='Exportar prontuário', modulo='prontuario', acao='exportar'),
        
        # Atendimento
        Permissao(nome='atendimento_criar', descricao='Registrar atendimento', modulo='atendimento', acao='criar'),
        Permissao(nome='atendimento_ler', descricao='Visualizar atendimento', modulo='atendimento', acao='ler'),
        Permissao(nome='atendimento_editar', descricao='Editar atendimento', modulo='atendimento', acao='editar'),
        
        # Internação
        Permissao(nome='internacao_criar', descricao='Registrar internação', modulo='internacao', acao='criar'),
        Permissao(nome='internacao_editar', descricao='Editar internação', modulo='internacao', acao='editar'),
        Permissao(nome='internacao_alta', descricao='Dar alta internação', modulo='internacao', acao='editar'),
        
        # Vagas
        Permissao(nome='vaga_visualizar', descricao='Visualizar vagas disponíveis', modulo='vagas', acao='ler'),
        Permissao(nome='vaga_reservar', descricao='Reservar vaga', modulo='vagas', acao='editar'),
        Permissao(nome='vaga_gerenciar', descricao='Gerenciar vagas', modulo='vagas', acao='editar'),
        
        # Transferências
        Permissao(nome='transferencia_solicitar', descricao='Solicitar transferência', modulo='transferencia', acao='criar'),
        Permissao(nome='transferencia_aceitar', descricao='Aceitar transferência', modulo='transferencia', acao='editar'),
        Permissao(nome='transferencia_recusar', descricao='Recusar transferência', modulo='transferencia', acao='editar'),
        
        # Relatórios
        Permissao(nome='relatorio_ler', descricao='Visualizar relatórios', modulo='relatorios', acao='ler'),
        Permissao(nome='relatorio_exportar', descricao='Exportar relatórios', modulo='relatorios', acao='exportar'),
        Permissao(nome='relatorio_estadual', descricao='Acessar relatórios estaduais', modulo='relatorios', acao='ler'),
        
        # Financeiro
        Permissao(nome='financeiro_ler', descricao='Visualizar dados financeiros', modulo='financeiro', acao='ler'),
        Permissao(nome='financeiro_editar', descricao='Editar dados financeiros', modulo='financeiro', acao='editar'),
        
        # Admin
        Permissao(nome='admin_usuarios', descricao='Gerenciar usuários', modulo='admin', acao='editar'),
        Permissao(nome='admin_permissoes', descricao='Gerenciar permissões', modulo='admin', acao='editar'),
        Permissao(nome='admin_unidades', descricao='Gerenciar unidades', modulo='admin', acao='editar'),
        Permissao(nome='admin_backup', descricao='Fazer backup', modulo='admin', acao='editar'),
    ]
    
    # Inserir permissões
    for perm in permissoes:
        if not Permissao.query.filter_by(nome=perm.nome).first():
            db.session.add(perm)
    
    db.session.commit()
    print(f"  ✓ {len(permissoes)} permissões criadas")
    
    # ========== CRIAR ROLES ==========
    roles_config = [
        {
            'nome': 'admin',
            'descricao': 'Administrador do sistema',
            'tipo': 'nacional',
            'permissoes': [p.nome for p in permissoes]  # Todas
        },
        {
            'nome': 'gestor_estadual',
            'descricao': 'Gestor Estadual de Saúde',
            'tipo': 'estadual',
            'permissoes': [
                'paciente_ler', 'prontuario_ler', 'atendimento_ler',
                'internacao_ler', 'vaga_visualizar', 'relatorio_estadual',
                'relatorio_ler', 'relatorio_exportar',
                'transferencia_solicitar', 'financeiro_ler'
            ]
        },
        {
            'nome': 'gestor_unidade',
            'descricao': 'Gestor de Unidade',
            'tipo': 'unidade',
            'permissoes': [
                'paciente_criar', 'paciente_ler', 'paciente_editar',
                'prontuario_ler', 'prontuario_editar',
                'atendimento_criar', 'atendimento_ler', 'atendimento_editar',
                'internacao_criar', 'internacao_editar', 'internacao_alta',
                'vaga_visualizar', 'vaga_gerenciar',
                'transferencia_solicitar', 'transferencia_aceitar',
                'relatorio_ler', 'relatorio_exportar',
                'financeiro_ler', 'financeiro_editar'
            ]
        },
        {
            'nome': 'medico',
            'descricao': 'Médico',
            'tipo': 'unidade',
            'permissoes': [
                'paciente_ler', 'prontuario_ler', 'prontuario_editar',
                'atendimento_criar', 'atendimento_ler', 'atendimento_editar',
                'internacao_ler', 'internacao_editar',
                'vaga_visualizar', 'relatorio_ler',
                'transferencia_solicitar'
            ]
        },
        {
            'nome': 'enfermeira',
            'descricao': 'Enfermeira',
            'tipo': 'unidade',
            'permissoes': [
                'paciente_ler', 'prontuario_ler', 'prontuario_editar',
                'atendimento_ler', 'atendimento_editar',
                'internacao_ler', 'internacao_editar',
                'vaga_visualizar', 'relatorio_ler'
            ]
        },
        {
            'nome': 'recepcionista',
            'descricao': 'Recepcionista',
            'tipo': 'unidade',
            'permissoes': [
                'paciente_ler', 'paciente_criar',
                'prontuario_ler',
                'atendimento_ler',
                'vaga_visualizar'
            ]
        },
        {
            'nome': 'gestor_financeiro',
            'descricao': 'Gestor Financeiro',
            'tipo': 'unidade',
            'permissoes': [
                'paciente_ler',
                'atendimento_ler',
                'internacao_ler',
                'relatorio_ler',
                'relatorio_exportar',
                'financeiro_ler',
                'financeiro_editar'
            ]
        },
    ]
    
    # Inserir roles
    for role_config in roles_config:
        if not Role.query.filter_by(nome=role_config['nome']).first():
            role = Role(
                nome=role_config['nome'],
                descricao=role_config['descricao'],
                tipo_acesso=role_config['tipo']
            )
            
            for perm_nome in role_config['permissoes']:
                perm = Permissao.query.filter_by(nome=perm_nome).first()
                if perm:
                    role.adicionar_permissao(perm)
            
            db.session.add(role)
    
    db.session.commit()
    print(f"  ✓ {len(roles_config)} roles criadas")
    
    print("\n✓ Estrutura de permissões carregada com sucesso!\n")