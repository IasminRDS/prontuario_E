# -*- coding: utf-8 -*-
"""
Modelos de Dados - Prontuário Único SUS
Importação centralizada de todos os modelos
"""

# Modelos principais
from models.paciente import Paciente
from models.user import User as Usuario
from models.unidade import UnidadeSaude
from models.medico import Medico

# Modelos de atendimento
from models.atendimento import Atendimento
from models.agendamento import Agendamento
from models.triagem import Triagem
from models.prontuario import Prontuario

# Modelos de consulta e exames
from models.exame import Exame

# Modelos de internação
from models.internacao import Internacao
from models.prescricao_hospitalar import PrescricaoHospitalar

# Modelos de procedimentos
from models.cirurgia import Cirurgia
from models.pronto_socorro import ProntoSocorro

# Modelos de medicamentos e vacinas
from models.medicamento import Medicamento
from models.vacina import Vacina

# Modelos de referência e encaminhamento
from models.encaminhamento import Encaminhamento

# Modelos de estoque
from models.estoque import Estoque

# Modelos financeiros
from models.faturamento import Faturamento

# Modelos de auditoria
from models.audit_log import AuditLog

# Exportar todos os modelos
__all__ = [
    'Paciente',
    'Usuario',
    'UnidadeSaude',
    'Medico',
    'Atendimento',
    'Agendamento',
    'Triagem',
    'Prontuario',
    'Exame',
    'Internacao',
    'PrescricaoHospitalar',
    'Cirurgia',
    'ProntoSocorro',
    'Medicamento',
    'Vacina',
    'Encaminhamento',
    'Estoque',
    'Faturamento',
    'AuditLog'
]