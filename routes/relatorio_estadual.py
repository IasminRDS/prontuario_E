# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, send_file, flash, abort, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.unidade import Unidade
from models.paciente import Paciente
from models.atendimento import Atendimento
from models.internacao import Internacao, Leito, Setor
from models.cirurgia import Cirurgia
from models.pronto_socorro import AtendimentoPS
from models.transferencia import TransferenciaPaciente
from database.db import db
from datetime import datetime, date, timedelta
from io import BytesIO, StringIO
import csv

rel_estadual_bp = Blueprint('rel_estadual', __name__, url_prefix='/relatorios/estadual')


def _requer_gestor():
    return current_user.pode_ver_estadual()


@rel_estadual_bp.route('/')
@login_required
def index():
    if not _requer_gestor():
        abort(403)
    return render_template('relatorio_estadual/index.html')


@rel_estadual_bp.route('/painel')
@login_required
def painel():
    """Dashboard em tempo real com indicadores da rede estadual"""
    if not _requer_gestor():
        abort(403)
    
    # Dados de hoje
    hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoje_fim = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Dados de ontem para comparação
    ontem_inicio = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    ontem_fim = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    
    unidades = Unidade.query.filter_by(ativo=True).all()
    
    # INDICADORES GERAIS
    atend_hoje = Atendimento.query.filter(Atendimento.data_hora.between(hoje_inicio, hoje_fim)).count()
    atend_ontem = Atendimento.query.filter(Atendimento.data_hora.between(ontem_inicio, ontem_fim)).count()
    
    intern_ativas = Internacao.query.filter_by(status='ativa').count()
    altas_hoje = Internacao.query.filter(Internacao.data_alta.between(hoje_inicio, hoje_fim), 
                                         Internacao.status=='alta').count()
    obitos_hoje = Internacao.query.filter(Internacao.data_alta.between(hoje_inicio, hoje_fim), 
                                          Internacao.status=='obito').count()
    
    cir_agendadas = Cirurgia.query.filter(Cirurgia.status.in_(['agendada', 'confirmada'])).count()
    cir_realizadas_hoje = Cirurgia.query.filter(Cirurgia.data_agendada.between(hoje_inicio, hoje_fim),
                                                 Cirurgia.status=='realizada').count()
    
    ps_hoje = AtendimentoPS.query.filter(AtendimentoPS.data_entrada.between(hoje_inicio, hoje_fim)).count()
    
    transf_pendentes = TransferenciaPaciente.query.filter(
        TransferenciaPaciente.status.in_(['solicitada', 'aceita', 'em_transito'])).count()
    
    # TAXA DE OCUPAÇÃO - SEM FILTRO DE UNIDADE (total geral)
    total_leitos = Leito.query.filter_by(ativo=True).count()
    leitos_ocupados = Leito.query.filter_by(ativo=True, status='ocupado').count()
    taxa_ocupacao = round((leitos_ocupados / total_leitos * 100) if total_leitos else 0)
    
    # Classificar status ocupação
    if taxa_ocupacao >= 90:
        status_ocupacao = 'critica'
        cor_ocupacao = 'var(--sus-vermelho)'
    elif taxa_ocupacao >= 70:
        status_ocupacao = 'alta'
        cor_ocupacao = 'var(--sus-amarelo)'
    else:
        status_ocupacao = 'normal'
        cor_ocupacao = 'var(--sus-verde)'
    
    # DADOS POR UNIDADE
    unidades_dados = []
    for u in unidades:
        try:
            u_intern = Internacao.query.filter_by(unidade_id=u.id, status='ativa').count()
            u_leitos = Leito.query.filter_by(ativo=True).count()  # Total geral
            u_leitos_ocu = Leito.query.filter_by(ativo=True, status='ocupado').count()  # Total geral
            u_taxa = round((u_leitos_ocu / u_leitos * 100) if u_leitos else 0)
            u_atend = Atendimento.query.filter(Atendimento.data_hora.between(hoje_inicio, hoje_fim),
                                               Atendimento.unidade_id==u.id).count()
            
            unidades_dados.append({
                'id': u.id,
                'nome': u.nome,
                'municipio': u.municipio or '—',
                'internacoes': u_intern,
                'leitos_total': u_leitos,
                'leitos_ocupados': u_leitos_ocu,
                'taxa_ocupacao': u_taxa,
                'atendimentos': u_atend,
            })
        except Exception as e:
            # Se houver erro, continua para próxima unidade
            continue
    
    # Ordenar por taxa de ocupação (maiores primeiro)
    unidades_dados.sort(key=lambda x: x['taxa_ocupacao'], reverse=True)
    
    # COMPARATIVO
    variacao_atend = ((atend_hoje - atend_ontem) / atend_ontem * 100) if atend_ontem > 0 else 0
    
    return render_template('relatorio_estadual/painel.html',
                           atend_hoje=atend_hoje,
                           atend_ontem=atend_ontem,
                           variacao_atend=variacao_atend,
                           intern_ativas=intern_ativas,
                           altas_hoje=altas_hoje,
                           obitos_hoje=obitos_hoje,
                           cir_agendadas=cir_agendadas,
                           cir_realizadas_hoje=cir_realizadas_hoje,
                           ps_hoje=ps_hoje,
                           transf_pendentes=transf_pendentes,
                           total_leitos=total_leitos,
                           leitos_ocupados=leitos_ocupados,
                           taxa_ocupacao=taxa_ocupacao,
                           status_ocupacao=status_ocupacao,
                           cor_ocupacao=cor_ocupacao,
                           unidades_dados=unidades_dados)


