# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.faturamento import AIH, APAC
from models.internacao import Internacao
from models.paciente import Paciente
from models.medico import Medico
from database.db import db
from utils.audit import registrar
from datetime import datetime, date

faturamento_bp = Blueprint('faturamento', __name__, url_prefix='/faturamento')

@faturamento_bp.route('/')
@faturamento_bp.route('/aih')
@login_required
def aih_lista():
    status = request.args.get('status', '')
    comp   = request.args.get('competencia', date.today().strftime('%Y/%m'))
    uid    = current_user.unidade_id
    q = AIH.query.filter_by(unidade_id=uid)
    if status: q = q.filter_by(status=status)
    if comp:   q = q.filter_by(competencia=comp)
    aihs = q.order_by(AIH.criado_em.desc()).all()
    total_valor = sum(a.valor_total or 0 for a in aihs)
    return render_template('faturamento/aih_lista.html',
                           aihs=aihs, status=status, comp=comp, total_valor=total_valor)

@faturamento_bp.route('/aih/nova', methods=['GET', 'POST'])
@faturamento_bp.route('/aih/nova/<int:internacao_id>', methods=['GET', 'POST'])
@login_required
def aih_nova(internacao_id=None):
    internacoes = Internacao.query.filter_by(
        unidade_id=current_user.unidade_id, status='alta').all()
    medicos = Medico.query.all()
    intern_sel = Internacao.query.get(internacao_id) if internacao_id else None

    if request.method == 'POST':
        try:
            di_str = request.form.get('data_internacao', '').strip()
            ds_str = request.form.get('data_saida', '').strip()
            aih = AIH(
                internacao_id=int(request.form['internacao_id']),
                unidade_id=current_user.unidade_id,
                paciente_id=int(request.form['paciente_id']),
                medico_id=request.form.get('medico_id') or None,
                numero_aih=request.form.get('numero_aih', '').strip() or None,
                tipo_aih=request.form.get('tipo_aih', '1'),
                competencia=request.form.get('competencia', '').strip() or None,
                cid_principal=request.form.get('cid_principal', '').strip().upper() or None,
                cid_secundario=request.form.get('cid_secundario', '').strip().upper() or None,
                carater_internacao=request.form.get('carater_internacao', '01'),
                procedimento_principal=request.form.get('procedimento_principal', '').strip() or None,
                procedimento_secundario=request.form.get('procedimento_secundario', '').strip() or None,
                data_internacao=datetime.strptime(di_str, '%Y-%m-%d').date() if di_str else None,
                data_saida=datetime.strptime(ds_str, '%Y-%m-%d').date() if ds_str else None,
                dias_permanencia=int(request.form['dias_permanencia']) if request.form.get('dias_permanencia') else None,
                motivo_saida=request.form.get('motivo_saida', '').strip() or None,
                valor_total=float(request.form['valor_total']) if request.form.get('valor_total') else None,
                valor_sh=float(request.form['valor_sh']) if request.form.get('valor_sh') else None,
                valor_sp=float(request.form['valor_sp']) if request.form.get('valor_sp') else None,
                status=request.form.get('status', 'rascunho'),
                observacoes=request.form.get('observacoes', '').strip() or None,
            )
            db.session.add(aih)
            db.session.flush()
            registrar('aih', aih.id, 'create', f'AIH criada — competência {aih.competencia}')
            db.session.commit()
            flash('AIH registrada!', 'success')
            return redirect(url_for('faturamento.aih_lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')

    return render_template('faturamento/aih_form.html',
                           internacoes=internacoes, medicos=medicos,
                           intern_sel=intern_sel,
                           comp_atual=date.today().strftime('%Y/%m'))

@faturamento_bp.route('/aih/<int:id>', methods=['GET', 'POST'])
@login_required
def aih_editar(id):
    aih = AIH.query.get_or_404(id)
    medicos = Medico.query.all()
    if request.method == 'POST':
        try:
            aih.status = request.form.get('status', aih.status)
            aih.numero_aih = request.form.get('numero_aih', '').strip() or aih.numero_aih
            aih.valor_total = float(request.form['valor_total']) if request.form.get('valor_total') else aih.valor_total
            aih.observacoes = request.form.get('observacoes', '').strip() or None
            registrar('aih', id, 'update', f'AIH atualizada → {aih.status}')
            db.session.commit()
            flash('AIH atualizada!', 'success')
            return redirect(url_for('faturamento.aih_lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
    return render_template('faturamento/aih_form.html', aih=aih, medicos=medicos,
                           internacoes=[], intern_sel=aih.internacao,
                           comp_atual=aih.competencia or date.today().strftime('%Y/%m'))

@faturamento_bp.route('/apac')
@login_required
def apac_lista():
    status = request.args.get('status', '')
    uid    = current_user.unidade_id
    q = APAC.query.filter_by(unidade_id=uid)
    if status: q = q.filter_by(status=status)
    apacs = q.order_by(APAC.criado_em.desc()).all()
    return render_template('faturamento/apac_lista.html', apacs=apacs, status=status)

@faturamento_bp.route('/apac/nova', methods=['GET', 'POST'])
@login_required
def apac_nova():
    pacientes = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
    medicos   = Medico.query.all()
    if request.method == 'POST':
        try:
            di_str = request.form.get('data_inicio', '').strip()
            df_str = request.form.get('data_fim', '').strip()
            apac = APAC(
                paciente_id=int(request.form['paciente_id']),
                unidade_id=current_user.unidade_id,
                medico_id=request.form.get('medico_id') or None,
                numero_apac=request.form.get('numero_apac', '').strip() or None,
                tipo=request.form.get('tipo', 'inicial'),
                procedimento=request.form.get('procedimento', '').strip() or None,
                cid=request.form.get('cid', '').strip().upper() or None,
                competencia=request.form.get('competencia', '').strip() or None,
                data_inicio=datetime.strptime(di_str, '%Y-%m-%d').date() if di_str else None,
                data_fim=datetime.strptime(df_str, '%Y-%m-%d').date() if df_str else None,
                quantidade=int(request.form.get('quantidade', 1)),
                valor_total=float(request.form['valor_total']) if request.form.get('valor_total') else None,
                justificativa=request.form.get('justificativa', '').strip() or None,
                status=request.form.get('status', 'rascunho'),
            )
            db.session.add(apac)
            db.session.flush()
            registrar('apac', apac.id, 'create', f'APAC criada')
            db.session.commit()
            flash('APAC registrada!', 'success')
            return redirect(url_for('faturamento.apac_lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
    return render_template('faturamento/apac_form.html',
                           pacientes=pacientes, medicos=medicos,
                           comp_atual=date.today().strftime('%Y/%m'))
