from flask_script import Manager
from api import app
from api.scripts.db import InitDB, CreatePessoas


if __name__ == "__main__":
    manager = Manager(app)
    manager.add_command('init_db', InitDB())
    manager.add_command('create_pessoas', CreatePessoas())
    manager.run()
