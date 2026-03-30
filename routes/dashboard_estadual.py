# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
from models.unidade import Unidade
from models.paciente import Paciente
from models.atendimento import Atendimento
from models.internacao import Internacao, Setor, Leito
from models.triagem import Triagem
from models.exame import ExameSolicitado
from models.encaminhamento import Encaminhamento
from models.pronto_socorro import AtendimentoPS
from models.estoque import ItemEstoque
from models.cirurgia import Cirurgia
from database.db import db
from datetime import datetime, date, timedelta

dash_estadual_bp = Blueprint('dash_estadual', __name__, url_prefix='/estadual')


def _requer_estadual():
    if not current_user.pode_ver_estadual():
        abort(403)


def _dados_unidade(u, hoje, inicio_mes):
    """Agrega indicadores de uma unidade."""
    uid = u.id

    # Pacientes
    total_pac = Paciente.query.filter_by(ativo=True).count()

    # Atendimentos
    at_hoje = Atendimento.query.filter(
        db.func.date(Atendimento.data_hora) == hoje).count()
    at_mes = Atendimento.query.filter(
        Atendimento.data_hora >= inicio_mes).count()

    # Internações ativas
    internados = Internacao.query.filter_by(
        unidade_id=uid, status='ativa').count()

    # Leitos
    total_leitos = Leito.query.join(Setor).filter(
        Setor.ativo == True, Leito.ativo == True).count()
    leitos_ocu = Leito.query.join(Setor).filter(
        Setor.ativo == True, Leito.ativo == True,
        Leito.status == 'ocupado').count()
    taxa_ocu = round(leitos_ocu / total_leitos * 100) if total_leitos else 0

    # PS ativo
    ps_fila = AtendimentoPS.query.filter(
        AtendimentoPS.unidade_id == uid,
        AtendimentoPS.status.notin_(
            ['alta', 'internado', 'transferido', 'obito', 'evasao'])
    ).count()
    ps_criticos = AtendimentoPS.query.filter(
        AtendimentoPS.unidade_id == uid,
        AtendimentoPS.classificacao.in_(['vermelho', 'laranja']),
        AtendimentoPS.status.notin_(
            ['alta', 'internado', 'transferido', 'obito', 'evasao'])
    ).count()

    # Exames pendentes
    exames_pend = ExameSolicitado.query.filter(
        ExameSolicitado.unidade_id == uid,
        ExameSolicitado.status.in_(['solicitado', 'coletado', 'em_analise'])
    ).count()

    # Encaminhamentos abertos
    enc_abertos = Encaminhamento.query.filter(
        Encaminhamento.unidade_origem_id == uid,
        Encaminhamento.status.in_(['solicitado', 'agendado'])
    ).count()

    # Cirurgias hoje
    cir_hoje = Cirurgia.query.filter(
        db.func.date(Cirurgia.data_agendada) == hoje,
        Cirurgia.unidade_id == uid
    ).count()

    # Estoque crítico
    est_critico = ItemEstoque.query.filter(
        ItemEstoque.unidade_id == uid,
        ItemEstoque.ativo == True,
        ItemEstoque.quantidade <= ItemEstoque.estoque_minimo
    ).count()

    # Alertas
    alertas = []
    if ps_criticos > 0:
        alertas.append({'tipo': 'critico', 'msg': f'{ps_criticos} emergência(s) no PS'})
    if taxa_ocu >= 90:
        alertas.append({'tipo': 'aviso', 'msg': f'Ocupação {taxa_ocu}% — lotação crítica'})
    if est_critico > 0:
        alertas.append({'tipo': 'aviso', 'msg': f'{est_critico} item(ns) em falta'})

    return {
        'id':           uid,
        'nome':         u.nome,
        'tipo':         u.tipo or 'Unidade',
        'municipio':    u.municipio or '—',
        'uf':           u.uf or '—',
        'cnes':         u.cnes or '—',
        'total_pac':    total_pac,
        'at_hoje':      at_hoje,
        'at_mes':       at_mes,
        'internados':   internados,
        'total_leitos': total_leitos,
        'leitos_ocu':   leitos_ocu,
        'taxa_ocu':     taxa_ocu,
        'ps_fila':      ps_fila,
        'ps_criticos':  ps_criticos,
        'exames_pend':  exames_pend,
        'enc_abertos':  enc_abertos,
        'cir_hoje':     cir_hoje,
        'est_critico':  est_critico,
        'alertas':      alertas,
    }


