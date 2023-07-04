import tkinter as tk
from tkinter import ttk
import socket
from json import dumps, loads
from tkinter import messagebox
import threading

HOST = '127.0.0.1'
PORT = 12345

CREDIT_CARD_OPERATION = 'credit-card'
DEBIT_CARD_OPERATION = 'debit-card'
INSTALLMENT_CREDIT_CARD_OPERATION = 'installment-credit-card'

root = tk.Tk()
root.geometry("800x600")

div_1 = tk.Label(root, text="------")
div_1.pack()

label_title_operador = tk.Label(root, text="DISPLAY OPERADOR")
label_title_operador.pack()

display_operador = tk.Label(root, text="")
display_operador.pack()

div_2 = tk.Label(root, text="------")
div_2.pack()

title_cliente = tk.Label(root, text="DISPLAY CLIENTE")
title_cliente.pack()

display_cliente = tk.Label(root, text="")
display_cliente.pack()

div_3 = tk.Label(root, text="------")
div_3.pack()

title = tk.Label(root, text="Digite um valor")
title.pack()
input_value = tk.Text(root, height = 2, width = 20)
input_value.pack()

title_parcela = tk.Label(root, text="Digite a quantidade de parcela")
title_parcela.pack()
input_parcela = tk.Text(root, height = 2, width = 20)
input_parcela.pack()

title_valor_entrada = tk.Label(root, text="Digite o valor de entrada")
title_valor_entrada.pack()
input_valor_entrada = tk.Text(root, height = 2, width = 20)
input_valor_entrada.pack()

div_4 = tk.Label(root, text="------")
div_4.pack()

combo_box = ttk.Combobox(root, values=["Crédito", "Débito"])
combo_box.set("Crédito")
combo_box.pack()

div_5 = tk.Label(root, text="------ XXXX ------")
div_5.pack()

receipt = tk.Label(root, text="")
receipt.pack()
recibo = ''


def payload_create_transaction(operation, amount, parcelas, valor_entrada):
    if int(parcelas) > 1:
        payload = {
            "endpoint": "create-transaction",
            "payload": {
                "type": operation,
                "amount": amount,
                "installmentDetail": {
                    'quantityIntallment': parcelas
                }
            }
        }
        if valor_entrada:
            payload['payload']['installmentDetail']['entryAmount'] = valor_entrada

        return bytes(dumps(payload), "utf-8")
    else:
        payload = {
            "endpoint": "create-transaction",
            "payload": {
                "type": operation,
                "amount": amount,
                "installments": 1
            }
        }
        return bytes(dumps(payload), "utf-8")

def payload_confirm_create(confirm: bool):
    payload = {
        "endpoint": "continue-transaction",
        "payload": {
            "action": {
                "type": "confirm",
                "value": confirm
            }
        }
    }
    return bytes(dumps(payload), "utf-8")

def payload_answer_menu_create(option):
    payload = {
        "endpoint": "continue-transaction",
        "payload": {
            "action": {
                "type": "answer-menu",
                "answerOption": option
            }
        }
    }
    return bytes(dumps(payload), "utf-8")

def payload_answer_create(response):
    payload = {
        "endpoint": "continue-transaction",
        "payload": {
            "action": {
                "type": "answer",
                "rawText": response
            }
        }
    }
    return dumps(payload).encode()

def payload_continue_create(response):
    payload = {
        "endpoint": "continue-transaction",
        "payload": {
            "action": {
                "type": "continue",
                "value": True if response else False
            }
        }
    }
    return dumps(payload).encode()

def payload_finish_transaction(finish):
    payload = {
        "endpoint": "finish-transaction",
        "payload": {
            'action': 'finish-transaction' if finish else 'undo-transaction'
        }
    }
    return dumps(payload).encode()

