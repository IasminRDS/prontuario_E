# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.predicao import Predicao
from models.kpi import KPI
from models.unidade import Unidade
from database.db import db
from datetime import date, timedelta
import statistics

api_predicoes_bp = Blueprint('api_predicoes', __name__, url_prefix='/api/predicoes')

def regressao_linear(valores):
    """Regressão linear simples"""
    if len(valores) < 2:
        return valores[-1] if valores else 0
    
    n = len(valores)
    x = list(range(n))
    y = valores
    
    x_media = statistics.mean(x)
    y_media = statistics.mean(y)
    
    numerador = sum((x[i] - x_media) * (y[i] - y_media) for i in range(n))
    denominador = sum((x[i] - x_media) ** 2 for i in range(n))
    
    if denominador == 0:
        return y_media
    
    inclinacao = numerador / denominador
    intercepto = y_media - inclinacao * x_media
    
    # Predição para próximo dia (x = n)
    return intercepto + inclinacao * n

def media_movel(valores, periodo=7):
    """Média móvel simples"""
    if len(valores) < periodo:
        return statistics.mean(valores)
    return statistics.mean(valores[-periodo:])

@api_predicoes_bp.route('/ocupacao/<int:unidade_id>')
@login_required
def predicao_ocupacao(unidade_id):
    """Prediz taxa de ocupação para próximos 7 dias"""
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    # Pegar últimos 30 dias
    data_inicio = date.today() - timedelta(days=30)
    kpis = KPI.query.filter(
        KPI.unidade_id == unidade_id,
        KPI.data >= data_inicio
    ).order_by(KPI.data).all()
    
    if not kpis or len(kpis) < 5:
        return jsonify({'erro': 'Dados insuficientes'}), 400
    
    ocupacoes = [k.taxa_ocupacao for k in kpis]
    
    predicoes = []
    for i in range(1, 8):  # Próximos 7 dias
        valor = regressao_linear(ocupacoes)
        data_pred = date.today() + timedelta(days=i)
        
        pred = Predicao(
            unidade_id=unidade_id,
            tipo='ocupacao',
            data_predicao=data_pred,
            valor_predito=valor,
        )
        predicoes.append(pred.to_dict())
    
    return jsonify({
        'unidade_id': unidade_id,
        'tipo': 'ocupacao',
        'predicoes': predicoes,
        'metodo': 'regressão linear + média móvel'
    })

@api_predicoes_bp.route('/atendimentos/<int:unidade_id>')
@login_required
def predicao_atendimentos(unidade_id):
    """Prediz atendimentos para próximos 7 dias"""
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    data_inicio = date.today() - timedelta(days=30)
    kpis = KPI.query.filter(
        KPI.unidade_id == unidade_id,
        KPI.data >= data_inicio
    ).order_by(KPI.data).all()
    
    if not kpis or len(kpis) < 5:
        return jsonify({'erro': 'Dados insuficientes'}), 400
    
    atendimentos = [k.atendimentos for k in kpis]
    
    predicoes = []
    for i in range(1, 8):
        valor = regressao_linear(atendimentos)
        data_pred = date.today() + timedelta(days=i)
        
        predicoes.append({
            'data': str(data_pred),
            'valor_predito': round(valor),
            'margem_erro': round(valor * 0.15),  # Margem de 15%
        })
    
    return jsonify({
        'unidade_id': unidade_id,
        'tipo': 'atendimentos',
        'predicoes': predicoes,
        'metodo': 'regressão linear'
    })

@api_predicoes_bp.route('/calcular-todas', methods=['POST'])
@login_required
def calcular_todas():
    """Calcula todas as predições (executada diariamente)"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    unidades = Unidade.query.filter_by(ativo=True).all()
    
    for u in unidades:
        try:
            # Ocupação
            data_inicio = date.today() - timedelta(days=30)
            kpis = KPI.query.filter(
                KPI.unidade_id == u.id,
                KPI.data >= data_inicio
            ).order_by(KPI.data).all()
            
            if len(kpis) >= 5:
                ocupacoes = [k.taxa_ocupacao for k in kpis]
                valor_pred = regressao_linear(ocupacoes)
                
                pred = Predicao(
                    unidade_id=u.id,
                    tipo='ocupacao',
                    data_predicao=date.today() + timedelta(days=1),
                    valor_predito=valor_pred,
                )
                db.session.add(pred)
                
                # Atendimentos
                atendimentos = [k.atendimentos for k in kpis]
                valor_pred_atend = regressao_linear(atendimentos)
                
                pred_atend = Predicao(
                    unidade_id=u.id,
                    tipo='atendimentos',
                    data_predicao=date.today() + timedelta(days=1),
                    valor_predito=valor_pred_atend,
                )
                db.session.add(pred_atend)
        except Exception as e:
            print(f"Erro calculando predições para {u.nome}: {str(e)}")
    
    db.session.commit()
    return jsonify({'status': 'Predições calculadas com sucesso'})