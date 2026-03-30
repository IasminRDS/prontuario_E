# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.unidade import Unidade
from models.internacao import Setor, Leito, Internacao
from models.transferencia import TransferenciaPaciente
from database.db import db
from datetime import datetime, date

regulacao_bp = Blueprint('regulacao', __name__, url_prefix='/regulacao')


@regulacao_bp.route('/')
@login_required
def index():
    """Central de vagas — visão de todos os leitos do estado."""
    tipo_filtro = request.args.get('tipo', '')
    mun_filtro  = request.args.get('municipio', '')

    unidades_q = Unidade.query.filter_by(ativo=True)
    if mun_filtro:
        unidades_q = unidades_q.filter(Unidade.municipio.ilike(f'%{mun_filtro}%'))
    unidades = unidades_q.order_by(Unidade.municipio, Unidade.nome).all()

    # Montar mapa de vagas por unidade
    mapa = []
    for u in unidades:
        setores_u = Setor.query.filter_by(ativo=True).all()
        setores_dados = []
        for s in setores_u:
            if tipo_filtro and s.tipo != tipo_filtro:
                continue
            total   = s.total_leitos
            ocupados= s.leitos_ocupados
            livres  = s.leitos_livres
            if total == 0:
                continue
            setores_dados.append({
                'id':      s.id,
                'nome':    s.nome,
                'tipo':    s.tipo,
                'total':   total,
                'ocupados':ocupados,
                'livres':  livres,
                'taxa':    s.taxa_ocupacao,
            })
        if setores_dados:
            total_u   = sum(s['total']    for s in setores_dados)
            livres_u  = sum(s['livres']   for s in setores_dados)
            ocupados_u= sum(s['ocupados'] for s in setores_dados)
            taxa_u    = round(ocupados_u / total_u * 100) if total_u else 0
            mapa.append({
                'unidade':   u,
                'setores':   setores_dados,
                'total':     total_u,
                'livres':    livres_u,
                'ocupados':  ocupados_u,
                'taxa':      taxa_u,
            })

    # Transferências pendentes de alocação
    transferencias_pendentes = TransferenciaPaciente.query.filter(
        TransferenciaPaciente.status.in_(['solicitada', 'aceita', 'em_transito'])
    ).order_by(TransferenciaPaciente.data_solicitacao).all()

    # Totais estado
    total_leitos  = sum(m['total']    for m in mapa)
    total_livres  = sum(m['livres']   for m in mapa)
    total_ocupados= sum(m['ocupados'] for m in mapa)
    taxa_estado   = round(total_ocupados / total_leitos * 100) if total_leitos else 0

    # Municípios disponíveis para filtro
    municipios = sorted(set(u.municipio for u in unidades if u.municipio))

    return render_template('regulacao/index.html',
                           mapa=mapa,
                           transferencias_pendentes=transferencias_pendentes,
                           total_leitos=total_leitos,
                           total_livres=total_livres,
                           total_ocupados=total_ocupados,
                           taxa_estado=taxa_estado,
                           municipios=municipios,
                           tipo_filtro=tipo_filtro,
                           mun_filtro=mun_filtro)


@regulacao_bp.route('/api/vagas')
@login_required
def api_vagas():
    """API para consulta de vagas em tempo real."""
    tipo = request.args.get('tipo', '')
    setores = Setor.query.filter_by(ativo=True)
    if tipo:
        setores = setores.filter_by(tipo=tipo)
    resultado = []
    for s in setores.all():
        if s.leitos_livres > 0:
            resultado.append({
                'setor':     s.nome,
                'tipo':      s.tipo,
                'livres':    s.leitos_livres,
                'total':     s.total_leitos,
                'taxa':      s.taxa_ocupacao,
            })
    resultado.sort(key=lambda x: x['taxa'])
    return jsonify(resultado)
