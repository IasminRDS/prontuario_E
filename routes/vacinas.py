from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.vacina import Vacina, VacinaAplicada
from models.paciente import Paciente
from database.db import db
from utils.audit import registrar
from datetime import datetime, date

vacinas_bp = Blueprint('vacinas', __name__, url_prefix='/vacinas')


@vacinas_bp.route('/paciente/<int:paciente_id>')
@login_required
def cartao(paciente_id):
    paciente   = Paciente.query.get_or_404(paciente_id)
    aplicadas  = (VacinaAplicada.query
                  .filter_by(paciente_id=paciente_id)
                  .order_by(VacinaAplicada.data_aplicacao.desc())
                  .all())
    vacinas_ref = Vacina.query.filter_by(ativo=True).order_by(Vacina.nome).all()

    # Mapa vacina_id -> lista de doses aplicadas
    doses_por_vacina = {}
    for a in aplicadas:
        doses_por_vacina.setdefault(a.vacina_id, []).append(a)

    return render_template('vacinas/cartao.html',
                           paciente=paciente,
                           aplicadas=aplicadas,
                           vacinas_ref=vacinas_ref,
                           doses_por_vacina=doses_por_vacina)


@vacinas_bp.route('/paciente/<int:paciente_id>/registrar', methods=['GET', 'POST'])
@login_required
def registrar_dose(paciente_id):
    paciente    = Paciente.query.get_or_404(paciente_id)
    vacinas_ref = Vacina.query.filter_by(ativo=True).order_by(Vacina.nome).all()

    if request.method == 'POST':
        try:
            vacina_id   = int(request.form['vacina_id'])
            data_str    = request.form.get('data_aplicacao', '')
            data_aplic  = datetime.strptime(data_str, '%Y-%m-%d').date()

            # Número automático da dose
            doses_ant = VacinaAplicada.query.filter_by(
                paciente_id=paciente_id,
                vacina_id=vacina_id
            ).count()

            aplic = VacinaAplicada(
                paciente_id     = paciente_id,
                vacina_id       = vacina_id,
                unidade_id      = current_user.unidade_id,
                aplicado_por    = current_user.id,
                dose_numero     = doses_ant + 1,
                data_aplicacao  = data_aplic,
                lote            = request.form.get('lote', '').strip() or None,
                via             = request.form.get('via', '').strip() or None,
                local_aplicacao = request.form.get('local_aplicacao', '').strip() or None,
                observacoes     = request.form.get('observacoes', '').strip() or None,
            )
            db.session.add(aplic)
            db.session.flush()
            registrar('vacinas_aplicadas', aplic.id, 'create',
                      f'Dose {aplic.dose_numero} aplicada - vacina {vacina_id}')
            db.session.commit()
            flash('Dose registrada com sucesso!', 'success')
            return redirect(url_for('vacinas.cartao', paciente_id=paciente_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar dose: {e}', 'danger')

    return render_template('vacinas/form.html',
                           paciente=paciente,
                           vacinas_ref=vacinas_ref)


@vacinas_bp.route('/aplicacao/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_dose(id):
    aplic = VacinaAplicada.query.get_or_404(id)
    pid   = aplic.paciente_id
    registrar('vacinas_aplicadas', aplic.id, 'delete', 'Dose excluída')
    db.session.delete(aplic)
    db.session.commit()
    flash('Registro de dose removido.', 'info')
    return redirect(url_for('vacinas.cartao', paciente_id=pid))


# ── Admin: cadastro de vacinas de referência ──
@vacinas_bp.route('/catalogo')
@login_required
def catalogo():
    vacinas = Vacina.query.order_by(Vacina.nome).all()
    return render_template('vacinas/catalogo.html', vacinas=vacinas)


@vacinas_bp.route('/catalogo/novo', methods=['GET', 'POST'])
@login_required
def nova_vacina():
    if request.method == 'POST':
        try:
            v = Vacina(
                nome          = request.form.get('nome', '').strip(),
                sigla         = request.form.get('sigla', '').strip().upper() or None,
                fabricante    = request.form.get('fabricante', '').strip() or None,
                doses_total   = int(request.form.get('doses_total', 1)),
                intervalo_dias= int(request.form['intervalo_dias']) if request.form.get('intervalo_dias') else None,
                descricao     = request.form.get('descricao', '').strip() or None,
            )
            db.session.add(v)
            db.session.flush()
            registrar('vacinas', v.id, 'create', f'Vacina {v.nome} cadastrada')
            db.session.commit()
            flash(f'Vacina {v.nome} cadastrada!', 'success')
            return redirect(url_for('vacinas.catalogo'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')
    return render_template('vacinas/vacina_form.html', vacina=None)