@rel_estadual_bp.route('/consolidado')
@login_required
def consolidado():
    if not _requer_gestor():
        abort(403)

    data_ini = request.args.get('data_ini', date.today().replace(day=1).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))
    exportar = request.args.get('exportar', '')

    try:
        di = datetime.strptime(data_ini, '%Y-%m-%d')
        df = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59)
    except ValueError:
        di = datetime.now().replace(day=1)
        df = datetime.now()

    unidades = Unidade.query.filter_by(ativo=True).order_by(
        Unidade.municipio, Unidade.nome).all()

    dados = []
    for u in unidades:
        uid = u.id
        at      = Atendimento.query.filter(Atendimento.data_hora.between(di, df)).count()
        intern  = Internacao.query.filter(Internacao.data_entrada.between(di, df), Internacao.unidade_id==uid).count()
        altas   = Internacao.query.filter(Internacao.data_alta.between(di, df), Internacao.unidade_id==uid, Internacao.status=='alta').count()
        obitos  = Internacao.query.filter(Internacao.data_alta.between(di, df), Internacao.unidade_id==uid, Internacao.status=='obito').count()
        cir     = Cirurgia.query.filter(Cirurgia.data_agendada.between(di, df), Cirurgia.unidade_id==uid, Cirurgia.status=='realizada').count()
        ps_tot  = AtendimentoPS.query.filter(AtendimentoPS.data_entrada.between(di, df), AtendimentoPS.unidade_id==uid).count()
        transf_e= TransferenciaPaciente.query.filter(TransferenciaPaciente.data_solicitacao.between(di, df), TransferenciaPaciente.unidade_origem_id==uid).count()
        transf_r= TransferenciaPaciente.query.filter(TransferenciaPaciente.data_solicitacao.between(di, df), TransferenciaPaciente.unidade_destino_id==uid).count()
        
        t_leitos = Leito.query.filter_by(ativo=True).count()
        o_leitos = Leito.query.filter_by(ativo=True, status='ocupado').count()
        taxa = round(o_leitos / t_leitos * 100) if t_leitos else 0

        dados.append({
            'unidade':    u.nome,
            'municipio':  u.municipio or '—',
            'tipo':       u.tipo or '—',
            'atendimentos': at,
            'internacoes':  intern,
            'altas':        altas,
            'obitos':       obitos,
            'cirurgias':    cir,
            'ps':           ps_tot,
            'transf_env':   transf_e,
            'transf_rec':   transf_r,
            'taxa_ocu':     taxa,
            'leitos_total': t_leitos,
        })

    totais = {k: sum(d[k] for d in dados)
              for k in ['atendimentos','internacoes','altas','obitos',
                        'cirurgias','ps','transf_env','transf_rec','leitos_total']}
    totais['municipio'] = f'{len(set(d["municipio"] for d in dados))} municípios'
    totais['unidade']   = f'{len(dados)} unidades'
    totais['tipo']      = '—'
    totais['taxa_ocu']  = round(sum(d['taxa_ocu'] for d in dados) / len(dados)) if dados else 0

    if exportar == 'csv':
        try:
            return _exportar_csv(dados, totais, data_ini, data_fim)
        except Exception as e:
            flash(f'Erro ao exportar CSV: {str(e)}', 'danger')
            return render_template('relatorio_estadual/consolidado.html',
                                   dados=dados, totais=totais,
                                   data_ini=data_ini, data_fim=data_fim)

    if exportar == 'pdf':
        try:
            return _gerar_pdf_consolidado(dados, totais, data_ini, data_fim)
        except ImportError:
            flash('Biblioteca reportlab não instalada. Para gerar PDFs, instale: pip install reportlab', 'danger')
            return render_template('relatorio_estadual/consolidado.html',
                                   dados=dados, totais=totais,
                                   data_ini=data_ini, data_fim=data_fim)
        except Exception as e:
            flash(f'Erro ao exportar PDF: {str(e)}', 'danger')
            return render_template('relatorio_estadual/consolidado.html',
                                   dados=dados, totais=totais,
                                   data_ini=data_ini, data_fim=data_fim)

    return render_template('relatorio_estadual/consolidado.html',
                           dados=dados, totais=totais,
                           data_ini=data_ini, data_fim=data_fim)


