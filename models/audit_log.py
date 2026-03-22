from database.db import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tabela      = db.Column(db.String(50),  nullable=False)
    registro_id = db.Column(db.Integer,     nullable=True)
    acao        = db.Column(db.String(20),  nullable=False)  # create | update | delete | view
    descricao   = db.Column(db.Text,        nullable=True)
    ip          = db.Column(db.String(45),  nullable=True)
    criado_em   = db.Column(db.DateTime,    default=datetime.utcnow)

    usuario = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.acao} {self.tabela}:{self.registro_id}>'
