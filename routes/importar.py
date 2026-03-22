# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.paciente import Paciente
from database.db import db
from utils.audit import registrar
import csv
import io
from datetime import datetime

importar_bp = Blueprint('importar', __name__, url_prefix='/importar')

COLUNAS_OBRIGATORIAS = {'nome', 'data_nascimento', 'sexo'}
COLUNAS_ACEITAS = {
    'nome', 'nome_social', 'cns', 'cpf', 'rg', 'data_nascimento', 'sexo',
    'raca_cor', 'nome_mae', 'nome_pai', 'telefone', 'telefone2', 'email',
    'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'municipio', 'uf',
    'tipo_sanguineo', 'alergias', 'observacoes'
}


@importar_bp.route('/pacientes', methods=['GET', 'POST'])
@login_required
def pacientes():
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        if not arquivo or not arquivo.filename.endswith('.csv'):
            flash('Envie um arquivo .csv válido.', 'danger')
            return redirect(url_for('importar.pacientes'))

        try:
            conteudo = arquivo.read().decode('utf-8-sig')
            reader   = csv.DictReader(io.StringIO(conteudo))
            colunas  = set(c.strip().lower() for c in reader.fieldnames or [])

            faltando = COLUNAS_OBRIGATORIAS - colunas
            if faltando:
                flash(f'Colunas obrigatórias ausentes: {", ".join(faltando)}', 'danger')
                return redirect(url_for('importar.pacientes'))

            inseridos = 0
            ignorados = 0
            erros     = []

            for i, row in enumerate(reader, start=2):
                row = {k.strip().lower(): v.strip() for k, v in row.items()}
                try:
                    # Verificar duplicata por CNS ou CPF
                    cns = row.get('cns', '').strip() or None
                    cpf = row.get('cpf', '').strip() or None
                    if cns and Paciente.query.filter_by(cns=cns).first():
                        ignorados += 1
                        continue
                    if cpf and Paciente.query.filter_by(cpf=cpf).first():
                        ignorados += 1
                        continue

                    # Parsear data
                    data_nasc_str = row.get('data_nascimento', '')
                    data_nasc = None
                    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                        try:
                            data_nasc = datetime.strptime(data_nasc_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    if not data_nasc:
                        erros.append(f'Linha {i}: data_nascimento inválida ({data_nasc_str})')
                        continue

                    sexo = row.get('sexo', '').strip().upper()
                    if sexo not in ('M', 'F', 'I'):
                        sexo = 'I'

                    p = Paciente(
                        nome          = row.get('nome', '').strip().upper(),
                        nome_social   = row.get('nome_social', '').strip() or None,
                        cns           = cns,
                        cpf           = cpf,
                        rg            = row.get('rg', '').strip() or None,
                        data_nascimento = data_nasc,
                        sexo          = sexo,
                        raca_cor      = row.get('raca_cor', '').strip() or None,
                        nome_mae      = row.get('nome_mae', '').strip().upper() or None,
                        nome_pai      = row.get('nome_pai', '').strip().upper() or None,
                        telefone      = row.get('telefone', '').strip() or None,
                        telefone2     = row.get('telefone2', '').strip() or None,
                        email         = row.get('email', '').strip().lower() or None,
                        cep           = row.get('cep', '').strip() or None,
                        logradouro    = row.get('logradouro', '').strip().upper() or None,
                        numero        = row.get('numero', '').strip() or None,
                        complemento   = row.get('complemento', '').strip() or None,
                        bairro        = row.get('bairro', '').strip().upper() or None,
                        municipio     = row.get('municipio', '').strip().upper() or None,
                        uf            = row.get('uf', '').strip().upper() or None,
                        tipo_sanguineo= row.get('tipo_sanguineo', '').strip() or None,
                        alergias      = row.get('alergias', '').strip() or None,
                        observacoes   = row.get('observacoes', '').strip() or None,
                        criado_por    = current_user.id,
                    )
                    db.session.add(p)
                    inseridos += 1

                except Exception as e:
                    erros.append(f'Linha {i}: {e}')

            db.session.commit()
            registrar('pacientes', None, 'create',
                      f'Importação CSV: {inseridos} inseridos, {ignorados} ignorados, {len(erros)} erros')

            if inseridos:
                flash(f'{inseridos} paciente(s) importado(s) com sucesso!', 'success')
            if ignorados:
                flash(f'{ignorados} registro(s) ignorado(s) por duplicata (CNS/CPF já existente).', 'warning')
            if erros:
                flash(f'{len(erros)} erro(s) encontrado(s). Veja os detalhes abaixo.', 'danger')
                return render_template('importar/resultado.html',
                                       inseridos=inseridos, ignorados=ignorados, erros=erros)

            return redirect(url_for('pacientes.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar arquivo: {e}', 'danger')

    return render_template('importar/pacientes.html')


@importar_bp.route('/pacientes/modelo')
@login_required
def modelo_csv():
    """Baixa um CSV de exemplo com as colunas aceitas."""
    linhas = [
        ','.join(['nome','data_nascimento','sexo','cns','cpf','raca_cor',
                  'nome_mae','telefone','municipio','uf','alergias']),
        'MARIA DA SILVA,01/01/1980,F,123456789012345,123.456.789-00,Parda,'
        'ANA DA SILVA,(77) 99999-9999,BOM JESUS DA LAPA,BA,',
        'JOÃO SOUZA,15/06/1995,M,,,Branca,,,(77) 88888-8888,BARREIRAS,BA,Dipirona',
    ]
    conteudo = '\n'.join(linhas)
    return send_file(
        io.BytesIO(conteudo.encode('utf-8-sig')),
        mimetype='text/csv', as_attachment=True,
        download_name='modelo_importacao_pacientes.csv'
    )


from flask import send_file
