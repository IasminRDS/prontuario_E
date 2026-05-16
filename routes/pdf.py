from flask import Blueprint, send_file, abort, request, render_template
from flask_login import login_required, current_user
from models.prontuario import Prontuario
from models.paciente import Paciente
from models.medico import Medico
from models.encaminhamento import Encaminhamento
from services.pdf_service import gerar_prontuario, gerar_receituario, gerar_atestado
from services.pdf_encaminhamento import gerar_encaminhamento
from utils.audit import registrar

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')


@pdf_bp.route('/prontuario/<int:id>')
@login_required
def prontuario(id):
    p = Prontuario.query.get_or_404(id)
    paciente = p.paciente
    medico   = p.medico
    unidade  = p.unidade
    buf = gerar_prontuario(p, paciente, medico, unidade)
    registrar('prontuarios', id, 'view', 'PDF prontuário gerado')
    nome = f'prontuario_{paciente.nome.split()[0].lower()}_{id}.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=False, download_name=nome)


@pdf_bp.route('/receituario/<int:id>')
@login_required
def receituario(id):
    p = Prontuario.query.get_or_404(id)
    if not p.prescricao:
        abort(400, 'Prontuário sem prescrição registrada.')
    paciente = p.paciente
    medico   = p.medico
    unidade  = p.unidade
    buf = gerar_receituario(p, paciente, medico, unidade)
    registrar('prontuarios', id, 'view', 'Receituário PDF gerado')
    nome = f'receituario_{paciente.nome.split()[0].lower()}_{id}.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=False, download_name=nome)


@pdf_bp.route('/atestado/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def atestado(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    medico   = Medico.query.filter_by(user_id=current_user.id).first()
    unidade  = current_user.unidade

    if request.method == 'POST':
        dias = int(request.form.get('dias', 1))
        cid  = request.form.get('cid', '').strip().upper() or None
        obs  = request.form.get('observacao', '').strip() or None
        buf  = gerar_atestado(paciente, medico, unidade, dias, cid, obs)
        registrar('pacientes', paciente_id, 'view', f'Atestado {dias}d gerado')
        nome = f'atestado_{paciente.nome.split()[0].lower()}.pdf'
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=False, download_name=nome)

    return render_template('pdf/atestado_form.html', paciente=paciente)


@pdf_bp.route('/encaminhamento/<int:id>')
@login_required
def encaminhamento(id):
    enc      = Encaminhamento.query.get_or_404(id)
    paciente = enc.paciente
    medico   = enc.medico
    unidade  = enc.unidade_origem
    buf = gerar_encaminhamento(enc, paciente, medico, unidade)
    registrar('encaminhamentos', id, 'view', 'PDF encaminhamento gerado')
    nome = f'encaminhamento_{enc.especialidade.lower().replace(" ","_")}_{id}.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=False, download_name=nome)
