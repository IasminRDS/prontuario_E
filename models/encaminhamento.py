    paciente_id     = db.Column(db.Integer, db.ForeignKey('pacientes.id'),   nullable=False)
    prontuario_id   = db.Column(db.Integer, db.ForeignKey('prontuarios.id'), nullable=True)
    medico_id       = db.Column(db.Integer, db.ForeignKey('medicos.id'),     nullable=True)
    unidade_origem_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id'), nullable=False)

    especialidade   = db.Column(db.String(100), nullable=False)
    servico_destino = db.Column(db.String(200), nullable=True)


    prioridade      = db.Column(db.String(20), default='eletivo')


    motivo          = db.Column(db.Text, nullable=False)
    hipotese_diagnostica = db.Column(db.String(200), nullable=True)
    cid             = db.Column(db.String(10),  nullable=True)

    status          = db.Column(db.String(20), default='solicitado')


    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_agendada    = db.Column(db.DateTime, nullable=True)
    data_realizacao  = db.Column(db.DateTime, nullable=True)

    observacoes      = db.Column(db.Text, nullable=True)
    retorno_info     = db.Column(db.Text, nullable=True)

    criado_por  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relacionamentos
    paciente       = db.relationship('Paciente',   backref='encaminhamentos')
    prontuario     = db.relationship('Prontuario', backref='encaminhamentos')
    medico         = db.relationship('Medico',     backref='encaminhamentos')
    unidade_origem = db.relationship('UnidadeSaude', backref='encaminhamentos')

    STATUS_LABELS = {
        'solicitado': ('Solicitado', 'cinza'),
    return self.PRIORIDADE_LABELS.get(self.prioridade, (self.prioridade, 'cinza'))

    def __repr__(self):
        return f'<Encaminhamento {self.id} {self.especialidade}>'
    