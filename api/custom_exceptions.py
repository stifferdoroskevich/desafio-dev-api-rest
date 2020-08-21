# error messages
msg_params_invalid = "Parametros invalidos. Favor siga a documentacao: https://bit.ly/documentacao_dock"
msg_data_not_found = "Sua consulta nao retornou dados"
msg_account_not_found = "Conta nao existente."
msg_account_inactive = "Conta ja se encontrava inativa."
msg_200 = "Operacao realizada com sucesso."


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class DatabaseError(Exception):
    pass
