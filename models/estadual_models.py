# -*- coding: utf-8 -*-
"""
Modelos de Dados para Operações Estaduais
Regulação, Vagas, Transferências, Alertas
"""

from database.db import db
from datetime import datetime
from enum import Enum

class StatusRegulacao(Enum):
    """Status de uma regulação"""
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    RECUSADA = "recusada"
    CANCELADA = "cancelada"
    TRANSFERIDA = "transferida"

class StatusTransferencia(Enum):
    """Status de transferência de paciente"""
    SOLICITADA = "solicitada"
    APROVADA = "aprovada"
    EM_TRANSITO = "em_transito"
    RECEBIDA = "recebida"
    CANCELADA = "cancelada"

class SeveridadeAlerta(Enum):
    """Níveis de severidade de alertas"""
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"
    INFO = "info"

class TipoAlerta(Enum):
    """Tipos de alertas do sistema"""
    SUPERLOTACAO = "superlotacao"
    PACIENTE_RISCO = "paciente_risco"
    SURTO = "surto"
    VAGAS_CRITICAS = "vagas_criticas"
    PERFORMANCE = "performance"
    OPERACIONAL = "operacional"

# ========== MODELO: REGULAÇÃO ==========
class Regulacao(db.Model):
    """
    Regulação de Leitos no Estado
    Integração entre unidades para oferta/demanda de leitos
    """
    __tablename__ = 'regulacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações do Paciente
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    paciente = db.relationship('Paciente', backref='regulacoes')
    
    # Unidade Solicitante (onde está o paciente)
    unidade_solicitante_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=False)
    unidade_solicitante = db.relationship('UnidadeSaude', foreign_keys=[unidade_solicitante_id], backref='regulacoes_solicitadas')
    
    # Unidade Reguladora (que vai receber)
    unidade_receptora_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=True)
    unidade_receptora = db.relationship('UnidadeSaude', foreign_keys=[unidade_receptora_id], backref='regulacoes_recebidas')
    
    # Informações Clínicas
    especialidade = db.Column(db.String(100), nullable=False)  # Cardiologia, Neurologia, etc
    diagnostico = db.Column(db.String(500), nullable=True)
    descricao_clinica = db.Column(db.Text, nullable=True)
    urgencia = db.Column(db.String(20), default='eletiva')  # urgente, emergencial, eletiva
    
    # Status
    status = db.Column(db.String(20), default='pendente')  # pendente, aprovada, recusada, etc
    motivo_recusa = db.Column(db.Text, nullable=True)
    
    # Profissional responsável
    profissional_solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    profissional_solicitante = db.relationship('Usuario', foreign_keys=[profissional_solicitante_id])
    
    profissional_regulador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    profissional_regulador = db.relationship('Usuario', foreign_keys=[profissional_regulador_id])
    
    # Timestamps
    data_solicitacao = db.Column(db.DateTime, default=datetime.now)
    data_resposta = db.Column(db.DateTime, nullable=True)
    data_transferencia = db.Column(db.DateTime, nullable=True)
    
    # Prioridade
    prioridade = db.Column(db.Integer, default=0)  # 0-10, maior = mais urgente
    tempo_maximo_resposta = db.Column(db.Integer)  # minutos
    
    def __repr__(self):
        return f'<Regulacao {self.id} - {self.status}>'
    
    def tempo_resposta_minutos(self):
        """Calcula tempo de resposta em minutos"""
        if self.data_resposta:
            delta = self.data_resposta - self.data_solicitacao
            return int(delta.total_seconds() / 60)
        return None
    
    def esta_vencida(self):
        """Verifica se a regulação venceu o prazo"""
        if self.tempo_maximo_resposta:
            tempo = self.tempo_resposta_minutos()
            return tempo and tempo > self.tempo_maximo_resposta
        return False

