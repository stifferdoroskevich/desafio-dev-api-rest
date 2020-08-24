from api import app, db, custom_exceptions as ce
from flask import request, jsonify
from werkzeug.exceptions import HTTPException
from api.models.db_creation import Contas, Transacoes, Pessoas


@app.route('/')
def home():
    return "Welcome to DOCK!"


@app.route('/pessoas', methods=['GET'])
def get_pessoas():
    pessoas = Pessoas.query.all()
    dados_pessoas = {}
    for pessoa in pessoas:
        dados_pessoas[pessoa.id_pessoa] = {
            'idPessoa': pessoa.id_pessoa,
            'nome': pessoa.nome,
            'cpf': pessoa.cpf,
            'dataNascimento': pessoa.data_nascimento
        }
    if not pessoas:
        raise ce.InvalidUsage("Pessoas nao encontradas")

    return jsonify(dados_pessoas)


@app.route('/pessoas/<id>', methods=['GET'])
def get_pessoa(id):
    pessoa = Pessoas.query.get(id)
    if not pessoa:
        raise ce.InvalidUsage("Pessoa nao encontrada")

    dados_pessoa = {id: {
        'idPessoa': pessoa.id_pessoa,
        'nome': pessoa.nome,
        'cpf': pessoa.cpf,
        'dataNascimento': pessoa.data_nascimento
    }}
    return jsonify(dados_pessoa)


@app.route('/contas', methods=['POST'])
def new_conta():
    id_pessoa = int(request.json['idPessoa'])
    saldo = int(request.json['saldo'])
    limite_saque_diario = int(request.json['limiteSaqueDiario'])
    flag_ativo = bool(request.json['flagAtivo'])
    tipo_conta = int(request.json['tipoConta'])

    # Validar limiteSaqueDiario e saldo e tipoConta
    if limite_saque_diario < 0 or tipo_conta not in [0, 1]:
        raise ce.InvalidUsage({"message": "Limite de saque diario nao deve ser negativo. Tipo de conta deve ser 0 - Conta Corrente, 1 - Conta Poupança."})

    # Validar se a pessoa existe
    pessoa = Pessoas.query.get(id_pessoa)
    if not pessoa:
        raise ce.InvalidUsage({"message": "Pessoa nao existente"})

    try:
        conta = Contas(id_pessoa, saldo, limite_saque_diario, flag_ativo, tipo_conta)
        db.session.add(conta)
        db.session.commit()
    except ce.DatabaseError:
        return jsonify({"message": "Erro no banco de Dados, dados nao salvos"})

    return jsonify({"message": {"idConta": conta.id_conta}}), 200


@app.route('/contas/<id>', methods=['GET'])
def get_saldo(id):
    if not id.isnumeric():
        raise ce.InvalidUsage(ce.msg_params_invalid)

    conta = Contas.query.get(id)

    if not conta:
        raise ce.InvalidUsage("Conta {} nao existe".format(id))

    valor_saldo = {'saldo': conta.saldo}

    return jsonify(valor_saldo)


@app.route('/contas/inativar/<id>', methods=['PUT'])
def inativar_conta(id):
    if not id.isnumeric():
        raise ce.InvalidUsage(ce.msg_params_invalid)

    conta = Contas.query.get(id)

    if not conta:
        raise ce.InvalidUsage("Conta {} nao existe".format(id))

    if not conta.flag_ativo:
        raise ce.InvalidUsage("Conta {} inativada anteriormente".format(id))

    conta.flag_ativo = False
    db.session.commit()
    return jsonify({'message': "Conta {} inativada".format(id)})


