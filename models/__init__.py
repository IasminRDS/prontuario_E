# -*- coding: utf-8 -*-
"""
Models Package - Importação centralizada de todos os modelos
Prontuário Único - SUS
"""

# ========== MODELOS BÁSICOS ==========
from models.unidade import Unidade

# Corrigir imports que usam UnidadeSaude (deve ser Unidade)
__all__ = ['Unidade']  # Alias para backward compatibility


# ========== MODELOS DE USUÁRIOS ==========
try:
    from models.user import User
    __all__.append('User')
except ImportError as e:
    print(f"⚠️  User: {e}")


# ========== MODELOS DE PACIENTES ==========
try:
    from models.paciente import Paciente
    __all__.append('Paciente')
except ImportError as e:
    print(f"⚠️  Paciente: {e}")


# ========== MODELOS DE MÉDICOS ==========
try:
    from models.medico import Medico
    __all__.append('Medico')
except ImportError as e:
    print(f"⚠️  Médico: {e}")


# ========== MODELOS DE ATENDIMENTO ==========
try:
    from models.atendimento import Atendimento
    __all__.append('Atendimento')
except ImportError as e:
    print(f"⚠️  Atendimento: {e}")


# ========== MODELOS DE PRONTUÁRIO ==========
try:
    from models.prontuario import Prontuario
    __all__.append('Prontuario')
except ImportError as e:
    print(f"⚠️  Prontuário: {e}")


# ========== MODELOS DE AUDITORIA ==========
try:
    from models.auditlog import AuditLog
    __all__.append('AuditLog')
except ImportError as e:
    print(f"⚠️  AuditLog: {e}")


# ========== MODELOS DE AGENDAMENTO ==========
try:
    from models.agendamento import Agendamento
    __all__.append('Agendamento')
except ImportError as e:
    print(f"⚠️  Agendamento: {e}")


# ========== MODELOS DE VACINAÇÃO ==========
try:
    from models.vacina import Vacina, VacinaAplicada
    __all__.extend(['Vacina', 'VacinaAplicada'])
except ImportError as e:
    print(f"⚠️  Vacina: {e}")


# ========== MODELOS DE TRIAGEM ==========
try:
    from models.triagem import Triagem
    __all__.append('Triagem')
except ImportError as e:
    print(f"⚠️  Triagem: {e}")


# ========== MODELOS DE EXAMES ==========
try:
    from models.exame import TipoExame, ExameSolicitado
    __all__.extend(['TipoExame', 'ExameSolicitado'])
except ImportError as e:
    print(f"⚠️  Exame: {e}")


# ========== MODELOS DE ENCAMINHAMENTOS ==========
try:
    from models.encaminhamento import Encaminhamento
    __all__.append('Encaminhamento')
except ImportError as e:
    print(f"⚠️  Encaminhamento: {e}")


# ========== MODELOS DE MEDICAMENTOS ==========
try:
    from models.medicamento import Medicamento, Prescricao, ItemPrescricao
    __all__.extend(['Medicamento', 'Prescricao', 'ItemPrescricao'])
except ImportError as e:
    print(f"⚠️  Medicamento: {e}")


# ========== MODELOS DE INTERNAÇÃO ==========
try:
    from models.internacao import Setor, Leito, Internacao, EvolucaoInternacao
    __all__.extend(['Setor', 'Leito', 'Internacao', 'EvolucaoInternacao'])
except ImportError as e:
    print(f"⚠️  Internação: {e}")


# ========== MODELOS DE PRESCRIÇÃO HOSPITALAR ==========
try:
    from models.prescricao_hospitalar import (
        PrescricaoHospitalar, 
        ItemPrescricaoHosp, 
        AdministracaoMed
    )
    __all__.extend(['PrescricaoHospitalar', 'ItemPrescricaoHosp', 'AdministracaoMed'])
except ImportError as e:
    print(f"⚠️  PrescricaoHospitalar: {e}")


