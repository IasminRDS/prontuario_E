# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.kpi import KPI
from models.unidade import Unidade
from database.db import db
from datetime import datetime, date, timedelta

api_kpi_bp = Blueprint('api_kpi', __name__, url_prefix='/api/kpi')

@api_kpi_bp.route('/painel/<int:unidade_id>')
@login_required
def painel_kpi(unidade_id):
    """Retorna KPIs da unidade em JSON"""
    if not current_user.pode_ver_unidade(unidade_id):
        return jsonify({'erro': 'Acesso negado'}), 403
    
    dias = request.args.get('dias', 30, type=int)
    data_inicio = date.today() - timedelta(days=dias)
    
    kpis = KPI.query.filter(
        KPI.unidade_id == unidade_id,
        KPI.data >= data_inicio
    ).order_by(KPI.data).all()
    
    return jsonify({
        'unidade_id': unidade_id,
        'periodo_dias': dias,
        'total_registros': len(kpis),
        'dados': [k.to_dict() for k in kpis],
        'resumo': {
            'atendimentos_total': sum(k.atendimentos for k in kpis),
            'internacoes_total': sum(k.internacoes for k in kpis),
            'taxa_ocupacao_media': sum(k.taxa_ocupacao for k in kpis) / len(kpis) if kpis else 0,
            'taxa_mortalidade_media': sum(k.taxa_mortalidade for k in kpis) / len(kpis) if kpis else 0,
        }
    })

@api_kpi_bp.route('/comparativo')
@login_required
def comparativo_unidades():
    """Compara KPIs entre unidades"""
    if not current_user.pode_ver_estadual():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    data_ini = request.args.get('data_ini', (date.today() - timedelta(days=30)).isoformat())
    data_fim = request.args.get('data_fim', date.today().isoformat())
    
    unidades = Unidade.query.filter_by(ativo=True).all()
    comparativo = []
    
    for u in unidades:
        kpis = KPI.query.filter(
            KPI.unidade_id == u.id,
            KPI.data.between(data_ini, data_fim)
        ).all()
        
        if kpis:
            comparativo.append({
                'unidade': u.nome,
                'municipio': u.municipio,
                'atendimentos': sum(k.atendimentos for k in kpis),
                'internacoes': sum(k.internacoes for k in kpis),
                'altas': sum(k.altas for k in kpis),
                'obitos': sum(k.obitos for k in kpis),
                'taxa_ocupacao_media': sum(k.taxa_ocupacao for k in kpis) / len(kpis),
                'taxa_mortalidade_media': sum(k.taxa_mortalidade for k in kpis) / len(kpis),
            })
    
    return jsonify(comparativo)

@api_kpi_bp.route('/atualizar-cache', methods=['POST'])
@login_required
def atualizar_cache():
    """Recalcula KPIs do dia - executado a cada hora"""
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    from models.atendimento import Atendimento
    from models.internacao import Internacao, Leito
    from models.cirurgia import Cirurgia
    from models.pronto_socorro import AtendimentoPS
    
    unidades = Unidade.query.filter_by(ativo=True).all()
    hoje = date.today()
    
    for u in unidades:
        # Verificar se já existe KPI de hoje
        kpi_existente = KPI.query.filter_by(unidade_id=u.id, data=hoje).first()
        
        atendimentos = Atendimento.query.filter(
            Atendimento.unidade_id == u.id,
            db.func.date(Atendimento.data_hora) == hoje
        ).count()
        
        internacoes = Internacao.query.filter(
            Internacao.unidade_id == u.id,
            db.func.date(Internacao.data_entrada) == hoje
        ).count()
        
        altas = Internacao.query.filter(
            Internacao.unidade_id == u.id,
            db.func.date(Internacao.data_alta) == hoje,
            Internacao.status == 'alta'
        ).count()
        
        obitos = Internacao.query.filter(
            Internacao.unidade_id == u.id,
            db.func.date(Internacao.data_alta) == hoje,
            Internacao.status == 'obito'
        ).count()
        
        cirurgias = Cirurgia.query.filter(
            Cirurgia.unidade_id == u.id,
            db.func.date(Cirurgia.data_agendada) == hoje,
            Cirurgia.status == 'realizada'
        ).count()
        
        ps = AtendimentoPS.query.filter(
            AtendimentoPS.unidade_id == u.id,
            db.func.date(AtendimentoPS.data_entrada) == hoje
        ).count()
        
        total_leitos = Leito.query.filter_by(ativo=True).count()
        leitos_ocupados = Leito.query.filter_by(ativo=True, status='ocupado').count()
        taxa_ocupacao = round((leitos_ocupados / total_leitos * 100) if total_leitos else 0)
        
        taxa_mortalidade = round((obitos / internacoes * 100) if internacoes > 0 else 0)
        taxa_altas = round((altas / internacoes * 100) if internacoes > 0 else 0)
        
        if kpi_existente:
            kpi_existente.atendimentos = atendimentos
            kpi_existente.internacoes = internacoes
            kpi_existente.altas = altas
            kpi_existente.obitos = obitos
            kpi_existente.cirurgias = cirurgias
            kpi_existente.taxa_ocupacao = taxa_ocupacao
            kpi_existente.taxa_mortalidade = taxa_mortalidade
            kpi_existente.taxa_altas = taxa_altas
            kpi_existente.ps_atendimentos = ps
            kpi_existente.timestamp = datetime.now()
        else:
            kpi = KPI(
                unidade_id=u.id,
                data=hoje,
                atendimentos=atendimentos,
                internacoes=internacoes,
                altas=altas,
                obitos=obitos,
                cirurgias=cirurgias,
                taxa_ocupacao=taxa_ocupacao,
                taxa_mortalidade=taxa_mortalidade,
                taxa_altas=taxa_altas,
                ps_atendimentos=ps,
            )
            db.session.add(kpi)
    
    db.session.commit()
    return jsonify({'status': 'KPIs atualizados com sucesso'})