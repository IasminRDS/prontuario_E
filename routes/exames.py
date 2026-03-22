# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.exame import ExameSolicitado, TipoExame
from models.paciente import Paciente
from models.medico import Medico
from database.db import db
from utils.audit import registrar
from utils.security import medico_requerido
from datetime import datetime

exames_bp = Blueprint('exames', __name__, url_prefix='/exames')


@exames_bp.route('/paciente/<int:paciente_id>')
@login_required
def lista_paciente(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    exames   = (ExameSolicitado.query
                .filter_by(paciente_id=paciente_id)
                .order_by(ExameSolicitado.data_solicitacao.desc())
                .all())
    pendentes  = [e for e in exames if e.status not in ('resultado_disponivel','cancelado')]
    concluidos = [e for e in exames if e.status == 'resultado_disponivel']
    return render_template('exames/lista.html',
                           paciente=paciente, exames=exames,
                           pendentes=pendentes, concluidos=concluidos)


@exames_bp.route('/solicitar/<int:paciente_id>', methods=['GET', 'POST'])
@exames_bp.route('/solicitar/<int:paciente_id>/<int:prontuario_id>', methods=['GET', 'POST'])
@login_required
@medico_requerido
def solicitar(paciente_id, prontuario_id=None):
    paciente   = Paciente.query.get_or_404(paciente_id)
    tipos      = TipoExame.query.filter_by(ativo=True).order_by(TipoExame.nome).all()
    medico     = Medico.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        tipo_ids = request.form.getlist('tipo_exame_ids')
        if not tipo_ids:
            flash('Selecione pelo menos um exame.', 'warning')
        else:
            try:
                urgencia  = request.form.get('urgencia', 'rotina')
                indicacao = request.form.get('indicacao_clinica', '').strip() or None
                obs       = request.form.get('observacoes', '').strip() or None

                for tid in tipo_ids:
                    e = ExameSolicitado(
                        paciente_id       = paciente_id,
                        prontuario_id     = prontuario_id,
                        medico_id         = medico.id if medico else None,
                        unidade_id        = current_user.unidade_id,
                        tipo_exame_id     = int(tid),
                        urgencia          = urgencia,
                        indicacao_clinica = indicacao,
                        observacoes       = obs,
                        criado_por        = current_user.id,
                    )
                    db.session.add(e)
                    db.session.flush()
                    registrar('exames_solicitados', e.id, 'create',
                              f'Exame {tid} solicitado para paciente {paciente_id}')

                db.session.commit()
                flash(f'{len(tipo_ids)} exame(s) solicitado(s) com sucesso!', 'success')
                return redirect(url_for('exames.lista_paciente', paciente_id=paciente_id))
            except Exception as ex:
                db.session.rollback()
                flash(f'Erro: {ex}', 'danger')

    categorias = {}
    for t in tipos:
        categorias.setdefault(t.categoria or 'outro', []).append(t)

    return render_template('exames/solicitar.html',
                           paciente=paciente,
                           categorias=categorias,
                           prontuario_id=prontuario_id)


@exames_bp.route('/<int:id>/resultado', methods=['GET', 'POST'])
@login_required
def registrar_resultado(id):
    exame = ExameSolicitado.query.get_or_404(id)

    if request.method == 'POST':
        try:
            exame.resultado_texto   = request.form.get('resultado_texto', '').strip() or None
            exame.resultado_valor   = request.form.get('resultado_valor', '').strip() or None
            exame.resultado_unidade = request.form.get('resultado_unidade', '').strip() or None
            exame.valor_referencia  = request.form.get('valor_referencia', '').strip() or None
            exame.interpretacao     = request.form.get('interpretacao', '') or None
            exame.status            = 'resultado_disponivel'
            exame.data_resultado    = datetime.utcnow()
            registrar('exames_solicitados', exame.id, 'update',
                      f'Resultado registrado — {exame.interpretacao or "sem interpretação"}')
            db.session.commit()
            flash('Resultado registrado com sucesso!', 'success')
            return redirect(url_for('exames.lista_paciente',
                                    paciente_id=exame.paciente_id))
        except Exception as ex:
            db.session.rollback()
            flash(f'Erro: {ex}', 'danger')

    return render_template('exames/resultado.html', exame=exame)


@exames_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    exame = ExameSolicitado.query.get_or_404(id)
    exame.status = 'cancelado'
    registrar('exames_solicitados', id, 'delete', 'Exame cancelado')
    db.session.commit()
    flash('Exame cancelado.', 'info')
    return redirect(url_for('exames.lista_paciente', paciente_id=exame.paciente_id))


# ── Catálogo de tipos de exame ──
@exames_bp.route('/catalogo')
@login_required
def catalogo():
    tipos = TipoExame.query.order_by(TipoExame.categoria, TipoExame.nome).all()
    return render_template('exames/catalogo.html', tipos=tipos)


@exames_bp.route('/catalogo/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo():
    if request.method == 'POST':
        try:
            t = TipoExame(
                codigo    = request.form.get('codigo', '').strip().upper(),
                nome      = request.form.get('nome', '').strip(),
                categoria = request.form.get('categoria', 'laboratorial'),
                instrucoes= request.form.get('instrucoes', '').strip() or None,
            )
            db.session.add(t)
            db.session.flush()
            registrar('tipos_exame', t.id, 'create', f'Tipo exame {t.codigo} criado')
            db.session.commit()
            flash(f'Exame {t.nome} cadastrado!', 'success')
            return redirect(url_for('exames.catalogo'))
        except Exception as ex:
            db.session.rollback()
            flash(f'Erro: {ex}', 'danger')
    return render_template('exames/tipo_form.html')


# ── Fila de resultados pendentes (visão geral) ──
@exames_bp.route('/pendentes')
@login_required
def pendentes():
    exames = (ExameSolicitado.query
              .filter(ExameSolicitado.status.in_(['solicitado','coletado','em_analise']),
                      ExameSolicitado.unidade_id == current_user.unidade_id)
              .order_by(
                  db.case(
                      (ExameSolicitado.urgencia == 'urgentissimo', 1),
                      (ExameSolicitado.urgencia == 'urgente', 2),
                      else_=3),
                  ExameSolicitado.data_solicitacao
              ).all())
    return render_template('exames/pendentes.html', exames=exames)
