def init_db(app):
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    with app.app_context():
        from models.user import User
        from models.paciente import Paciente
        from models.medico import Medico
        from models.unidade import Unidade
        from models.atendimento import Atendimento
        from models.prontuario import Prontuario
        from models.audit_log import AuditLog
        from models.agendamento import Agendamento
        from models.vacina import Vacina, VacinaAplicada
        from models.triagem import Triagem
        from models.exame import TipoExame, ExameSolicitado
        from models.encaminhamento import Encaminhamento
        from models.medicamento import Medicamento, Prescricao, ItemPrescricao
        from models.internacao import Setor, Leito, Internacao, EvolucaoInternacao
        from models.prescricao_hospitalar import PrescricaoHospitalar, ItemPrescricaoHosp, AdministracaoMed
        from models.cirurgia import SalaCirurgica, Cirurgia
        from models.estoque import ItemEstoque, MovEstoque
        from models.faturamento import AIH, APAC
        from models.pronto_socorro import AtendimentoPS
        from models.transferencia import TransferenciaPaciente  # ← ADICIONE ESTA LINHA
        db.create_all()
        _seed_data()