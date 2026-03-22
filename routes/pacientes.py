from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.paciente import Paciente
from database.db import db
from datetime import datetime, date
from utils.security import perfil_requerido

pacientes_bp = Blueprint('pacientes', __name__, url_prefix='/pacientes')

@pacientes_bp.route('/')
@login_required
def index():
    q          = request.args.get('q', '').strip()
    sexo       = request.args.get('sexo', '')
    idade_min  = request.args.get('idade_min', '', type=str)
    idade_max  = request.args.get('idade_max', '', type=str)
    municipio  = request.args.get('municipio', '').strip()
    tem_cns    = request.args.get('tem_cns', '')
    page       = request.args.get('page', 1, type=int)

    from datetime import date
    from dateutil.relativedelta import relativedelta

    query = Paciente.query.filter_by(ativo=True)

    if q:
        query = query.filter(db.or_(
            Paciente.nome.ilike(f'%{q}%'),
            Paciente.cns.ilike(f'%{q}%'),
            Paciente.cpf.ilike(f'%{q}%'),
            Paciente.nome_mae.ilike(f'%{q}%'),
        ))
    if sexo:
        query = query.filter(Paciente.sexo == sexo)
    if municipio:
        query = query.filter(Paciente.municipio.ilike(f'%{municipio}%'))
    if tem_cns == '1':
        query = query.filter(Paciente.cns.isnot(None), Paciente.cns != '')
    elif tem_cns == '0':
        query = query.filter(db.or_(Paciente.cns.is_(None), Paciente.cns == ''))
    if idade_min:
        try:
            data_max = date.today() - relativedelta(years=int(idade_min))
            query = query.filter(Paciente.data_nascimento <= data_max)
        except Exception:
            pass
    if idade_max:
        try:
            data_min = date.today() - relativedelta(years=int(idade_max) + 1)
            query = query.filter(Paciente.data_nascimento >= data_min)
        except Exception:
            pass

    pacientes = query.order_by(Paciente.nome).paginate(page=page, per_page=20)
    tem_filtro = any([q, sexo, idade_min, idade_max, municipio, tem_cns])
    return render_template('pacientes/index.html',
                           pacientes=pacientes, q=q,
                           filtro_sexo=sexo, filtro_idade_min=idade_min,
                           filtro_idade_max=idade_max, filtro_municipio=municipio,
                           filtro_tem_cns=tem_cns, tem_filtro=tem_filtro)