@dash_estadual_bp.route('/')
@login_required
def index():
    _requer_estadual()
    hoje       = date.today()
    inicio_mes = hoje.replace(day=1)

    unidades = Unidade.query.filter_by(ativo=True).order_by(
        Unidade.municipio, Unidade.nome).all()

    dados_unidades = [_dados_unidade(u, hoje, inicio_mes) for u in unidades]

    # Totais consolidados
    total_pac      = Paciente.query.filter_by(ativo=True).count()
    total_at_hoje  = Atendimento.query.filter(
        db.func.date(Atendimento.data_hora) == hoje).count()
    total_at_mes   = Atendimento.query.filter(
        Atendimento.data_hora >= inicio_mes).count()
    total_internados = Internacao.query.filter_by(status='ativa').count()
    total_leitos   = Leito.query.join(Setor).filter(
        Setor.ativo == True, Leito.ativo == True).count()
    total_ocu      = Leito.query.join(Setor).filter(
        Setor.ativo == True, Leito.ativo == True,
        Leito.status == 'ocupado').count()
    taxa_estado    = round(total_ocu / total_leitos * 100) if total_leitos else 0
    total_ps       = AtendimentoPS.query.filter(
        AtendimentoPS.status.notin_(
            ['alta', 'internado', 'transferido', 'obito', 'evasao'])
    ).count()
    total_criticos = AtendimentoPS.query.filter(
        AtendimentoPS.classificacao.in_(['vermelho', 'laranja']),
        AtendimentoPS.status.notin_(
            ['alta', 'internado', 'transferido', 'obito', 'evasao'])
    ).count()
    total_unidades = len(unidades)
    unid_alertas   = sum(1 for d in dados_unidades if d['alertas'])

    # Atendimentos últimos 7 dias — todos os estados
    labels_7d, atend_7d = [], []
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        labels_7d.append(d.strftime('%d/%m'))
        atend_7d.append(
            Atendimento.query.filter(
                db.func.date(Atendimento.data_hora) == d).count())

    # Por tipo de unidade
    tipos = {}
    for u in unidades:
        t = u.tipo or 'Outro'
        tipos[t] = tipos.get(t, 0) + 1

    # Por município
    municipios = {}
    for d in dados_unidades:
        m = d['municipio']
        if m not in municipios:
            municipios[m] = {'unidades': 0, 'internados': 0,
                              'ps_fila': 0, 'at_hoje': 0}
        municipios[m]['unidades']  += 1
        municipios[m]['internados'] += d['internados']
        municipios[m]['ps_fila']   += d['ps_fila']
        municipios[m]['at_hoje']   += d['at_hoje']

    return render_template('dashboard_estadual/index.html',
        hoje=hoje,
        dados_unidades=dados_unidades,
        total_pac=total_pac,
        total_at_hoje=total_at_hoje,
        total_at_mes=total_at_mes,
        total_internados=total_internados,
        total_leitos=total_leitos,
        total_ocu=total_ocu,
        taxa_estado=taxa_estado,
        total_ps=total_ps,
        total_criticos=total_criticos,
        total_unidades=total_unidades,
        unid_alertas=unid_alertas,
        labels_7d=labels_7d,
        atend_7d=atend_7d,
        tipos_labels=list(tipos.keys()),
        tipos_dados=list(tipos.values()),
        municipios=municipios,
    )


@dash_estadual_bp.route('/api/resumo')
@login_required
def api_resumo():
    _requer_estadual()
    hoje = date.today()
    unidades = Unidade.query.filter_by(ativo=True).all()
    resumo = []
    for u in unidades:
        leitos_t = Leito.query.join(Setor).filter(
            Setor.ativo == True, Leito.ativo == True).count()
        leitos_o = Leito.query.join(Setor).filter(
            Setor.ativo == True, Leito.ativo == True,
            Leito.status == 'ocupado').count()
        ps_crit = AtendimentoPS.query.filter(
            AtendimentoPS.unidade_id == u.id,
            AtendimentoPS.classificacao.in_(['vermelho', 'laranja']),
            AtendimentoPS.status.notin_(
                ['alta', 'internado', 'transferido', 'obito', 'evasao'])
        ).count()
        resumo.append({
            'id': u.id, 'nome': u.nome, 'municipio': u.municipio,
            'taxa_ocu': round(leitos_o / leitos_t * 100) if leitos_t else 0,
            'ps_criticos': ps_crit,
        })
    return jsonify(resumo)
