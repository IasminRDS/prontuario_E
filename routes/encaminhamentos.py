# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.encaminhamento import Encaminhamento
from models.paciente import Paciente
from models.medico import Medico
from database.db import db
from utils.audit import registrar
from utils.security import medico_requerido
from datetime import datetime

encaminhamentos_bp = Blueprint('encaminhamentos', __name__, url_prefix='/encaminhamentos')

ESPECIALIDADES = sorted([
    'Cardiologia', 'Dermatologia', 'Endocrinologia', 'Gastroenterologia',
    'Geriatria', 'Ginecologia e Obstetrícia', 'Hematologia', 'Infectologia',
    'Nefrologia', 'Neurologia', 'Oftalmologia', 'Oncologia', 'Ortopedia',
    'Otorrinolaringologia', 'Pediatria', 'Pneumologia', 'Psiquiatria',
    'Reumatologia', 'Urologia', 'Cirurgia Geral', 'Cirurgia Vascular',
    'Nutrição', 'Psicologia', 'Fisioterapia', 'Fonoaudiologia',
    'Serviço Social', 'CAPS', 'NASF', 'Centro de Especialidades',
])


@encaminhamentos_bp.route('/paciente/<int:paciente_id>')
@login_required
def lista_paciente(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    encaminhamentos = (Encaminhamento.query
                       .filter_by(paciente_id=paciente_id)
                       .order_by(Encaminhamento.data_solicitacao.desc())
                       .all())
    ativos    = [e for e in encaminhamentos if e.status in ('solicitado','agendado')]
    historico = [e for e in encaminhamentos if e.status in ('realizado','cancelado')]
    return render_template('encaminhamentos/lista.html',
                           paciente=paciente,
                           ativos=ativos, historico=historico)


@encaminhamentos_bp.route('/novo/<int:paciente_id>', methods=['GET', 'POST'])
@encaminhamentos_bp.route('/novo/<int:paciente_id>/<int:prontuario_id>', methods=['GET', 'POST'])
@login_required
@medico_requerido
def novo(paciente_id, prontuario_id=None):
    paciente = Paciente.query.get_or_404(paciente_id)
    medico   = Medico.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        try:
            data_ag_str = request.form.get('data_agendada', '').strip()
            data_ag = datetime.strptime(data_ag_str, '%Y-%m-%dT%H:%M') if data_ag_str else None

            enc = Encaminhamento(
                paciente_id       = paciente_id,
                prontuario_id     = prontuario_id,
                medico_id         = medico.id if medico else None,
                unidade_origem_id = current_user.unidade_id,
                especialidade     = request.form.get('especialidade', '').strip(),
                servico_destino   = request.form.get('servico_destino', '').strip() or None,
                prioridade        = request.form.get('prioridade', 'eletivo'),
                motivo            = request.form.get('motivo', '').strip(),
                hipotese_diagnostica = request.form.get('hipotese_diagnostica','').strip() or None,
                cid               = request.form.get('cid','').strip().upper() or None,
                data_agendada     = data_ag,
                observacoes       = request.form.get('observacoes','').strip() or None,
                criado_por        = current_user.id,
            )
            db.session.add(enc)
            db.session.flush()
            registrar('encaminhamentos', enc.id, 'create',
                      f'Encaminhamento {enc.especialidade} criado')
            db.session.commit()
            flash(f'Encaminhamento para {enc.especialidade} registrado!', 'success')
            return redirect(url_for('encaminhamentos.lista_paciente', paciente_id=paciente_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')

    return render_template('encaminhamentos/form.html',
                           paciente=paciente,
                           especialidades=ESPECIALIDADES,
                           prontuario_id=prontuario_id)


@encaminhamentos_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def atualizar_status(id):
    enc    = Encaminhamento.query.get_or_404(id)
    novo   = request.form.get('status')
    retorno= request.form.get('retorno_info', '').strip() or None

    if novo in Encaminhamento.STATUS_LABELS:
        enc.status = novo
        if novo == 'realizado':
            enc.data_realizacao = datetime.utcnow()
        if retorno:
            enc.retorno_info = retorno
        registrar('encaminhamentos', enc.id, 'update', f'Status → {novo}')
        db.session.commit()
        flash('Status atualizado!', 'success')
    return redirect(url_for('encaminhamentos.lista_paciente',
                            paciente_id=enc.paciente_id))


@encaminhamentos_bp.route('/<int:id>')
@login_required
def visualizar(id):
    enc = Encaminhamento.query.get_or_404(id)
    return render_template('encaminhamentos/visualizar.html', enc=enc)


@encaminhamentos_bp.route('/painel')
@login_required
def painel():
    """Visão geral de todos encaminhamentos ativos da unidade."""
    status   = request.args.get('status', '')
    esp      = request.args.get('especialidade', '')
    page     = request.args.get('page', 1, type=int)

    q = Encaminhamento.query.filter_by(
        unidade_origem_id=current_user.unidade_id)
    if status:
        q = q.filter(Encaminhamento.status == status)
    if esp:
        q = q.filter(Encaminhamento.especialidade.ilike(f'%{esp}%'))

    encaminhamentos = q.order_by(
        db.case(
            (Encaminhamento.prioridade == 'urgente',     1),
            (Encaminhamento.prioridade == 'prioritario', 2),
            else_=3),
        Encaminhamento.data_solicitacao.desc()
    ).paginate(page=page, per_page=30)

    return render_template('encaminhamentos/painel.html',
                           encaminhamentos=encaminhamentos,
                           especialidades=ESPECIALIDADES,
                           filtro_status=status,
                           filtro_esp=esp)
