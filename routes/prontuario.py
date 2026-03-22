from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.prontuario import Prontuario
from models.paciente import Paciente
from models.medico import Medico
from models.atendimento import Atendimento
from database.db import db
from datetime import datetime
from utils.security import medico_requerido

prontuario_bp = Blueprint('prontuario', __name__, url_prefix='/prontuario')

@prontuario_bp.route('/paciente/<int:paciente_id>')
@login_required
def historico(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    prontuarios = Prontuario.query.filter_by(paciente_id=paciente_id)\
        .order_by(Prontuario.criado_em.desc()).all()
    return render_template('prontuario/historico.html', paciente=paciente, prontuarios=prontuarios)

@prontuario_bp.route('/novo/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
@medico_requerido
def novo(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    medico = Medico.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        try:
            # Criar atendimento vinculado
            atendimento = Atendimento(
                paciente_id=paciente_id,
                medico_id=medico.id if medico else None,
                unidade_id=current_user.unidade_id,
                tipo=request.form.get('tipo_atendimento', 'consulta'),
                status='finalizado',
                queixa_principal=request.form.get('subjetivo', '')[:200],
                criado_por=current_user.id
            )
            db.session.add(atendimento)
            db.session.flush()

            prontuario = Prontuario(
                paciente_id=paciente_id,
                atendimento_id=atendimento.id,
                medico_id=medico.id if medico else None,
                unidade_id=current_user.unidade_id,
                subjetivo=request.form.get('subjetivo', '').strip(),
                objetivo=request.form.get('objetivo', '').strip(),
                avaliacao=request.form.get('avaliacao', '').strip(),
                plano=request.form.get('plano', '').strip(),
                pressao_arterial=request.form.get('pressao_arterial', '').strip() or None,
                temperatura=float(request.form.get('temperatura')) if request.form.get('temperatura') else None,
                frequencia_cardiaca=int(request.form.get('frequencia_cardiaca')) if request.form.get('frequencia_cardiaca') else None,
                frequencia_respiratoria=int(request.form.get('frequencia_respiratoria')) if request.form.get('frequencia_respiratoria') else None,
                saturacao_o2=float(request.form.get('saturacao_o2')) if request.form.get('saturacao_o2') else None,
                peso=float(request.form.get('peso')) if request.form.get('peso') else None,
                altura=float(request.form.get('altura')) if request.form.get('altura') else None,
                glicemia=float(request.form.get('glicemia')) if request.form.get('glicemia') else None,
                cid_principal=request.form.get('cid_principal', '').strip().upper() or None,
                cid_secundario=request.form.get('cid_secundario', '').strip().upper() or None,
                prescricao=request.form.get('prescricao', '').strip() or None,
                encaminhamento=request.form.get('encaminhamento', '').strip() or None,
                retorno_dias=int(request.form.get('retorno_dias')) if request.form.get('retorno_dias') else None,
            )

            if 'assinar' in request.form:
                prontuario.assinar()

            db.session.add(prontuario)
            db.session.commit()
            flash('Prontuário registrado com sucesso!', 'success')
            return redirect(url_for('prontuario.visualizar', id=prontuario.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar prontuário: {str(e)}', 'danger')

    return render_template('prontuario/form.html', paciente=paciente, prontuario=None)

@prontuario_bp.route('/<int:id>')
@login_required
def visualizar(id):
    prontuario = Prontuario.query.get_or_404(id)
    paciente = prontuario.paciente
    return render_template('prontuario/visualizar.html', prontuario=prontuario, paciente=paciente)

@prontuario_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@medico_requerido
def editar(id):
    prontuario = Prontuario.query.get_or_404(id)
    paciente = prontuario.paciente

    if prontuario.assinado:
        flash('Prontuário já assinado não pode ser editado.', 'warning')
        return redirect(url_for('prontuario.visualizar', id=prontuario.id))

    if request.method == 'POST':
        try:
            prontuario.subjetivo = request.form.get('subjetivo', '').strip()
            prontuario.objetivo = request.form.get('objetivo', '').strip()
            prontuario.avaliacao = request.form.get('avaliacao', '').strip()
            prontuario.plano = request.form.get('plano', '').strip()
            prontuario.pressao_arterial = request.form.get('pressao_arterial') or None
            prontuario.temperatura = float(request.form.get('temperatura')) if request.form.get('temperatura') else None
            prontuario.frequencia_cardiaca = int(request.form.get('frequencia_cardiaca')) if request.form.get('frequencia_cardiaca') else None
            prontuario.peso = float(request.form.get('peso')) if request.form.get('peso') else None
            prontuario.altura = float(request.form.get('altura')) if request.form.get('altura') else None
            prontuario.cid_principal = request.form.get('cid_principal', '').upper() or None
            prontuario.prescricao = request.form.get('prescricao') or None
            prontuario.encaminhamento = request.form.get('encaminhamento') or None
            prontuario.atualizado_em = datetime.utcnow()

            if 'assinar' in request.form:
                prontuario.assinar()

            db.session.commit()
            flash('Prontuário atualizado!', 'success')
            return redirect(url_for('prontuario.visualizar', id=prontuario.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')

    return render_template('prontuario/form.html', paciente=paciente, prontuario=prontuario)