# ========== MODELO: VAGA ==========
class Vaga(db.Model):
    """
    Controle de Vagas Disponíveis em Leitos
    Integração estadual de disponibilidade
    """
    __tablename__ = 'vagas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    codigo_vaga = db.Column(db.String(50), unique=True, nullable=False)  # Ex: "UTI-001"
    
    # Localização
    unidade_saude_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=False)
    unidade_saude = db.relationship('UnidadeSaude', backref='vagas')
    
    # Informações da Vaga
    especialidade = db.Column(db.String(100), nullable=False)
    tipo_leito = db.Column(db.String(50), nullable=False)  # UTI, Semi-intensivo, Enfermaria
    tipo_cuidado = db.Column(db.String(100), nullable=False)  # Clínico, Cirúrgico, etc
    
    # Status
    ocupada = db.Column(db.Boolean, default=False)
    ativa = db.Column(db.Boolean, default=True)
    
    # Paciente Atual
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    paciente = db.relationship('Paciente', backref='vaga_atual')
    
    # Internação Atual
    internacao_id = db.Column(db.Integer, db.ForeignKey('internacoes.id'), nullable=True)
    internacao = db.relationship('Internacao', backref='vaga')
    
    # Disponibilidade
    data_disponivel = db.Column(db.DateTime, nullable=True)
    previsao_liberacao = db.Column(db.DateTime, nullable=True)
    
    # Controle
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Vaga {self.codigo_vaga} - {"Ocupada" if self.ocupada else "Disponível"}>'
    
    @property
    def status(self):
        if not self.ativa:
            return "Inativa"
        elif self.ocupada:
            return "Ocupada"
        else:
            return "Disponível"
    
    def liberar(self):
        """Libera a vaga"""
        self.ocupada = False
        self.paciente_id = None
        self.internacao_id = None
        self.data_disponivel = datetime.now()
        db.session.commit()

# ========== MODELO: TRANSFERÊNCIA ==========
class Transferencia(db.Model):
    """
    Transferência de Pacientes entre Unidades
    Controle de fluxo de pacientes
    """
    __tablename__ = 'transferencias'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Paciente
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    paciente = db.relationship('Paciente', backref='transferencias')
    
    # Unidades
    unidade_origem_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=False)
    unidade_origem = db.relationship('UnidadeSaude', foreign_keys=[unidade_origem_id], backref='transferencias_saida')
    
    unidade_destino_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=False)
    unidade_destino = db.relationship('UnidadeSaude', foreign_keys=[unidade_destino_id], backref='transferencias_entrada')
    
    # Informações
    motivo = db.Column(db.Text, nullable=False)
    especializacao_necessaria = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='solicitada')  # solicitada, aprovada, em_transito, recebida
    
    # Profissionais
    solicitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    solicitado_por = db.relationship('Usuario', foreign_keys=[solicitado_por_id])
    
    autorizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    autorizado_por = db.relationship('Usuario', foreign_keys=[autorizado_por_id])
    
    # Transportador
    transportador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    transportador = db.relationship('Usuario', foreign_keys=[transportador_id])
    
    # Timestamps
    data_solicitacao = db.Column(db.DateTime, default=datetime.now)
    data_autorizacao = db.Column(db.DateTime, nullable=True)
    data_saida = db.Column(db.DateTime, nullable=True)
    data_chegada = db.Column(db.DateTime, nullable=True)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    intercorrencias = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Transferencia {self.id} - {self.status}>'
    
    def tempo_espera_minutos(self):
        """Tempo de espera desde solicitação"""
        data_fim = self.data_autorizacao or datetime.now()
        delta = data_fim - self.data_solicitacao
        return int(delta.total_seconds() / 60)
    
    def tempo_transito_minutos(self):
        """Tempo de trânsito"""
        if self.data_saida and self.data_chegada:
            delta = self.data_chegada - self.data_saida
            return int(delta.total_seconds() / 60)
        return None

