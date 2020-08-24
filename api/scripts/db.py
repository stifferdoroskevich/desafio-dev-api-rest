from flask_script import Command
from api import db
from api.models.db_creation import Pessoas


class InitDB(Command):
    "Create Database"

    def run(self):
        db.drop_all()
        db.create_all()


class CreatePessoas(Command):
    "Create 2 rows on Pessoas Table"

    def run(self):
        pessoa1 = Pessoas('Márcio Luiz Félix Filho', '333.888.333-44', '01/01/1990')
        pessoa2 = Pessoas('Samuel Oliveira Santos', '334.889.334-45', '01/01/1990')
        pessoa3 = Pessoas('Stiffer Doroskevich', '335.890.335-46', '01/01/1988')
        db.session.add(pessoa1)
        db.session.add(pessoa2)
        db.session.add(pessoa3)
        db.session.commit()