@pacientes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            data_nasc_str = request.form.get('data_nascimento')
            data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None

            paciente = Paciente(
                nome=request.form.get('nome', '').strip().upper(),
                nome_social=request.form.get('nome_social', '').strip() or None,
                cns=request.form.get('cns', '').strip() or None,
                cpf=request.form.get('cpf', '').strip() or None,
                rg=request.form.get('rg', '').strip() or None,
                data_nascimento=data_nasc,
                sexo=request.form.get('sexo'),
                raca_cor=request.form.get('raca_cor') or None,
                nome_mae=request.form.get('nome_mae', '').strip().upper() or None,
                nome_pai=request.form.get('nome_pai', '').strip().upper() or None,
                telefone=request.form.get('telefone', '').strip() or None,
                telefone2=request.form.get('telefone2', '').strip() or None,
                email=request.form.get('email', '').strip().lower() or None,
                cep=request.form.get('cep', '').strip() or None,
                logradouro=request.form.get('logradouro', '').strip().upper() or None,
                numero=request.form.get('numero', '').strip() or None,
                complemento=request.form.get('complemento', '').strip() or None,
                bairro=request.form.get('bairro', '').strip().upper() or None,
                municipio=request.form.get('municipio', '').strip().upper() or None,
                uf=request.form.get('uf', '').strip().upper() or None,
                tipo_sanguineo=request.form.get('tipo_sanguineo') or None,
                alergias=request.form.get('alergias', '').strip() or None,
                observacoes=request.form.get('observacoes', '').strip() or None,
                criado_por=current_user.id
            )
            db.session.add(paciente)
            db.session.commit()
            flash(f'Paciente {paciente.nome} cadastrado com sucesso!', 'success')
            return redirect(url_for('pacientes.perfil', id=paciente.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar paciente: {str(e)}', 'danger')

    return render_template('pacientes/form.html', paciente=None)

@pacientes_bp.route('/<int:id>')
@login_required
def perfil(id):
    paciente = Paciente.query.get_or_404(id)
    atendimentos = paciente.atendimentos.order_by('data_hora').limit(10).all()
    prontuarios = paciente.prontuarios.order_by('criado_em').limit(10).all()
    return render_template('pacientes/perfil.html', paciente=paciente,
                           atendimentos=atendimentos, prontuarios=prontuarios)

@pacientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    paciente = Paciente.query.get_or_404(id)

    if request.method == 'POST':
        try:
            data_nasc_str = request.form.get('data_nascimento')
            paciente.data_nascimento = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else paciente.data_nascimento
            paciente.nome = request.form.get('nome', '').strip().upper()
            paciente.nome_social = request.form.get('nome_social', '').strip() or None
            paciente.cns = request.form.get('cns', '').strip() or None
            paciente.cpf = request.form.get('cpf', '').strip() or None
            paciente.telefone = request.form.get('telefone', '').strip() or None
            paciente.telefone2 = request.form.get('telefone2', '').strip() or None
            paciente.email = request.form.get('email', '').strip().lower() or None
            paciente.cep = request.form.get('cep', '').strip() or None
            paciente.logradouro = request.form.get('logradouro', '').strip().upper() or None
            paciente.numero = request.form.get('numero', '').strip() or None
            paciente.complemento = request.form.get('complemento', '').strip() or None
            paciente.bairro = request.form.get('bairro', '').strip().upper() or None
            paciente.municipio = request.form.get('municipio', '').strip().upper() or None
            paciente.uf = request.form.get('uf', '').strip().upper() or None
            paciente.tipo_sanguineo = request.form.get('tipo_sanguineo') or None
            paciente.alergias = request.form.get('alergias', '').strip() or None
            paciente.observacoes = request.form.get('observacoes', '').strip() or None
            paciente.atualizado_em = datetime.utcnow()
            db.session.commit()
            flash('Dados do paciente atualizados com sucesso!', 'success')
            return redirect(url_for('pacientes.perfil', id=paciente.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'danger')

    return render_template('pacientes/form.html', paciente=paciente)

@pacientes_bp.route('/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    pacientes = Paciente.query.filter(
        Paciente.ativo == True,
        db.or_(
            Paciente.nome.ilike(f'%{q}%'),
            Paciente.cns.ilike(f'%{q}%'),
            Paciente.cpf.ilike(f'%{q}%'),
        )
    ).limit(10).all()
    return jsonify([{
        'id': p.id,
        'nome': p.nome_exibicao,
        'cns': p.cns or '',
        'idade': p.idade,
        'data_nascimento': p.data_nascimento.strftime('%d/%m/%Y')
    } for p in pacientes])


@pacientes_bp.route('/qrscan')
@login_required
def qrscan():
    return render_template('pacientes/qrscan.html')


@pacientes_bp.route('/buscar-codigo')
@login_required
def buscar_codigo():
    """Busca paciente por CNS, CPF ou ID — usada pelo leitor de QR/código de barras."""
    q = request.args.get('q', '').strip().replace('.', '').replace('-', '').replace('/', '')
    if not q:
        return jsonify({'encontrado': False})

    pac = None
    # Tentar por CNS (15 dígitos)
    if q.isdigit() and len(q) == 15:
        pac = Paciente.query.filter_by(cns=q, ativo=True).first()
    # Tentar por CPF (11 dígitos)
    if not pac and q.isdigit() and len(q) == 11:
        pac = Paciente.query.filter_by(cpf=q, ativo=True).first()
    # Tentar por ID
    if not pac and q.isdigit():
        pac = Paciente.query.filter_by(id=int(q), ativo=True).first()
    # Busca ampla
    if not pac:
        pac = Paciente.query.filter(
            Paciente.ativo == True,
            db.or_(
                Paciente.cns == q,
                Paciente.cpf == q,
            )
        ).first()

    if not pac:
        return jsonify({'encontrado': False})

    return jsonify({
        'encontrado': True,
        'paciente': {
            'id':        pac.id,
            'nome':      pac.nome_exibicao,
            'cns':       pac.cns or '',
            'cpf':       pac.cpf or '',
            'idade':     pac.idade,
            'nascimento': pac.data_nascimento.strftime('%d/%m/%Y'),
            'sexo':      pac.sexo,
            'alergias':  pac.alergias or '',
        }
    })
