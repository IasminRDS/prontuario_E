# -*- coding: utf-8 -*-
"""
Analytics Avançado para Nível Estadual
Integração com BI e Data Warehouse
Conformidade com Ministério da Saúde
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from database.db import db
from models import (
    Paciente, UnidadeSaude, Consulta, Internacao, Agendamento,
    Triagem, Regulacao, Vaga, Transferencia, Alerta
)
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, distinct, case, desc
import json

# Blueprint
analytics_estadual_bp = Blueprint(
    'analytics_estadual',
    __name__,
    url_prefix='/api/analytics/estadual'
)

# ========== DECORADOR: Requer Permissão ==========
def requer_permissao(permissao):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            if not current_user.is_authenticated or not current_user.tem_permissao(permissao):
                return jsonify({'error': 'Acesso negado'}), 403
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# ========== ROTAS DE ANALYTICS ==========

@analytics_estadual_bp.route('/indicadores-saude')
@login_required
@requer_permissao('ver_analytics')
def indicadores_saude():
    """
    Indicadores de Saúde Pública conforme Ministério da Saúde
    Taxa de cobertura, reinternação, eficiência
    """
    try:
        periodo_dias = request.args.get('dias', 30, type=int)
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        # 1. Taxa de cobertura por região
        cobertura = db.session.query(
            UnidadeSaude.regiao,
            func.count(distinct(Paciente.id)).label('pacientes'),
            func.count(Consulta.id).label('consultas'),
            func.count(distinct(Agendamento.id)).label('agendamentos'),
            (func.count(Consulta.id) / func.count(distinct(Paciente.id))).label('consultas_por_paciente')
        ).join(Paciente).join(Consulta).outerjoin(Agendamento).filter(
            and_(
                Consulta.data_consulta >= data_inicio,
                UnidadeSaude.regiao.isnot(None)
            )
        ).group_by(UnidadeSaude.regiao).all()
        
        # 2. Taxa de reinternação (pacientes com mais de 1 internação em período)
        reinternacoes_query = db.session.query(
            Paciente.id,
            func.count(Internacao.id).label('vezes_internado')
        ).join(Internacao).filter(
            Internacao.data_admissao >= data_inicio
        ).group_by(Paciente.id).all()
        
        reinternados = len([r for r in reinternacoes_query if r[1] > 1])
        total_internacoes = sum([r[1] for r in reinternacoes_query])
        taxa_reinternacao = (reinternados / len(reinternacoes_query) * 100) if reinternacoes_query else 0
        
        # 3. Tempo médio de permanência por especialidade
        tempo_permanencia = db.session.query(
            Internacao.especialidade,
            func.avg(
                func.datediff(Internacao.data_saida, Internacao.data_admissao)
            ).label('dias_medio'),
            func.count(Internacao.id).label('total_internacoes')
        ).filter(
            and_(
                Internacao.data_saida.isnot(None),
                Internacao.data_admissao >= data_inicio
            )
        ).group_by(Internacao.especialidade).order_by(
            func.avg(
                func.datediff(Internacao.data_saida, Internacao.data_admissao)
            ).desc()
        ).all()
        
        # 4. Taxa de abandono de tratamento
        agendamentos = db.session.query(
            func.count(Agendamento.id).label('total'),
            func.sum(case([(Agendamento.status == 'faltou', 1)])).label('faltas'),
            func.sum(case([(Agendamento.status == 'cancelada', 1)])).label('canceladas')
        ).filter(
            Agendamento.data_agendamento >= data_inicio
        ).first()
        
        taxa_falta = (agendamentos[1] / agendamentos[0] * 100) if agendamentos[0] > 0 else 0
        taxa_cancelamento = (agendamentos[2] / agendamentos[0] * 100) if agendamentos[0] > 0 else 0
        
        return jsonify({
            'status': 'success',
            'periodo': {
                'dias': periodo_dias,
                'data_inicio': data_inicio.isoformat(),
                'data_fim': datetime.now().isoformat()
            },
            'cobertura_por_regiao': [
                {
                    'regiao': r[0] or 'Sem Região',
                    'pacientes': r[1],
                    'consultas': r[2],
                    'agendamentos': r[3],
                    'consultas_por_paciente': float(r[4]) if r[4] else 0
                } for r in cobertura
            ],
            'reinternacao': {
                'taxa_percentual': round(taxa_reinternacao, 2),
                'pacientes_reinternados': reinternados,
                'total_internacoes': total_internacoes
            },
            'tempo_permanencia': [
                {
                    'especialidade': t[0] or 'Não especificada',
                    'dias_medio': round(float(t[1]), 2) if t[1] else 0,
                    'total_internacoes': t[2]
                } for t in tempo_permanencia
            ],
            'abandono': {
                'taxa_falta_percentual': round(taxa_falta, 2),
                'taxa_cancelamento_percentual': round(taxa_cancelamento, 2),
                'total_agendamentos': agendamentos[0]
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro em indicadores_saude: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_estadual_bp.route('/matriz-regulacao')
@login_required
@requer_permissao('ver_analytics')
def matriz_regulacao():
    """
    Matriz de Regulação - Integração Estadual
    Mostra oferta x demanda de leitos
    """
    try:
        # Demanda por especialidade e região
        demanda = db.session.query(
            Regulacao.especialidade,
            UnidadeSaude.regiao,
            func.count(Regulacao.id).label('solicitacoes'),
            func.sum(case([(Regulacao.status == 'aprovada', 1)])).label('aprovadas'),
            func.sum(case([(Regulacao.status == 'recusada', 1)])).label('recusadas'),
            func.sum(case([(Regulacao.status == 'pendente', 1)])).label('pendentes'),
            func.avg(Regulacao.prioridade).label('prioridade_media')
        ).join(UnidadeSaude).group_by(
            Regulacao.especialidade, UnidadeSaude.regiao
        ).all()
        
        # Oferta de leitos por especialidade e região
        oferta = db.session.query(
            Vaga.especialidade,
            UnidadeSaude.regiao,
            func.count(Vaga.id).label('total_vagas'),
            func.sum(case([(Vaga.ocupada == False, 1)])).label('vagas_disponiveis'),
            func.sum(case([(Vaga.ativa == False, 1)])).label('vagas_inativas'),
            (func.sum(case([(Vaga.ocupada == False, 1)])) / func.count(Vaga.id) * 100).label('taxa_disponibilidade')
        ).join(UnidadeSaude).group_by(
            Vaga.especialidade, UnidadeSaude.regiao
        ).all()
        
        # Tempo médio de resposta de regulações
        tempo_resposta = db.session.query(
            Regulacao.especialidade,
            func.avg(
                func.timestampdiff('MINUTE', Regulacao.data_solicitacao, Regulacao.data_resposta)
            ).label('tempo_medio_min'),
            func.min(
                func.timestampdiff('MINUTE', Regulacao.data_solicitacao, Regulacao.data_resposta)
            ).label('tempo_minimo_min'),
            func.max(
                func.timestampdiff('MINUTE', Regulacao.data_solicitacao, Regulacao.data_resposta)
            ).label('tempo_maximo_min')
        ).filter(
            Regulacao.data_resposta.isnot(None)
        ).group_by(Regulacao.especialidade).all()
        
        return jsonify({
            'status': 'success',
            'demanda': [
                {
                    'especialidade': d[0] or 'Não especificada',
                    'regiao': d[1] or 'Sem região',
                    'solicitacoes': d[2],
                    'aprovadas': d[3] or 0,
                    'recusadas': d[4] or 0,
                    'pendentes': d[5] or 0,
                    'prioridade_media': float(d[6]) if d[6] else 0,
                    'taxa_aprovacao': round((d[3] or 0) / d[2] * 100, 2) if d[2] > 0 else 0
                } for d in demanda
            ],
            'oferta': [
                {
                    'especialidade': o[0] or 'Não especificada',
                    'regiao': o[1] or 'Sem região',
                    'total_vagas': o[2],
                    'vagas_disponiveis': o[3] or 0,
                    'vagas_inativas': o[4] or 0,
                    'taxa_disponibilidade': round(float(o[5]), 2) if o[5] else 0
                } for o in oferta
            ],
            'tempo_resposta': [
                {
                    'especialidade': t[0] or 'Não especificada',
                    'tempo_medio_minutos': int(t[1]) if t[1] else 0,
                    'tempo_minimo_minutos': int(t[2]) if t[2] else 0,
                    'tempo_maximo_minutos': int(t[3]) if t[3] else 0
                } for t in tempo_resposta
            ]
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro em matriz_regulacao: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_estadual_bp.route('/eficiencia-operacional')
@login_required
@requer_permissao('ver_analytics')
def eficiencia_operacional():
    """
    Métricas de eficiência operacional por unidade
    Desempenho comparativo
    """
    try:
        # Eficiência por unidade
        eficiencia = db.session.query(
            UnidadeSaude.id,
            UnidadeSaude.nome,
            UnidadeSaude.regiao,
            func.count(distinct(Consulta.paciente_id)).label('pacientes_atendidos'),
            func.count(Consulta.id).label('total_consultas'),
            func.avg(
                func.timestampdiff('MINUTE', Consulta.data_entrada, Consulta.data_saida)
            ).label('tempo_medio_consulta'),
            func.count(distinct(Agendamento.id)).label('agendamentos'),
            func.sum(case([(Agendamento.status == 'faltou', 1)])).label('faltas'),
            func.count(distinct(Internacao.paciente_id)).label('pacientes_internados'),
            func.avg(func.datediff(Internacao.data_saida, Internacao.data_admissao)).label('tempo_medio_internacao')
        ).join(Consulta, isouter=True).join(
            Agendamento, isouter=True
        ).join(Internacao, isouter=True).group_by(UnidadeSaude.id).all()
        
        resultado = []
        for e in eficiencia:
            taxa_falta = (e[7] / e[6] * 100) if e[6] > 0 else 0
            produtividade = (e[4] / e[3]) if e[3] > 0 else 0
            
            resultado.append({
                'unidade_id': e[0],
                'nome': e[1],
                'regiao': e[2],
                'pacientes_atendidos': e[3],
                'total_consultas': e[4],
                'tempo_medio_consulta_min': int(e[5]) if e[5] else 0,
                'agendamentos': e[6],
                'taxa_falta_percentual': round(taxa_falta, 2),
                'pacientes_internados': e[8],
                'tempo_medio_internacao_dias': round(float(e[9]), 2) if e[9] else 0,
                'produtividade_consultas_por_paciente': round(produtividade, 2)
            })
        
        return jsonify({
            'status': 'success',
            'unidades': sorted(resultado, key=lambda x: x['total_consultas'], reverse=True),
            'media_taxa_falta': round(sum([x['taxa_falta_percentual'] for x in resultado]) / len(resultado), 2) if resultado else 0,
            'media_tempo_consulta': round(sum([x['tempo_medio_consulta_min'] for x in resultado]) / len(resultado), 2) if resultado else 0
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro em eficiencia_operacional: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_estadual_bp.route('/transferencias-estaduais')
@login_required
@requer_permissao('ver_analytics')
def transferencias_estaduais():
    """
    Análise de transferências entre regiões
    Fluxo de pacientes
    """
    try:
        # Fluxo de transferências
        fluxos = db.session.query(
            UnidadeSaude.regiao.label('regiao_origem'),
            UnidadeSaude.regiao.label('regiao_destino'),
            func.count(Transferencia.id).label('total'),
            func.sum(case([(Transferencia.status == 'recebida', 1)])).label('concluidas'),
            func.avg(
                func.timestampdiff('MINUTE', Transferencia.data_solicitacao, Transferencia.data_chegada)
            ).label('tempo_medio_min')
        ).join(
            UnidadeSaude, UnidadeSaude.id == Transferencia.unidade_origem_id
        ).group_by(
            UnidadeSaude.regiao
        ).all()
        
        # Motivos de transferência
        motivos = db.session.query(
            func.substr(Transferencia.motivo, 1, 50).label('motivo'),
            func.count(Transferencia.id).label('total')
        ).group_by(
            func.substr(Transferencia.motivo, 1, 50)
        ).order_by(
            func.count(Transferencia.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'status': 'success',
            'fluxos': [
                {
                    'origem': f[0] or 'Desconhecida',
                    'destino': f[1] or 'Desconhecida',
                    'total_transferencias': f[2],
                    'concluidas': f[3] or 0,
                    'tempo_medio_minutos': int(f[4]) if f[4] else 0
                } for f in fluxos
            ],
            'motivos_principais': [
                {
                    'motivo': m[0],
                    'total': m[1]
                } for m in motivos
            ]
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro em transferencias_estaduais: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_estadual_bp.route('/comparativo-periodos')
@login_required
@requer_permissao('ver_analytics')
def comparativo_periodos():
    """
    Compara indicadores entre dois períodos
    """
    try:
        dias = request.args.get('dias', 30, type=int)
        
        # Período atual
        data_atual_inicio = datetime.now() - timedelta(days=dias)
        data_atual_fim = datetime.now()
        
        # Período anterior
        data_anterior_inicio = datetime.now() - timedelta(days=dias*2)
        data_anterior_fim = datetime.now() - timedelta(days=dias)
        
        def calcular_metricas(data_inicio, data_fim):
            consultas = Consulta.query.filter(
                and_(Consulta.data_consulta >= data_inicio, Consulta.data_consulta <= data_fim)
            ).count()
            
            internacoes = Internacao.query.filter(
                and_(Internacao.data_admissao >= data_inicio, Internacao.data_admissao <= data_fim)
            ).count()
            
            pacientes = Paciente.query.join(Consulta).filter(
                and_(Consulta.data_consulta >= data_inicio, Consulta.data_consulta <= data_fim)
            ).count()
            
            agendamentos = Agendamento.query.filter(
                and_(Agendamento.data_agendamento >= data_inicio, Agendamento.data_agendamento <= data_fim)
            ).count()
            
            faltas = Agendamento.query.filter(
                and_(
                    Agendamento.data_agendamento >= data_inicio,
                    Agendamento.data_agendamento <= data_fim,
                    Agendamento.status == 'faltou'
                )
            ).count()
            
            return {
                'consultas': consultas,
                'internacoes': internacoes,
                'pacientes': pacientes,
                'agendamentos': agendamentos,
                'faltas': faltas,
                'taxa_falta': round((faltas / agendamentos * 100), 2) if agendamentos > 0 else 0
            }
        
        atual = calcular_metricas(data_atual_inicio, data_atual_fim)
        anterior = calcular_metricas(data_anterior_inicio, data_anterior_fim)
        
        # Calcular variações
        def variacao(atual_val, anterior_val):
            if anterior_val == 0:
                return 0
            return round(((atual_val - anterior_val) / anterior_val * 100), 2)
        
        return jsonify({