# ========== MODELO: ALERTA ==========
class Alerta(db.Model):
    """
    Sistema de Alertas Inteligente
    Monitora situações críticas em tempo real
    """
    __tablename__ = 'alertas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    
    # Tipo e Severidade
    tipo = db.Column(db.String(50), nullable=False)  # superlotacao, paciente_risco, surto, etc
    severidade = db.Column(db.String(20), default='medio')  # critico, alto, medio, baixo, info
    
    # Descrição
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    acao_recomendada = db.Column(db.Text, nullable=True)
    
    # Contexto
    unidade_saude_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=True)
    unidade_saude = db.relationship('UnidadeSaude', backref='alertas')
    
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    paciente = db.relationship('Paciente', backref='alertas')
    
    # Dados adicionais (JSON)
    dados = db.Column(db.JSON, nullable=True)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    lido = db.Column(db.Boolean, default=False)
    resolvido = db.Column(db.Boolean, default=False)
    
    # Profissional responsável
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    responsavel = db.relationship('Usuario', backref='alertas_responsavel')
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_leitura = db.Column(db.DateTime, nullable=True)
    data_resolucao = db.Column(db.DateTime, nullable=True)
    data_expiracao = db.Column(db.DateTime, nullable=True)
    
    # Prioridade
    prioridade = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Alerta {self.codigo} - {self.severidade}>'
    
    def marcar_como_lido(self):
        self.lido = True
        self.data_leitura = datetime.now()
        db.session.commit()
    
    def resolver(self):
        self.resolvido = True
        self.ativo = False
        self.data_resolucao = datetime.now()
        db.session.commit()
    
    @property
    def tempo_ativo_minutos(self):
        data_fim = self.data_resolucao or datetime.now()
        delta = data_fim - self.data_criacao
        return int(delta.total_seconds() / 60)

# ========== MODELO: KPIS ESTADUAIS ==========
class KPIEstadual(db.Model):
    """
    Armazena KPIs calculados para análise histórica
    """
    __tablename__ = 'kpi_estaduais'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Data do KPI
    data = db.Column(db.Date, nullable=False, default=datetime.now().date)
    
    # Indicadores Gerais
    total_pacientes = db.Column(db.Integer, default=0)
    pacientes_ativos_30d = db.Column(db.Integer, default=0)
    total_consultas = db.Column(db.Integer, default=0)
    total_internacoes = db.Column(db.Integer, default=0)
    
    # Ocupação
    leitos_totais = db.Column(db.Integer, default=0)
    leitos_ocupados = db.Column(db.Integer, default=0)
    taxa_ocupacao = db.Column(db.Float, default=0.0)
    
    # UTI
    uti_total = db.Column(db.Integer, default=0)
    uti_ocupados = db.Column(db.Integer, default=0)
    taxa_ocupacao_uti = db.Column(db.Float, default=0.0)
    
    # Especialidades
    top_especialidades = db.Column(db.JSON, nullable=True)
    
    # Regiões
    performance_regioes = db.Column(db.JSON, nullable=True)
    
    # Eficiência
    tempo_medio_atendimento = db.Column(db.Integer, default=0)  # minutos
    taxa_reinternacao = db.Column(db.Float, default=0.0)
    taxa_falta_agendamento = db.Column(db.Float, default=0.0)
    
    # Alertas
    total_alertas = db.Column(db.Integer, default=0)
    alertas_criticos = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<KPIEstadual {self.data}>'

# ========== MODELO: RELATÓRIO AGENDADO ==========
class RelatórioAgendado(db.Model):
    """
    Relatórios que são gerados automaticamente
    """
    __tablename__ = 'relatorios_agendados'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # diario, semanal, mensal
    formato = db.Column(db.String(20), default='pdf')  # pdf, xlsx, csv
    
    # Descrição
    descricao = db.Column(db.Text, nullable=True)
    
    # Destinatários
    destinatarios = db.Column(db.JSON, nullable=True)  # lista de emails
    
    # Agendamento
    ativo = db.Column(db.Boolean, default=True)
    dia_semana = db.Column(db.Integer, nullable=True)  # 0-6
    dia_mes = db.Column(db.Integer, nullable=True)     # 1-31
    hora = db.Column(db.Integer, default=0)
    minuto = db.Column(db.Integer, default=0)
    
    # Timestamp
    proxima_geracao = db.Column(db.DateTime, nullable=True)
    ultima_geracao = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<RelatórioAgendado {self.nome}>'