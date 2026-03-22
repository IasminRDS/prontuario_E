# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.pronto_socorro import AtendimentoPS
from models.paciente import Paciente
from models.medico import Medico
from database.db import db
from utils.audit import registrar
from datetime import datetime, date

ps_bp = Blueprint('ps', __name__, url_prefix='/ps')

ORDEM_CORES = ['vermelho', 'laranja', 'amarelo', 'verde', 'azul']

@ps_bp.route('/')
@login_required
def painel():
    uid = current_user.unidade_id
    ativos = AtendimentoPS.query.filter(
        AtendimentoPS.unidade_id == uid,
        AtendimentoPS.status.notin_(['alta','internado','transferido','obito','evasao'])
    ).order_by(AtendimentoPS.data_entrada).all()

    fila = {cor: [] for cor in ORDEM_CORES}
    for a in ativos:
        if a.classificacao in fila:
            fila[a.classificacao].append(a)

    stats = {
        'total':       len(ativos),
        'vermelho':    len(fila['vermelho']),
        'laranja':     len(fila['laranja']),
        'amarelo':     len(fila['amarelo']),
        'verde':       len(fila['verde']),
        'azul':        len(fila['azul']),
        'atendimento': sum(1 for a in ativos if a.status == 'em_atendimento'),
        'observacao':  sum(1 for a in ativos if a.status == 'em_observacao'),
    }
    return render_template('ps/painel.html', fila=fila, stats=stats,
                           ORDEM_CORES=ORDEM_CORES)

@ps_bp.route('/entrada', methods=['GET', 'POST'])
@login_required
def entrada():
    pacientes = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
    if request.method == 'POST':
        try:
            ps = AtendimentoPS(
                paciente_id=int(request.form['paciente_id']),
                unidade_id=current_user.unidade_id,
                criado_por=current_user.id,
                queixa_principal=request.form.get('queixa_principal', '').strip() or None,
                modo_chegada=request.form.get('modo_chegada', 'espontaneo'),
                classificacao=request.form.get('classificacao', 'verde'),
                status='triagem_realizada' if request.form.get('classificacao') else 'aguardando_triagem',
                data_triagem=datetime.utcnow() if request.form.get('classificacao') else None,
            )
            db.session.add(ps)
            db.session.flush()
            registrar('atendimentos_ps', ps.id, 'create', 'Entrada PS registrada')
            db.session.commit()
            flash('Paciente registrado no PS!', 'success')
            return redirect(url_for('ps.painel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
    return render_template('ps/entrada.html', pacientes=pacientes)

@ps_bp.route('/<int:id>')
@login_required
def visualizar(id):
    ps = AtendimentoPS.query.get_or_404(id)
    medicos = Medico.query.all()
    return render_template('ps/visualizar.html', ps=ps, medicos=medicos)

@ps_bp.route('/<int:id>/chamar', methods=['POST'])
@login_required
def chamar(id):
    ps = AtendimentoPS.query.get_or_404(id)
    ps.status = 'em_atendimento'
    ps.data_chamada = datetime.utcnow()
    ps.data_atendimento = datetime.utcnow()
    ps.medico_id = request.form.get('medico_id') or ps.medico_id
    registrar('atendimentos_ps', id, 'update', 'Chamado para atendimento')
    db.session.commit()
    flash('Paciente chamado!', 'success')
    return redirect(url_for('ps.visualizar', id=id))

@ps_bp.route('/<int:id>/desfecho', methods=['POST'])
@login_required
def desfecho(id):
    ps = AtendimentoPS.query.get_or_404(id)
    try:
        desfecho = request.form.get('desfecho', 'alta')
        ps.desfecho = desfecho
        ps.status = desfecho if desfecho in ('alta','internado','transferido','obito','evasao') else 'alta'
        ps.data_desfecho = datetime.utcnow()
        ps.cid = request.form.get('cid', '').strip().upper() or None
        ps.hipotese_diag = request.form.get('hipotese_diag', '').strip() or None
        ps.conduta = request.form.get('conduta', '').strip() or None
        ps.observacoes = request.form.get('observacoes', '').strip() or None
        registrar('atendimentos_ps', id, 'update', f'Desfecho: {desfecho}')
        db.session.commit()
        flash('Desfecho registrado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {e}', 'danger')
    return redirect(url_for('ps.painel'))

@ps_bp.route('/<int:id>/observacao', methods=['POST'])
@login_required
def colocar_observacao(id):
    ps = AtendimentoPS.query.get_or_404(id)
    ps.status = 'em_observacao'
    registrar('atendimentos_ps', id, 'update', 'Paciente em observação')
    db.session.commit()
    flash('Paciente colocado em observação.', 'info')
    return redirect(url_for('ps.painel'))

@ps_bp.route('/historico')
@login_required
def historico():
    data_s = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    try:
        data_f = datetime.strptime(data_s, '%Y-%m-%d').date()
    except ValueError:
        data_f = date.today()
    ats = AtendimentoPS.query.filter(
        db.func.date(AtendimentoPS.data_entrada) == data_f,
        AtendimentoPS.unidade_id == current_user.unidade_id
    ).order_by(AtendimentoPS.data_entrada.desc()).all()
    return render_template('ps/historico.html', ats=ats, data_s=data_s, data_f=data_f)

@ps_bp.route('/api/fila')
@login_required
def api_fila():
    uid = current_user.unidade_id
    ativos = AtendimentoPS.query.filter(
        AtendimentoPS.unidade_id == uid,
        AtendimentoPS.status.notin_(['alta','internado','transferido','obito','evasao'])
    ).all()
    return jsonify({cor: sum(1 for a in ativos if a.classificacao == cor)
                    for cor in ORDEM_CORES})