def _exportar_csv(dados, totais, data_ini, data_fim):
    buf = StringIO()
    w   = csv.writer(buf)
    w.writerow(['Unidade','Município','Tipo','Atendimentos','Internações',
                'Altas','Óbitos','Cirurgias','PS','Transf. Enviadas',
                'Transf. Recebidas','Taxa Ocupação (%)','Total Leitos',
                'Período'])
    for d in dados:
        w.writerow([d['unidade'], d['municipio'], d['tipo'],
                    d['atendimentos'], d['internacoes'], d['altas'],
                    d['obitos'], d['cirurgias'], d['ps'],
                    d['transf_env'], d['transf_rec'],
                    d['taxa_ocu'], d['leitos_total'],
                    f'{data_ini} a {data_fim}'])
    w.writerow([])
    w.writerow(['TOTAL', totais['municipio'], '—',
                totais['atendimentos'], totais['internacoes'],
                totais['altas'], totais['obitos'], totais['cirurgias'],
                totais['ps'], totais['transf_env'], totais['transf_rec'],
                totais['taxa_ocu'], totais['leitos_total'], ''])
    buf.seek(0)
    return send_file(BytesIO(buf.getvalue().encode('utf-8-sig')),
                     mimetype='text/csv', as_attachment=True,
                     download_name=f'relatorio_estadual_{date.today()}.csv')


def _gerar_pdf_consolidado(dados, totais, data_ini, data_fim):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    AZUL  = colors.HexColor('#003F88')
    CINZA = colors.HexColor('#2C3140')

    estilos = {
        'titulo': ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=13, textColor=AZUL),
        'sub':    ParagraphStyle('s', fontName='Helvetica', fontSize=8, textColor=CINZA),
        'rodape': ParagraphStyle('r', fontName='Helvetica', fontSize=7,
                                  textColor=colors.HexColor('#8A95A8'), alignment=TA_CENTER),
    }

    s = []
    s.append(Paragraph('Relatório Consolidado Estadual', estilos['titulo']))
    s.append(Paragraph(f'Período: {data_ini} a {data_fim}  ·  {len(dados)} unidades', estilos['sub']))
    s.append(Spacer(1, 0.3*cm))
    s.append(HRFlowable(width='100%', thickness=1, color=AZUL, spaceAfter=8))

    cabecalho = ['Unidade', 'Município', 'Tipo', 'Atend.', 'Intern.',
                 'Altas', 'Óbitos', 'Cir.', 'PS', 'Tx.Ocu%']
    linhas = [cabecalho]
    for d in dados:
        linhas.append([
            d['unidade'][:28], d['municipio'][:16], d['tipo'][:10],
            str(d['atendimentos']), str(d['internacoes']), str(d['altas']),
            str(d['obitos']), str(d['cirurgias']), str(d['ps']),
            f"{d['taxa_ocu']}%",
        ])
    linhas.append(['TOTAL', totais['municipio'], '—',
                   str(totais['atendimentos']), str(totais['internacoes']),
                   str(totais['altas']), str(totais['obitos']),
                   str(totais['cirurgias']), str(totais['ps']),
                   f"{totais['taxa_ocu']}%"])

    col_w = [6.5*cm, 3.5*cm, 2.5*cm, 1.5*cm, 1.5*cm, 1.5*cm,
             1.5*cm, 1.3*cm, 1.3*cm, 1.8*cm]
    tbl = Table(linhas, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  AZUL),
        ('TEXTCOLOR',    (0,0), (-1,0),  colors.white),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-2), [colors.white, colors.HexColor('#F7F8FA')]),
        ('BACKGROUND',   (0,-1),(-1,-1), colors.HexColor('#E8F0FB')),
        ('FONTNAME',     (0,-1),(-1,-1), 'Helvetica-Bold'),
        ('BOX',          (0,0), (-1,-1), 0.5, colors.HexColor('#D8DDE6')),
        ('INNERGRID',    (0,0), (-1,-1), 0.3, colors.HexColor('#D8DDE6')),
        ('ALIGN',        (3,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
    ]))
    s.append(tbl)
    s.append(Spacer(1, 0.4*cm))
    s.append(HRFlowable(width='100%', thickness=0.5,
                         color=colors.HexColor('#D8DDE6')))
    s.append(Paragraph(
        f'Gerado em {date.today().strftime("%d/%m/%Y")}  ·  Sistema de Prontuário Único SUS',
        estilos['rodape']))

    doc.build(s)
    buf.seek(0)
    return send_file(buf, mimetype='application/pdf', as_attachment=True,
                     download_name=f'relatorio_estadual_{date.today()}.pdf')
    
