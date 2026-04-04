from database.db import db
from datetime import datetime

class Regional(db.Model):
    __tablename__ = "regionais"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    codigo = db.Column(db.String(20), nullable=True, unique=True)
    uf = db.Column(db.String(2), nullable=False, index=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # relação com Unidade via regional_id (adicionaremos no model Unidade)
    unidades = db.relationship("Unidade", backref="regional", lazy="dynamic")

    def __repr__(self):
        return f"<Regional {self.nome}/{self.uf}>"