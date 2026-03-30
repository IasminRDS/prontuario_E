# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.permissao import Permissao, Role, AcessoEstadual, TipoAcesso
from models.user import User
from models.unidade import Unidade
from database.db import db
from datetime import datetime

api_permissoes_bp = Blueprint('api_permissoes', __name__, url_prefix='/api/permissoes')

# ========== ROLES ==========

@api_permissoes_bp.route('/roles', methods=['GET'])
@login_required
def listar_roles():
    """Lista todas as roles"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    roles = Role.query.all()
    return jsonify([r.to_dict() for r in roles])

@api_permissoes_bp.route('/roles', methods=['POST'])
@login_required
def criar_role():
    """Cria nova role"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    dados = request.get_json()
    
    # Verificar se já existe
    if Role.query.filter_by(nome=dados['nome']).first():
        return jsonify({'erro': 'Role já existe'}), 400
    
    role = Role(
        nome=dados['nome'],
        descricao=dados.get('descricao'),
        tipo_acesso=dados.get('tipo_acesso', 'unidade')
    )
    db.session.add(role)
    db.session.commit()
    
    return jsonify(role.to_dict()), 201

@api_permissoes_bp.route('/roles/<int:role_id>/permissoes', methods=['POST'])
@login_required
def adicionar_permissao_role(role_id):
    """Adiciona permissão à role"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    role = Role.query.get_or_404(role_id)
    dados = request.get_json()
    
    permissao = Permissao.query.get_or_404(dados['permissao_id'])
    
    if not role.tem_permissao(permissao.nome):
        role.adicionar_permissao(permissao)
        db.session.commit()
    
    return jsonify(role.to_dict()), 200

@api_permissoes_bp.route('/roles/<int:role_id>/permissoes/<int:perm_id>', methods=['DELETE'])
@login_required
def remover_permissao_role(role_id, perm_id):
    """Remove permissão da role"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    role = Role.query.get_or_404(role_id)
    permissao = Permissao.query.get_or_404(perm_id)
    
    role.remover_permissao(permissao)
    db.session.commit()
    
    return jsonify({'status': 'permissão removida'}), 200

# ========== PERMISSÕES ==========

@api_permissoes_bp.route('/list', methods=['GET'])
@login_required
def listar_permissoes():
    """Lista todas as permissões"""
    modulo = request.args.get('modulo')
    
    query = Permissao.query
    if modulo:
        query = query.filter_by(modulo=modulo)
    
    permissoes = query.all()
    return jsonify([p.to_dict() for p in permissoes])

# ========== ACESSO ESTADUAL ==========

@api_permissoes_bp.route('/acesso-estadual/<int:usuario_id>', methods=['GET'])
@login_required
def get_acesso_estadual(usuario_id):
    """Retorna acesso estadual do usuário"""
    if not current_user.is_admin() and current_user.id != usuario_id:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    acesso = AcessoEstadual.query.filter_by(usuario_id=usuario_id).first()
    
    if not acesso:
        return jsonify({'erro': 'Acesso não configurado'}), 404
    
    return jsonify(acesso.to_dict())

@api_permissoes_bp.route('/acesso-estadual', methods=['POST'])
@login_required
def criar_acesso_estadual():
    """Cria ou atualiza acesso estadual"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    dados = request.get_json()
    usuario_id = dados['usuario_id']
    
    usuario = User.query.get_or_404(usuario_id)
    
    acesso = AcessoEstadual.query.filter_by(usuario_id=usuario_id).first()
    
    if not acesso:
        acesso = AcessoEstadual(
            usuario_id=usuario_id,
            criado_por=current_user.id
        )
        db.session.add(acesso)
    
    acesso.estado = dados['estado']
    acesso.tipo_acesso = dados['tipo_acesso']
    acesso.regiao = dados.get('regiao')
    acesso.municipios = dados.get('municipios', [])
    acesso.unidades = dados.get('unidades', [])
    acesso.setores = dados.get('setores', {})
    acesso.ativo = dados.get('ativo', True)
    
    db.session.commit()
    
    return jsonify(acesso.to_dict()), 201

@api_permissoes_bp.route('/acesso-estadual/<int:usuario_id>', methods=['DELETE'])
@login_required
def inativar_acesso_estadual(usuario_id):
    """Inativa acesso estadual"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    acesso = AcessoEstadual.query.filter_by(usuario_id=usuario_id).first_or_404()
    
    acesso.ativo = False
    acesso.motivo_inativacao = request.get_json().get('motivo')
    acesso.data_fim = datetime.now()
    
    db.session.commit()
    
    return jsonify({'status': 'acesso inativado'})

# ========== UTILITÁRIOS ==========

@api_permissoes_bp.route('/estados', methods=['GET'])
@login_required
def listar_estados():
    """Lista todos os estados do Brasil"""
    estados = {
        'AC': 'Acre',
        'AL': 'Alagoas',
        'AP': 'Amapá',
        'AM': 'Amazonas',
        'BA': 'Bahia',
        'CE': 'Ceará',
        'DF': 'Distrito Federal',
        'ES': 'Espírito Santo',
        'GO': 'Goiás',
        'MA': 'Maranhão',
        'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais',
        'PA': 'Pará',
        'PB': 'Paraíba',
        'PR': 'Paraná',
        'PE': 'Pernambuco',
        'PI': 'Piauí',
        'RJ': 'Rio de Janeiro',
        'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul',
        'RO': 'Rondônia',
        'RR': 'Roraima',
        'SC': 'Santa Catarina',
        'SP': 'São Paulo',
        'SE': 'Sergipe',
        'TO': 'Tocantins',
    }
    return jsonify(estados)

@api_permissoes_bp.route('/tipos-acesso', methods=['GET'])
@login_required
def listar_tipos_acesso():
    """Lista tipos de acesso disponíveis"""
    tipos = {
        'nacional': 'Acesso Nacional (Ministério da Saúde)',
        'estadual': 'Acesso Estadual (Secretaria Estadual)',
        'regional': 'Acesso Regional (Coordenação Regional)',
        'municipal': 'Acesso Municipal (Secretaria Municipal)',
        'unidade': 'Acesso Unitário (Hospital/Clínica)',
        'profissional': 'Profissional de Saúde',
        'paciente': 'Paciente',
    }
    return jsonify(tipos)

@api_permissoes_bp.route('/meu-acesso', methods=['GET'])
@login_required
def meu_acesso():
    """Retorna acesso do usuário logado"""
    acesso = {
        'usuario_id': current_user.id,
        'nome': current_user.nome,
        'role': current_user.role.nome if current_user.role else None,
        'is_admin': current_user.is_admin(),
        'estados': current_user.get_estados_acesso(),
        'acesso_estadual': None
    }
    
    if current_user.acesso_estadual:
        acesso['acesso_estadual'] = current_user.acesso_estadual.to_dict()
    
    return jsonify(acesso)