@rel_estadual_bp.route('/hospitalares')   
@login_required
def hospitalares():
    """Relatório de indicadores hospitalares da unidade"""
    if not current_user.unidade_id:
        flash('Você não tem uma unidade associada', 'danger')
        return redirect(url_for('rel_hosp.index'))
    return redirect(url_for('rel_hosp.index'))
    
    data_ini = request.args.get('data_ini', date.today().replace(day=1).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))

    try:
        di = datetime.strptime(data_ini, '%Y-%m-%d')
        df = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59)
    except ValueError:
        di = datetime.now().replace(day=1)
        df = datetime.now()

    unidade = Unidade.query.get(current_user.unidade_id)
    
    # Dados da unidade
    atendimentos = Atendimento.query.filter(
        Atendimento.data_hora.between(di, df),
        Atendimento.unidade_id == current_user.unidade_id
    ).count()
    
    internacoes = Internacao.query.filter(
        Internacao.data_entrada.between(di, df),
        Internacao.unidade_id == current_user.unidade_id
    ).count()
    
    altas = Internacao.query.filter(
        Internacao.data_alta.between(di, df),
        Internacao.unidade_id == current_user.unidade_id,
        Internacao.status == 'alta'
    ).count()
    
    obitos = Internacao.query.filter(
        Internacao.data_alta.between(di, df),
        Internacao.unidade_id == current_user.unidade_id,
        Internacao.status == 'obito'
    ).count()
    
    cirurgias = Cirurgia.query.filter(
        Cirurgia.data_agendada.between(di, df),
        Cirurgia.unidade_id == current_user.unidade_id,
        Cirurgia.status == 'realizada'
    ).count()
    
    ps_atendimentos = AtendimentoPS.query.filter(
        AtendimentoPS.data_entrada.between(di, df),
        AtendimentoPS.unidade_id == current_user.unidade_id
    ).count()
    
    transf_enviadas = TransferenciaPaciente.query.filter(
        TransferenciaPaciente.data_solicitacao.between(di, df),
        TransferenciaPaciente.unidade_origem_id == current_user.unidade_id
    ).count()
    
    transf_recebidas = TransferenciaPaciente.query.filter(
        TransferenciaPaciente.data_solicitacao.between(di, df),
        TransferenciaPaciente.unidade_destino_id == current_user.unidade_id
    ).count()
    
    # Leitos
    total_leitos = Leito.query.filter_by(ativo=True).count()
    leitos_ocupados = Leito.query.filter_by(ativo=True, status='ocupado').count()
    taxa_ocupacao = round((leitos_ocupados / total_leitos * 100) if total_leitos else 0)
    
    # Indicadores
    taxa_mortalidade = round((obitos / internacoes * 100) if internacoes > 0 else 0)
    taxa_altas = round((altas / internacoes * 100) if internacoes > 0 else 0)
    
    indicadores = {
        'atendimentos': atendimentos,
        'internacoes': internacoes,
        'altas': altas,
        'obitos': obitos,
        'cirurgias': cirurgias,
        'ps': ps_atendimentos,
        'transf_enviadas': transf_enviadas,
        'transf_recebidas': transf_recebidas,
        'total_leitos': total_leitos,
        'leitos_ocupados': leitos_ocupados,
        'taxa_ocupacao': taxa_ocupacao,
        'taxa_mortalidade': taxa_mortalidade,
        'taxa_altas': taxa_altas,
    }
    
    return render_template('relatorio_estadual/hospitalares.html',
                           unidade=unidade,
                           indicadores=indicadores,
                           data_ini=data_ini,
                           data_fim=data_fim)