def start_transaction():
    amount = input_value.get(1.0, "end-1c")
    parcelas = input_parcela.get(1.0, "end-1c") if input_parcela.get(1.0, "end-1c") != '' else 1
    valor_entrada = input_valor_entrada.get(1.0, "end-1c")
    display_cliente.config(text='Iniciando transação ...')

    if int(parcelas) > 1 and combo_box.get() == 'Débito':
        display_cliente.config(text='Compras no débito não podem ser parceladas')
        display_operador.config(text='Compras no débito não podem ser parceladas')
        return

    receipt.config(text='')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        if int(parcelas) > 1:
            operation = INSTALLMENT_CREDIT_CARD_OPERATION
        elif combo_box.get() == 'Crédito':
            operation = CREDIT_CARD_OPERATION
        else:
            operation = DEBIT_CARD_OPERATION

        create_transaction_payload = payload_create_transaction(operation, amount, parcelas, valor_entrada)

        s.sendall(create_transaction_payload)

        count_continue = 0

        while True:
            data_received = s.recv(6096)
            if not data_received:
                continue
            payloads = data_received.decode().split('startRow:')
            del payloads[0]
            for data in payloads:
                data = loads(data)
                print(data)
                if 'errors' in data and data['errors']:
                    display_cliente.config(text=data['errorDescription'])
                    display_operador.config(text=data['errorDescription'])
                    break
                
                if data['payload']['action']['type'] == 'show-text-display':
                    if data['payload']['action']['showTo'] == 'both':
                        display_cliente.config(text=data['payload']['action']['text'])
                        display_operador.config(text=data['payload']['action']['text'])
                    elif data['payload']['action']['showTo'] == 'customer':
                        display_cliente.config(text=data['payload']['action']['text'])
                    else:
                        display_operador.config(text=data['payload']['action']['text'])

                if data['payload']['action']['type'] == 'clear-display':
                    if data['payload']['action']['showTo'] == 'both':
                        display_cliente.config(text="")
                        display_operador.config(text="")
                    elif data['payload']['action']['showTo'] == 'customer':
                        display_cliente.config(text="")
                    else:
                        display_operador.config(text="")
                
                if data['payload']['action']['type'] == 'confirm':
                    result = messagebox.askyesno("Confirmar", data['payload']['action']['text'])
                    s.sendall(payload_confirm_create(result))

                if data['payload']['action']['type'] == 'continue':
                    count_continue = count_continue + 1
                    if count_continue < 100:
                        s.sendall(payload_continue_create(True))
                    else:
                        result = messagebox.askyesno("Continuar transação", 'Deseja continuar a transação')
                        s.sendall(payload_continue_create(result))

                
                if data['payload']['action']['type'] == 'menu-question':
                    display_cliente.config(text=data['payload']['action']['text'])
                    display_operador.config(text=data['payload']['action']['text'])

                    options = ''
                    for option in data['payload']['action']['options']:
                        options = options + option + '\n'

                    title_menu = tk.Label(root, text=options)
                    title_menu.pack()
                    input_menu = tk.Text(root, height = 2, width = 20)
                    input_menu.pack()
                    
                    def continue_transaction():
                        picked_option = input_menu.get(1.0, "end-1c")
                        print(payload_answer_menu_create(picked_option))
                        s.sendall(payload_answer_menu_create(picked_option))

                    menu_button = tk.Button(root, text = "Escolher", command = continue_transaction)
                    menu_button.pack()

                if data['payload']['action']['type'] == 'question':
                    display_cliente.config(text=data['payload']['action']['text'])
                    display_operador.config(text=data['payload']['action']['text'])
                    input_question = tk.Text(root, height = 2, width = 20)
                    input_question.pack()
                    
                    def continue_transaction():
                        answer = input_question.get(1.0, "end-1c")
                        s.sendall(payload_answer_create(answer))

                    menu_button = tk.Button(root, text = "Responder", command = continue_transaction)
                    menu_button.pack()

                if data['payload']['action']['type'] == 'transaction-approved':
                    display_cliente.config(text='Transação aprovada')
                    display_operador.config(text='Transação aprovada')
                    result = messagebox.askyesno("Finalizar", 'Deseja finalizar?')
                    receipt.config(text=data['payload']['action']['receipt'])
                    s.sendall(payload_finish_transaction(result))
                    break


def loop_1():
    loop_1_thread = threading.Thread(target=start_transaction)
    loop_1_thread.start()


start_transaction_button = tk.Button(root, text = "Iniciar transação", command = loop_1)
start_transaction_button.pack()

root.mainloop()