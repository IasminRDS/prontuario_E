# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.alerta import Alerta, ConfiguradorAlerta
from models.unidade import Unidade
from models.internacao import Leito
from database.db import db
from datetime import datetime, timedelta

api_alertas_bp = Blueprint('api_alertas', __name__, url_prefix='/api/alertas')

@api_alertas_bp.route('/unidade/<int:unidade_id>')
@login_required
def alertas_unidade(unidade_id):
    """Lista alertas da unidade"""
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    horas = request.args.get('horas', 24, type=int)
    limite = datetime.now() - timedelta(hours=horas)
    
    alertas = Alerta.query.filter(
        Alerta.unidade_id == unidade_id,
        Alerta.timestamp >= limite
    ).order_by(Alerta.timestamp.desc()).all()
    
    criticos = sum(1 for a in alertas if a.nivel == 2)
    avisos = sum(1 for a in alertas if a.nivel == 1)
    
    return jsonify({
        'unidade_id': unidade_id,
        'total': len(alertas),
        'criticos': criticos,
        'avisos': avisos,
        'alertas': [a.to_dict() for a in alertas],
    })

@api_alertas_bp.route('/criar', methods=['POST'])
@login_required
def criar_alerta():
    """Cria novo alerta (interno ou via API)"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    dados = request.get_json()
    
    alerta = Alerta(
        unidade_id=dados['unidade_id'],
        tipo=dados['tipo'],
        nivel=dados['nivel'],
        titulo=dados['titulo'],
        mensagem=dados.get('mensagem'),
        dados_json=dados.get('dados'),
    )
    db.session.add(alerta)
    db.session.commit()
    
    return jsonify(alerta.to_dict()), 201

@api_alertas_bp.route('/verificar-criticos')
@login_required
def verificar_criticos():
    """Verifica se há alertas críticos"""
    if not current_user.pode_ver_estadual():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    criticos = Alerta.query.filter(
        Alerta.nivel == 2,
        Alerta.lido == False,
        Alerta.timestamp >= datetime.now() - timedelta(hours=1)
    ).count()
    
    return jsonify({'criticos': criticos})

@api_alertas_bp.route('/marcar-lido/<int:alerta_id>', methods=['POST'])
@login_required
def marcar_lido(alerta_id):
    """Marca alerta como lido"""
    alerta = Alerta.query.get_or_404(alerta_id)
    
    if not current_user.pode_ver_unidade(alerta.unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    alerta.lido = True
    db.session.commit()
    
    return jsonify({'status': 'Alerta marcado como lido'})

def gerar_alertas_automaticos():
    """Função chamada a cada hora para gerar alertas"""
    unidades = Unidade.query.filter_by(ativo=True).all()
    
    for u in unidades:
        config = ConfiguradorAlerta.query.filter_by(unidade_id=u.id, ativo=True).all()
        
        for cfg in config:
            if cfg.tipo == 'ocupacao':
                total_leitos = Leito.query.filter_by(ativo=True).count()
                leitos_ocu = Leito.query.filter_by(ativo=True, status='ocupado').count()
                taxa = (leitos_ocu / total_leitos * 100) if total_leitos else 0
                
                if taxa >= cfg.limiar_maximo:
                    # Verificar se já existe alerta crítico recente
                    alerta_recente = Alerta.query.filter(
                        Alerta.unidade_id == u.id,
                        Alerta.tipo == 'ocupacao',
                        Alerta.nivel == 2,
                        Alerta.timestamp >= datetime.now() - timedelta(hours=1)
                    ).first()
                    
                    if not alerta_recente:
                        alerta = Alerta(
                            unidade_id=u.id,
                            tipo='ocupacao',
                            nivel=2,
                            titulo=f'⚠️ CRÍTICO: Ocupação em {taxa:.0f}%',
                            mensagem=f'{leitos_ocu} de {total_leitos} leitos ocupados',
                            dados_json={'taxa': taxa, 'leitos': leitos_ocu, 'total': total_leitos}
                        )
                        db.session.add(alerta)
                
                elif taxa >= cfg.limiar_minimo:
                    alerta_recente = Alerta.query.filter(
                        Alerta.unidade_id == u.id,
                        Alerta.tipo == 'ocupacao',
                        Alerta.nivel == 1,
                        Alerta.timestamp >= datetime.now() - timedelta(hours=1)
                    ).first()
                    
                    if not alerta_recente:
                        alerta = Alerta(
                            unidade_id=u.id,
                            tipo='ocupacao',
                            nivel=1,
                            titulo=f'ℹ️ Ocupação em {taxa:.0f}%',
                            mensagem=f'{leitos_ocu} de {total_leitos} leitos ocupados',
                        )
                        db.session.add(alerta)
    
    db.session.commit()