# ========== MODELOS DE CIRURGIA ==========
try:
    from models.cirurgia import SalaCirurgica, Cirurgia
    __all__.extend(['SalaCirurgica', 'Cirurgia'])
except ImportError as e:
    print(f"⚠️  Cirurgia: {e}")


# ========== MODELOS DE ESTOQUE ==========
try:
    from models.estoque import ItemEstoque, MovEstoque
    __all__.extend(['ItemEstoque', 'MovEstoque'])
except ImportError as e:
    print(f"⚠️  Estoque: {e}")


# ========== MODELOS DE FATURAMENTO (SIA/SIH) ==========
try:
    from models.faturamento import AIH, APAC, ProcessoFaturamento
    __all__.extend(['AIH', 'APAC', 'ProcessoFaturamento'])
except ImportError as e:
    print(f"⚠️  Faturamento: {e}")


# ========== MODELOS DE PRONTO SOCORRO ==========
try:
    from models.pronto_socorro import AtendimentoPS
    __all__.append('AtendimentoPS')
except ImportError as e:
    print(f"⚠️  AtendimentoPS: {e}")


# ========== MODELOS DE TRANSFERÊNCIA ==========
try:
    from models.transferencia import TransferenciaPaciente
    __all__.append('TransferenciaPaciente')
except ImportError as e:
    print(f"⚠️  TransferenciaPaciente: {e}")


# ========== MODELOS DE PERMISSÕES E ACESSO ==========
try:
    from models.permissao import Permissao, Role, RolePermissao, AcessoEstadual
    __all__.extend(['Permissao', 'Role', 'RolePermissao', 'AcessoEstadual'])
except ImportError as e:
    print(f"⚠️  Permissões: {e}")


# ========== MODELOS DE ALERTAS ==========
try:
    from models.alerta import Alerta, ConfiguradorAlerta
    __all__.extend(['Alerta', 'ConfiguradorAlerta'])
except ImportError as e:
    print(f"⚠️  Alertas: {e}")


# ========== MODELOS DE KPI ==========
try:
    from models.kpi import KPI
    __all__.append('KPI')
except ImportError as e:
    print(f"⚠️  KPI: {e}")


# ========== MODELOS DE PREDIÇÃO ==========
try:
    from models.predicao import Predicao
    __all__.append('Predicao')
except ImportError as e:
    print(f"⚠️  Predição: {e}")


# ========== MODELOS DE VAGAS ==========
try:
    from models.vaga import Vaga, SolicitacaoTransferencia
    __all__.extend(['Vaga', 'SolicitacaoTransferencia'])
except ImportError as e:
    print(f"⚠️  Vagas: {e}")


# ========== MODELOS DE GEOLOCALIZAÇÃO ==========
try:
    from models.geo import Localizacao, AcessibilidadeRegiao, DemandaPorRegiao
    __all__.extend(['Localizacao', 'AcessibilidadeRegiao', 'DemandaPorRegiao'])
except ImportError as e:
    print(f"⚠️  Geolocalização: {e}")


# ========== MODELOS DE TELEMEDICINA ==========
try:
    from models.telemedicina import ConsultaTelemedicina, MonitoramentoPaciente
    __all__.extend(['ConsultaTelemedicina', 'MonitoramentoPaciente'])
except ImportError as e:
    print(f"⚠️  Telemedicina: {e}")


# ========== MODELOS DE NOTIFICAÇÕES ==========
try:
    from models.notificacao import SubscricaoPush
    __all__.append('SubscricaoPush')
except ImportError as e:
    print(f"⚠️  SubscricaoPush: {e}")


# ========== ALIASES PARA BACKWARD COMPATIBILITY ==========
# Se algum código usa "UnidadeSaude", ele será redirecionado para "Unidade"
UnidadeSaude = Unidade

# Adicionar ao __all__
if 'UnidadeSaude' not in __all__:
    __all__.append('UnidadeSaude')