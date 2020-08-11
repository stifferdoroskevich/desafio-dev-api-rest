from api import app, db
from flask import request, jsonify
from api.models.db_creation import Contas, Transacoes


@app.route('/')
def home():
    return "Welcome to DOCK!"


@app.route('/contas', methods=['POST'])
def new_conta():
    id_pessoa = request.json['idPessoa']
    saldo = request.json['saldo']
    limite_saque_diario = request.json['limiteSaqueDiario']
    flag_ativo = request.json['flagAtivo']
    tipo_conta = request.json['tipoConta']

    conta = Contas(id_pessoa, saldo, limite_saque_diario, flag_ativo, tipo_conta)
    db.session.add(conta)
    db.session.commit()

    if conta:
        return "200"


@app.route('/contas/<id>', methods=['GET'])
def get_saldo(id):
    conta = Contas.query.get(id)
    if conta:
        valor_saldo = {id: {
            'saldo': conta.saldo
        }}
    return jsonify(valor_saldo)


@app.route('/contas/<id>/inativar', methods=['PUT'])
def inativar_conta(id):
    conta = Contas.query.get(id)
    conta.flag_ativo = False
    db.session.commit()

    return "Conta Inativada!"


@app.route('/transacao/deposito', methods=['POST'])
def deposito():
    id_conta = request.json['idConta']
    valor = request.json['valor']

    transacao = Transacoes(id_conta, valor)
    conta = Contas.query.get(id_conta)
    conta.saldo = conta.saldo + valor
    db.session.add(transacao, conta)
    db.session.commit()

    if transacao:
        return "200"


@app.route('/transacao/saque', methods=['POST'])
def saque():
    id_conta = request.json['idConta']
    valor = request.json['valor']
    conta = Contas.query.get(id_conta)

    if valor > conta.saldo:
        return "Saldo Insuficiente"
    if valor > conta.limite_saque_diario:
        return "valor superior ao limite diario"

    conta.saldo = conta.saldo - valor
    transacao = Transacoes(id_conta, -valor)
    db.session.add(transacao, conta)
    db.session.commit()

    if transacao:
        return "200"


@app.route('/transacao/<id>', methods=['GET'])
def get_extrato_conta(id):
    data_inicial = request.json['dataInicial']
    data_final = request.json['dataFinal']
    extratos = Transacoes.query.filter(
        Transacoes.id_conta == id,
        Transacoes.data_transacao <= data_final,
        Transacoes.data_transacao >= data_inicial)
    resumo_extrato = {}
    for extrato in extratos:
        resumo_extrato[extrato.id_transacao] = {extrato.id_conta: {
            "idConta": extrato.id_conta,
            "idTransacao": extrato.id_transacao,
            "valor": extrato.valor,
            "dataTransacao": extrato.data_transacao
        }
    }
    return jsonify(resumo_extrato)
