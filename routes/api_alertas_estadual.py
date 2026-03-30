# -*- coding: utf-8 -*-
"""
Sistema de Alertas Inteligente para Nível Estadual
Detecta anomalias e situações críticas
"""

from flask import Blueprint, jsonify
from models import *
from datetime import datetime, timedelta
from sqlalchemy import func
import numpy as np

alertas_bp = Blueprint('alertas_estado', __name__, 
                       url_prefix='/api/alertas/estado')

@alertas_bp.route('/criticos')
def alertas_criticos():
    """Retorna alertas críticos que requerem ação imediata"""
    
    alertas = []
    
    # 1. SUPERLOTAÇÃO DE UTI
    taxa_uti = db.session.query(
        func.count(Internacao.id)
    ).filter(
        Internacao.tipo_leito == 'UTI',
        Internacao.data_saida.is_(None)
    ).scalar() or 0
    
    capacidade_uti = db.session.query(
        func.count(Vaga.id)
    ).filter(
        Vaga.especialidade == 'UTI'
    ).scalar() or 1
    
    taxa_ocupacao_uti = (taxa_uti / capacidade_uti * 100)
    if taxa_ocupacao_uti > 90:
        alertas.append({
            'severidade': 'CRÍTICO',
            'tipo': 'SUPERLOTAÇÃO_UTI',
            'mensagem': f'UTI com {taxa_ocupacao_uti:.1f}% de ocupação',
            'acao_recomendada': 'Ativar plano de contingência',
            'timestamp': datetime.now().isoformat()
        })
    
    # 2. PACIENTES EM RISCO
    pacientes_risco = db.session.query(
        Paciente.id,
        Paciente.nome,
        Triagem.pressao_sistolica,
        Triagem.frequencia_cardiaca
    ).join(Triagem).filter(
        or_(
            Triagem.pressao_sistolica > 180,
            Triagem.frequencia_cardiaca > 120
        )
    ).all()
    
    for p in pacientes_risco:
        alertas.append({
            'severidade': 'ALTO',
            'tipo': 'PACIENTE_RISCO',
            'paciente_id': p[0],
            'paciente_nome': p[1],
            'mensagem': f'Paciente {p[1]} com sinais vitais anormais',
            'timestamp': datetime.now().isoformat()
        })
    
    # 3. SURTO DE DOENÇA INFECCIOSA
    diagnosticos_ultimo_mes = db.session.query(
        Consulta.diagnostico_principal,
        func.count(Consulta.id).label('quantidade')
    ).filter(
        Consulta.data_consulta >= datetime.now() - timedelta(days=30)
    ).group_by(Consulta.diagnostico_principal).having(
        func.count(Consulta.id) > 10
    ).all()
    
    doencas_notificaveis = ['COVID-19', 'Dengue', 'Zika', 'Influenza']
    for diag in diagnosticos_ultimo_mes:
        if any(d in diag[0] for d in doencas_notificaveis):
            alertas.append({
                'severidade': 'CRÍTICO',
                'tipo': 'POSSÍVEL_SURTO',
                'doenca': diag[0],
                'casos': diag[1],
                'mensagem': f'Aumento de casos de {diag[0]}: {diag[1]} em 30 dias',
                'acao_recomendada': 'Notificar vigilância epidemiológica',
                'timestamp': datetime.now().isoformat()
            })
    
    # 4. VAGAS CRÍTICAS
    vagas_baixas = db.session.query(
        Vaga.especialidade,
        func.count(Vaga.id).label('total'),
        func.sum(case([
            (Vaga.ocupada == False, 1)
        ], else_=0)).label('disponiveis')
    ).group_by(Vaga.especialidade).having(
        func.sum(case([
            (Vaga.ocupada == False, 1)
        ], else_=0)) < 5
    ).all()
    
    for vaga in vagas_baixas:
        alertas.append({
            'severidade': 'MÉDIO',
            'tipo': 'VAGAS_BAIXAS',
            'especialidade': vaga[0],
            'vagas_disponiveis': vaga[2],
            'mensagem': f'Apenas {vaga[2]} vagas disponíveis em {vaga[0]}',
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({
        'total_alertas': len(alertas),
        'criticos': len([a for a in alertas if a['severidade'] == 'CRÍTICO']),
        'altos': len([a for a in alertas if a['severidade'] == 'ALTO']),
        'alertas': alertas
    })

@alertas_bp.route('/previsoes')
def alertas_previsoes():
    """Previsões baseadas em IA/ML para alertas futuros"""
    
    previsoes = []
    
    # Análise de tendência: Demanda crescente?
    consultas_por_semana = db.session.query(
        func.week(Consulta.data_consulta),
        func.count(Consulta.id)
    ).filter(
        Consulta.data_consulta >= datetime.now() - timedelta(days=60)
    ).group_by(func.week(Consulta.data_consulta)).order_by(
        func.week(Consulta.data_consulta)
    ).all()
    
    if len(consultas_por_semana) >= 2:
        valores = [c[1] for c in consultas_por_semana]
        tendencia = (valores[-1] - valores[0]) / valores[0] * 100
        
        if tendencia > 20:
            previsoes.append({
                'tipo': 'DEMANDA_CRESCENTE',
                'probabilidade': min(tendencia / 100, 1.0),
                'mensagem': f'Demanda crescendo {tendencia:.1f}% em 60 dias',
                'recomendacao': 'Preparar mais profissionais e recursos'
            })
    
    return jsonify({
        'previsoes': previsoes
    })