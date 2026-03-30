# -*- coding: utf-8 -*-
"""
Dashboard Estadual Avançado - v2.0
Visualização em tempo real de KPIs estaduais
"""

from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import login_required
from database.db import db
from models import (
    Paciente, UnidadeSaude, Consulta, Internacao, Agendamento, 
    Triagem, Regulacao, Vaga, Transferencia, Alerta, KPIEstadual
)
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, distinct, case
from functools import wraps

# Blueprint
dash_estadual_bp = Blueprint(
    'dashboard_estadual',
    __name__,
    url_prefix='/dashboard/estadual',
    template_folder='../templates/dashboard'
)

# ========== DECORADOR: Requer Permissão ==========
def requer_permissao(permissao):
    """Decorador para verificar permissões"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            if not current_user.is_authenticated:
                return jsonify({'error': 'Não autenticado'}), 401
            if not current_user.tem_permissao(permissao):
                return jsonify({'error': 'Acesso negado'}), 403
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# ========== FUNÇÕES AUXILIARES ==========

def calcular_kpis():
    """Calcula todos os KPIs estaduais"""
    try:
        # Total de pacientes
        total_pacientes = Paciente.query.count()
        
        # Pacientes ativos (última consulta últimos 30 dias)
        data_30d_atras = datetime.now() - timedelta(days=30)
        pacientes_ativos_30d = Paciente.query.join(Consulta).filter(
            Consulta.data_consulta >= data_30d_atras
        ).count()
        
        # Unidades ativas
        unidades_ativas = UnidadeSaude.query.filter_by(ativo=True).count()
        
        # Leitos ocupados
        leitos_ocupados = Internacao.query.filter(
            Internacao.data_saida.is_(None)
        ).count()
        
        # Vagas disponíveis
        vagas_disponiveis = Vaga.query.filter_by(ocupada=False, ativa=True).count()
        vagas_totais = Vaga.query.filter_by(ativa=True).count()
        
        # Taxa de ocupação
        taxa_ocupacao = (leitos_ocupados / vagas_totais * 100) if vagas_totais > 0 else 0
        
        # Taxa de ocupação UTI
        uti_ocupados = Internacao.query.filter(
            and_(
                Internacao.tipo_leito == 'UTI',
                Internacao.data_saida.is_(None)
            )
        ).count()
        uti_total = Vaga.query.filter_by(
            tipo_leito='UTI', ativa=True
        ).count()
        taxa_ocupacao_uti = (uti_ocupados / uti_total * 100) if uti_total > 0 else 0
        
        # Agendamentos pendentes
        agendamentos_pendentes = Agendamento.query.filter_by(
            status='pendente'
        ).count()
        
        # Tempo médio de atendimento (em minutos)
        consultas_recentes = db.session.query(
            func.avg(
                func.timestampdiff('MINUTE', Consulta.data_entrada, Consulta.data_saida)
            ).label('tempo_medio')
        ).filter(
            Consulta.data_consulta >= data_30d_atras
        ).scalar() or 0
        
        # Taxa de reinternação
        pacientes_reinternados = db.session.query(
            func.count(distinct(Internacao.paciente_id)).label('total')
        ).having(
            func.count(Internacao.id) > 1
        ).scalar() or 0
        total_internacoes = Internacao.query.count()
        taxa_reinternacao = (pacientes_reinternados / total_internacoes * 100) if total_internacoes > 0 else 0
        
        return {
            'total_pacientes': total_pacientes,
            'pacientes_ativos_30d': pacientes_ativos_30d,
            'unidades_ativas': unidades_ativas,
            'leitos_ocupados': leitos_ocupados,
            'vagas_disponiveis': vagas_disponiveis,
            'vagas_totais': vagas_totais,
            'taxa_ocupacao': round(taxa_ocupacao, 2),
            'taxa_ocupacao_uti': round(taxa_ocupacao_uti, 2),
            'agendamentos_pendentes': agendamentos_pendentes,
            'tempo_medio_atendimento': int(consultas_recentes),
            'taxa_reinternacao': round(taxa_reinternacao, 2)
        }
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular KPIs: {e}")
        return None

def calcular_timeline_30d():
    """Calcula série temporal dos últimos 30 dias"""
    try:
        data_inicio = datetime.now() - timedelta(days=30)
        
        timeline = db.session.query(
            func.date(Consulta.data_consulta).label('data'),
            func.count(Consulta.id).label('consultas'),
            func.count(distinct(Consulta.paciente_id)).label('pacientes'),
            func.count(distinct(Internacao.id)).label('internacoes')
        ).outerjoin(Internacao).filter(
            Consulta.data_consulta >= data_inicio
        ).group_by(
            func.date(Consulta.data_consulta)
        ).order_by(
            func.date(Consulta.data_consulta)
        ).all()
        
        return [
            {
                'data': str(t[0]),
                'consultas': t[1],
                'pacientes': t[2],
                'internacoes': t[3]
            } for t in timeline
        ]
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular timeline: {e}")
        return []

def calcular_stats_regiao():
    """Calcula estatísticas por região"""
    try:
        regioes = db.session.query(
            UnidadeSaude.regiao,
            func.count(distinct(Paciente.id)).label('pacientes'),
            func.count(Consulta.id).label('consultas'),
            func.count(Internacao.id).label('internacoes'),
            func.count(distinct(
                case([(Agendamento.status == 'faltou', Agendamento.id)])
            )).label('faltas'),
            func.count(Vaga.id).label('vagas_totais'),
            func.count(case([(Vaga.ocupada == False, Vaga.id)])).label('vagas_livres')
        ).outerjoin(Paciente).outerjoin(Consulta).outerjoin(
            Internacao
        ).outerjoin(Agendamento).outerjoin(Vaga).group_by(
            UnidadeSaude.regiao
        ).all()
        
        return [
            {
                'regiao': r[0],
                'pacientes': r[1],
                'consultas': r[2],
                'internacoes': r[3],
                'faltas': r[4],
                'vagas_totais': r[5],
                'vagas_livres': r[6],
                'taxa_ocupacao': round((r[5] - r[6]) / r[5] * 100, 2) if r[5] > 0 else 0
            } for r in regioes if r[0]
        ]
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular stats regionais: {e}")
        return []

def calcular_top_especialidades():
    """Retorna top 10 especialidades mais consultadas"""
    try:
        top = db.session.query(
            Consulta.especialidade,
            func.count(Consulta.id).label('total'),
            func.count(distinct(Consulta.paciente_id)).label('pacientes_unicos'),
            func.avg(
                func.timestampdiff('MINUTE', Consulta.data_entrada, Consulta.data_saida)
            ).label('tempo_medio')
        ).filter(
            Consulta.data_consulta >= datetime.now() - timedelta(days=30)
        ).group_by(
            Consulta.especialidade
        ).order_by(
            func.count(Consulta.id).desc()
        ).limit(10).all()
        
        return [
            {
                'especialidade': e[0],
                'total_consultas': e[1],
                'pacientes_unicos': e[2],
                'tempo_medio_min': int(e[3]) if e[3] else 0
            } for e in top
        ]
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular especialidades: {e}")
        return []

def calcular_alertas():
    """Calcula alertas ativos e críticos"""
    try:
        alertas_criticos = Alerta.query.filter(
            and_(
                Alerta.ativo == True,
                Alerta.severidade.in_(['critico', 'alto'])
            )
        ).count()
        
        alertas_totais = Alerta.query.filter(
            Alerta.ativo == True
        ).count()
        
        alertas_por_tipo = db.session.query(
            Alerta.tipo,
            func.count(Alerta.id).label('total')
        ).filter(Alerta.ativo == True).group_by(Alerta.tipo).all()
        
        return {
            'criticos': alertas_criticos,
            'totais': alertas_totais,
            'por_tipo': [
                {'tipo': a[0], 'total': a[1]} for a in alertas_por_tipo
            ]
        }
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular alertas: {e}")
        return {'criticos': 0, 'totais': 0, 'por_tipo': []}

# ========== ROTAS DO DASHBOARD ==========

@dash_estadual_bp.route('/')
@login_required
@requer_permissao('ver_dashboard_estadual')
def index():
    """Dashboard principal estadual"""
    return render_template('dashboard/estadual/index.html')

@dash_estadual_bp.route('/api/vista-geral')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_vista_geral():
    """
    API: Retorna todos os dados do dashboard em uma única requisição
    """
    try:
        kpis = calcular_kpis()
        timeline = calcular_timeline_30d()
        regioes = calcular_stats_regiao()
        especialidades = calcular_top_especialidades()
        alertas = calcular_alertas()
        
        # Salvar KPIs no banco (para histórico)
        kpi_hoje = KPIEstadual.query.filter_by(
            data=datetime.now().date()
        ).first()
        
        if not kpi_hoje:
            kpi_hoje = KPIEstadual(
                data=datetime.now().date(),
                **kpis
            )
            db.session.add(kpi_hoje)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'kpis': kpis,
            'timeline': timeline,
            'regioes': regioes,
            'especialidades': especialidades,
            'alertas': alertas
        })
    
    except Exception as e:
        current_app.logger.error(f"Erro em vista-geral: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@dash_estadual_bp.route('/api/kpis')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_kpis():
    """API: Apenas KPIs"""
    try:
        kpis = calcular_kpis()
        return jsonify(kpis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/timeline')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_timeline():
    """API: Série temporal"""
    try:
        dias = request.args.get('dias', 30, type=int)
        data_inicio = datetime.now() - timedelta(days=dias)
        
        timeline = db.session.query(
            func.date(Consulta.data_consulta).label('data'),
            func.count(Consulta.id).label('consultas'),
            func.count(distinct(Consulta.paciente_id)).label('pacientes'),
            func.count(distinct(Internacao.id)).label('internacoes'),
            func.sum(case([(Agendamento.status == 'faltou', 1)])).label('faltas')
        ).outerjoin(Internacao).outerjoin(Agendamento).filter(
            Consulta.data_consulta >= data_inicio
        ).group_by(
            func.date(Consulta.data_consulta)
        ).order_by(
            func.date(Consulta.data_consulta)
        ).all()
        
        return jsonify([
            {
                'data': str(t[0]),
                'consultas': t[1],
                'pacientes': t[2],
                'internacoes': t[3],
                'faltas': t[4] or 0
            } for t in timeline
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/regioes')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_regioes():
    """API: Dados por região"""
    try:
        regioes = calcular_stats_regiao()
        return jsonify(regioes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/especialidades')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_especialidades():
    """API: Top especialidades"""
    try:
        especialidades = calcular_top_especialidades()
        return jsonify(especialidades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/alertas')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_alertas():
    """API: Alertas ativos"""
    try:
        alertas = Alerta.query.filter(
            Alerta.ativo == True
        ).order_by(
            Alerta.data_criacao.desc()
        ).limit(50).all()
        
        return jsonify([
            {
                'id': a.id,
                'codigo': a.codigo,
                'tipo': a.tipo,
                'severidade': a.severidade,
                'titulo': a.titulo,
                'descricao': a.descricao,
                'data_criacao': a.data_criacao.isoformat(),
                'tempo_ativo_min': a.tempo_ativo_minutos,
                'lido': a.lido
            } for a in alertas
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/comparativo-regioes')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_comparativo_regioes():
    """API: Comparativo entre regiões"""
    try:
        regioes = calcular_stats_regiao()
        
        if not regioes:
            return jsonify([])
        
        # Ordenar por diferentes métricas
        regioes_ordenadas = sorted(regioes, key=lambda x: x['taxa_ocupacao'], reverse=True)
        
        return jsonify({
            'por_ocupacao': regioes_ordenadas,
            'por_pacientes': sorted(regioes, key=lambda x: x['pacientes'], reverse=True),
            'por_vagas_livres': sorted(regioes, key=lambda x: x['vagas_livres'], reverse=True)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/saude-publica')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_saude_publica():
    """API: Indicadores de Saúde Pública"""
    try:
        periodo_dias = request.args.get('dias', 30, type=int)
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        # Indicadores
        cobertura = Paciente.query.join(Consulta).filter(
            Consulta.data_consulta >= data_inicio
        ).count()
        
        total_pop_estimada = Paciente.query.count()
        taxa_cobertura = (cobertura / total_pop_estimada * 100) if total_pop_estimada > 0 else 0
        
        # Taxa de mortalidade (pacientes com óbito registrado)
        obitos = db.session.query(func.count(Paciente.id)).filter(
            and_(
                Paciente.data_obito.isnot(None),
                Paciente.data_obito >= data_inicio
            )
        ).scalar() or 0
        
        # Taxa de internação
        internacoes = Internacao.query.filter(
            Internacao.data_admissao >= data_inicio
        ).count()
        taxa_internacao = (internacoes / total_pop_estimada * 100) if total_pop_estimada > 0 else 0
        
        return jsonify({
            'taxa_cobertura': round(taxa_cobertura, 2),
            'pacientes_cobertos': cobertura,
            'taxa_internacao': round(taxa_internacao, 2),
            'obitos': obitos,
            'periodo_dias': periodo_dias
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/eficiencia')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_eficiencia():
    """API: Indicadores de eficiência operacional"""
    try:
        # Eficiência por unidade
        unidades = db.session.query(
            UnidadeSaude.id,
            UnidadeSaude.nome,
            UnidadeSaude.regiao,
            func.count(distinct(Consulta.paciente_id)).label('pacientes_atendidos'),
            func.count(Consulta.id).label('total_consultas'),
            func.avg(
                func.timestampdiff('MINUTE', Consulta.data_entrada, Consulta.data_saida)
            ).label('tempo_medio_consulta'),
            func.sum(case([(Agendamento.status == 'faltou', 1)])).label('faltas'),
            func.count(Agendamento.id).label('agendamentos_total')
        ).join(Consulta, isouter=True).join(
            Agendamento, isouter=True
        ).group_by(UnidadeSaude.id).all()
        
        resultado = []
        for u in unidades:
            taxa_falta = (u[6] / u[7] * 100) if u[7] > 0 else 0
            resultado.append({
                'unidade_id': u[0],
                'nome': u[1],
                'regiao': u[2],
                'pacientes_atendidos': u[3],
                'total_consultas': u[4],
                'tempo_medio_consulta_min': int(u[5]) if u[5] else 0,
                'taxa_falta': round(taxa_falta, 2)
            })
        
        return jsonify(sorted(resultado, key=lambda x: x['total_consultas'], reverse=True))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dash_estadual_bp.route('/api/historico-kpi')
@login_required
@requer_permissao('ver_dashboard_estadual')
def api_historico_kpi():
    """API: Histórico de KPIs"""
    try:
        dias = request.args.get('dias', 30, type=int)
        data_inicio = datetime.now().date() - timedelta(days=dias)
        
        kpis = KPIEstadual.query.filter(
            KPIEstadual.data >= data_inicio
        ).order_by(KPIEstadual.data).all()
        
        return jsonify([
            {
                'data': str(k.data),
                'total_pacientes': k.total_pacientes,
                'pacientes_ativos_30d': k.pacientes_ativos_30d,
                'taxa_ocupacao': k.taxa_ocupacao,
                'taxa_ocupacao_uti': k.taxa_ocupacao_uti,
                'tempo_medio_atendimento': k.tempo_media_atendimento,
                'taxa_reinternacao': k.taxa_reinternacao
            } for k in kpis
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500