@app.route('/transacao/deposito', methods=['POST'])
def deposito():
    if not request.json:
        raise ce.InvalidUsage(ce.msg_params_invalid)
    id_conta = request.json['idConta']
    conta = Contas.query.get(id_conta)
    if not int(id_conta):
        raise ce.InvalidUsage(ce.msg_params_invalid)
    if not conta:
        raise ce.InvalidUsage("Conta {} nao existente".format(id_conta))
    if not conta.flag_ativo:
        raise ce.InvalidUsage("Conta {} está inativa.".format(id_conta))
    valor = request.json['valor']
    if valor < 0:
        raise ce.InvalidUsage("Valor {} negativo. ".format(valor) + ce.msg_params_invalid)

    try:
        transacao = Transacoes(id_conta, valor)
        conta.saldo = conta.saldo + valor
        db.session.add(transacao, conta)
        db.session.commit()
    except ce.DatabaseError:
        return jsonify({"message": "Erro no banco de Dados, dados nao salvos"})

    if transacao:
        return jsonify({"message": ce.msg_200 + " Saldo atual {}".format(conta.saldo)}), 200


@app.route('/transacao/saque', methods=['POST'])
def saque():
    id_conta = request.json['idConta']
    valor = request.json['valor']
    conta = Contas.query.get(id_conta)
    if not conta:
        raise ce.InvalidUsage("Conta {} nao existente".format(id_conta))
    if not conta.flag_ativo:
        raise ce.InvalidUsage("Conta {} está inativa.".format(id_conta))
    if valor < 0:
        raise ce.InvalidUsage("Valor {} negativo. ".format(valor) + ce.msg_params_invalid)
    if valor > conta.saldo:
        return jsonify({"message": "Saldo Insuficiente"})
    if valor > conta.limite_saque_diario:
        return jsonify({"message": "valor superior ao limite diario. Valor maximo: {}".format(conta.limite_saque_diario)})

    try:
        conta.saldo = conta.saldo - valor
        transacao = Transacoes(id_conta, -valor)
        db.session.add(transacao, conta)
        db.session.commit()
    except ce.DatabaseError:
        return jsonify({"message": "Erro no banco de Dados, dados nao salvos"})

    return jsonify({"message": "Saque realizado com sucesso. Saldo Atual: {}".format(conta.saldo)}), 200


@app.route('/transacao/extrato/<id>', methods=['GET'])
def get_extrato_conta(id):
    if not Contas.query.get(id):
        raise ce.InvalidUsage("Conta {} nao encontrada".format(id))
    filter_list = [Transacoes.id_conta == id]
    if request.json:
        try:
            data_inicial = request.json['dataInicial']
            data_final = request.json['dataFinal']
            filter_list.extend([Transacoes.data_transacao >= data_inicial, Transacoes.data_transacao <= data_final])
        except Exception as e:
            return jsonify(
                {"message": ce.msg_params_invalid}), 403

    extratos = Transacoes.query.filter(*filter_list)

    resumo_extrato = {}
    for extrato in extratos:
        resumo_extrato[extrato.id_transacao] = {extrato.id_conta: {
            "idConta": extrato.id_conta,
            "idTransacao": extrato.id_transacao,
            "valor": extrato.valor,
            "dataTransacao": extrato.data_transacao
        }
    }
    if resumo_extrato == {}:
        return jsonify({"message": "Transacoes nao encontradas nesse periodo."})
    return jsonify(resumo_extrato)


# Path somente para debug
@app.route('/transacao/extrato', methods=['GET'])
def get_extrato_todos():
    extratos = Transacoes.query.all()

    resumo_extrato = {}
    for extrato in extratos:
        resumo_extrato[extrato.id_transacao] = {extrato.id_conta: {
            "idConta": extrato.id_conta,
            "idTransacao": extrato.id_transacao,
            "valor": extrato.valor,
            "dataTransacao": extrato.data_transacao
        }
    }
    if resumo_extrato == {}:
        return jsonify({"message": "Transacoes nao encontradas nesse periodo."})
    return jsonify(resumo_extrato)


@app.errorhandler(HTTPException)
def handle_bad_request(error):
    return jsonify({"message": "Bad Request or Invalid Parameters. Visit https://bit.ly/documentacao_dock"}), 400


@app.errorhandler(ce.InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
