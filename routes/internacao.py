# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.internacao import Setor, Leito, Internacao, EvolucaoInternacao
from models.paciente import Paciente
from models.medico import Medico
from database.db import db
from utils.audit import registrar
from datetime import datetime

internacao_bp = Blueprint('internacao', __name__, url_prefix='/internacao')


# ── Painel de leitos ──
@internacao_bp.route('/')
@login_required
def painel():
    setores  = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()
    total    = Leito.query.filter_by(ativo=True).count()
    ocupados = Leito.query.filter_by(status='ocupado', ativo=True).count()
    livres   = Leito.query.filter_by(status='livre', ativo=True).count()
    higieniz = Leito.query.filter_by(status='em_higienizacao', ativo=True).count()

    internacoes_ativas = Internacao.query.filter_by(
        status='ativa').order_by(Internacao.data_entrada).all()

    return render_template('internacao/painel.html',
                           setores=setores,
                           total=total, ocupados=ocupados,
                           livres=livres, higieniz=higieniz,
                           internacoes_ativas=internacoes_ativas)


# ── Nova internação ──
@internacao_bp.route('/nova', methods=['GET', 'POST'])
@internacao_bp.route('/nova/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def nova(paciente_id=None):
    pacientes = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
    medicos   = Medico.query.all()
    leitos_livres = (Leito.query
                     .filter_by(status='livre', ativo=True)
                     .join(Setor)
                     .filter_by(ativo=True)
                     .order_by(Setor.nome, Leito.numero)
                     .all())

    if request.method == 'POST':
        try:
            leito_id = int(request.form['leito_id'])
            leito    = Leito.query.get_or_404(leito_id)

            data_prevista = None
            dp = request.form.get('data_prevista_alta', '').strip()
            if dp:
                data_prevista = datetime.strptime(dp, '%Y-%m-%dT%H:%M')

            intern = Internacao(
                paciente_id        = int(request.form['paciente_id']),
                leito_id           = leito_id,
                medico_id          = request.form.get('medico_id') or None,
                unidade_id         = current_user.unidade_id,
                tipo               = request.form.get('tipo', 'clinica'),
                motivo             = request.form.get('motivo', '').strip(),
                hipotese_diag      = request.form.get('hipotese_diag', '').strip() or None,
                cid_principal      = request.form.get('cid_principal', '').strip().upper() or None,
                data_prevista_alta = data_prevista,
                aih_numero         = request.form.get('aih_numero', '').strip() or None,
                observacoes        = request.form.get('observacoes', '').strip() or None,
                criado_por         = current_user.id,
            )
            db.session.add(intern)
            db.session.flush()

            # Atualizar status do leito
            leito.status = 'ocupado'

            registrar('internacoes', intern.id, 'create',
                      f'Internação criada — leito {leito.numero}')
            db.session.commit()
            flash(f'Paciente internado no leito {leito.numero}!', 'success')
            return redirect(url_for('internacao.visualizar', id=intern.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao internar: {e}', 'danger')

    paciente_sel = Paciente.query.get(paciente_id) if paciente_id else None
    return render_template('internacao/form.html',
                           pacientes=pacientes, medicos=medicos,
                           leitos_livres=leitos_livres,
                           paciente_sel=paciente_sel)


# ── Visualizar internação ──
@internacao_bp.route('/<int:id>')
@login_required
def visualizar(id):
    intern   = Internacao.query.get_or_404(id)
    evolucoes = intern.evolucoes.order_by(EvolucaoInternacao.criado_em.desc()).all()
    prescricoes = intern.prescricoes_hosp
    cirurgias   = intern.cirurgias
    return render_template('internacao/visualizar.html',
                           intern=intern, evolucoes=evolucoes,
                           prescricoes=prescricoes, cirurgias=cirurgias)


# ── Evolução diária ──
@internacao_bp.route('/<int:id>/evolucao', methods=['GET', 'POST'])
@login_required
def nova_evolucao(id):
    intern = Internacao.query.get_or_404(id)

    if request.method == 'POST':
        try:
            ev = EvolucaoInternacao(
                internacao_id        = id,
                profissional_id      = current_user.id,
                tipo                 = request.form.get('tipo', 'medica'),
                pressao_arterial     = request.form.get('pressao_arterial', '').strip() or None,
                temperatura          = float(request.form['temperatura']) if request.form.get('temperatura') else None,
                frequencia_cardiaca  = int(request.form['frequencia_cardiaca']) if request.form.get('frequencia_cardiaca') else None,
                frequencia_respiratoria = int(request.form['frequencia_respiratoria']) if request.form.get('frequencia_respiratoria') else None,
                saturacao_o2         = float(request.form['saturacao_o2']) if request.form.get('saturacao_o2') else None,
                diurese_ml           = int(request.form['diurese_ml']) if request.form.get('diurese_ml') else None,
                balanco_hidrico      = int(request.form['balanco_hidrico']) if request.form.get('balanco_hidrico') else None,
                subjetivo            = request.form.get('subjetivo', '').strip() or None,
                objetivo             = request.form.get('objetivo', '').strip() or None,
                avaliacao            = request.form.get('avaliacao', '').strip() or None,
                plano                = request.form.get('plano', '').strip() or None,
            )
            db.session.add(ev)
            registrar('internacoes', id, 'update', 'Evolução registrada')
            db.session.commit()
            flash('Evolução registrada!', 'success')
            return redirect(url_for('internacao.visualizar', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')

    return render_template('internacao/evolucao_form.html', intern=intern)


# ── Alta ──
@internacao_bp.route('/<int:id>/alta', methods=['GET', 'POST'])
@login_required
def alta(id):
    intern = Internacao.query.get_or_404(id)

    if request.method == 'POST':
        try:
            intern.status       = 'alta'
            intern.data_alta    = datetime.utcnow()
            intern.tipo_alta    = request.form.get('tipo_alta', 'curado')
            intern.sumario_alta = request.form.get('sumario_alta', '').strip() or None
            intern.cid_alta     = request.form.get('cid_alta', '').strip().upper() or None
            intern.leito.status = 'em_higienizacao'
            registrar('internacoes', id, 'update',
                      f'Alta {intern.tipo_alta} — {intern.dias_internado} dias')
            db.session.commit()
            flash('Alta registrada com sucesso!', 'success')
            return redirect(url_for('internacao.painel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')

    return render_template('internacao/alta_form.html', intern=intern)


# ── Gestão de leitos e setores ──
@internacao_bp.route('/leitos')
@login_required
def leitos():
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()
    return render_template('internacao/leitos.html', setores=setores)


@internacao_bp.route('/leitos/<int:id>/status', methods=['POST'])
@login_required
def atualizar_leito(id):
    leito = Leito.query.get_or_404(id)
    novo  = request.form.get('status')
    if novo in Leito.STATUS_LABELS and leito.status != 'ocupado':
        leito.status = novo
        registrar('leitos', id, 'update', f'Status leito → {novo}')
        db.session.commit()
    return redirect(url_for('internacao.leitos'))


@internacao_bp.route('/setores/novo', methods=['GET', 'POST'])
@login_required
def novo_setor():
    if request.method == 'POST':
        try:
            s = Setor(
                nome        = request.form.get('nome', '').strip(),
                sigla       = request.form.get('sigla', '').strip().upper() or None,
                tipo        = request.form.get('tipo', 'enfermaria'),
                andar       = request.form.get('andar', '').strip() or None,
                responsavel = request.form.get('responsavel', '').strip() or None,
            )
            db.session.add(s)
            db.session.flush()

            # Criar leitos automaticamente
            qtd = int(request.form.get('qtd_leitos', 0))
            prefixo = s.sigla or s.nome[:3].upper()
            for i in range(1, qtd + 1):
                l = Leito(setor_id=s.id,
                          numero=f'{prefixo}-{i:02d}',
                          tipo=request.form.get('tipo_leito', 'comum'))
                db.session.add(l)

            db.session.commit()
            flash(f'Setor {s.nome} criado com {qtd} leito(s)!', 'success')
            return redirect(url_for('internacao.leitos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}', 'danger')

    return render_template('internacao/setor_form.html')


# ── API ──
@internacao_bp.route('/api/leitos')
@login_required
def api_leitos():
    setores = Setor.query.filter_by(ativo=True).all()
    return jsonify([{
        'setor': s.nome,
        'total': s.total_leitos,
        'ocupados': s.leitos_ocupados,
        'livres': s.leitos_livres,
        'taxa': s.taxa_ocupacao,
    } for s in setores])
