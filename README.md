# DOCUMENTAÇÃO PINPAD
Documentação, fluxo e exemplo de como utilizar nosso Pinpad em um terminal físico. Neste repositório também tem um exemplo em Python que poderá ser usado como base e também um fluxograma visual.

### DESCRIÇÃO DA INTEGRAÇÃO
Toda comunicação com nosso pinpad é feito via TCP, sendo assim não temos restrições de linguagem de programação. Toda comunicação é feita no formato JSON convertido em bytes, quando o Pinpad efetuar uma resposta ele no seguinte formato "startRow:JSON", pois pode vir mais de uma linha em um envio TCP conforme o exemplo:
"startRow:{ "errors": false, "errorDescription": null,"payload": {"id": ""}}"

### CLIENT DE EXEMPLO
Para rodar o exemplo é necessário ter o Python 3.9 e executar o comando abaixo:
```console
$ python client.py
```

### RESUMO DO FLUXO 
 1. Abrir conexão TCP
 2. Criar transação
 3. Abrir um loop e manter comunicação entre cliente e pinpad
 4. Imprimir comprovante
 5. Confirmar transação
 6. Encerrar conexão TCP

### CRIAR TRANSAÇÃO
Enviar um socket com o conteúdo em string utf-8.
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|endpoint|SIM|string|O valor deve ser create-transaction|
|payload|SIM|object| |
|payload.type|SIM|string|credit-card, debit-card, installment-credit-card|
|payload.amount|SIM|int|Valor da transação em centavos|
|payload.installmentDetail|NÃO|object|Obrigatório se o type for installment-credit-card|
|payload.installmentDetail.quantityIntallment|SIM|int|Quantidade de parcelas|
|payload.installmentDetail.entryAmount|NÃO|int|Valor de entrada em centavos|
Exemplo:
```json
//Request:
{
    "endpoint": "create-transaction",
    "payload": {
        "type": "credit-card|debit-card|installment-credit-card",
        "amount": 1000,
        "installmentDetail": {
            "quantityIntallment": 1,
            "entryAmount": 0
        }
    }
}
// Response:
{
	"errors": false,
	"errorDescription": null,
	"payload": {
		"id": "ID DA TRANSACAO"
	}
}
```

### EXIBINDO MENSAGENS NOS DISPLAYS
O Pinpad vai enviar mensagens para se exibir na tela do usuário, do operador ou de ambos.
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.text|SIM|string|Mensagem a ser exibida|
|payload.action.type|SIM|string|O type será o show-text-display|
|payload.action.showTo|SIM|string|Pode ser operator, customer ou both|
```json
{
	"payload": {
		"action": {
			"type": "show-text-display",
			"text": "APROXIME OU INSIRA O CARTÃO NO PINPAD",
			"showTo": "customer"
		}
	}
}
```

### Limpando os displays
O Pinpad vai pedir para apagar as mensagens do display.

|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|O type será o clear-display|
|payload.action.showTo|SIM|string|Pode ser operator, customer ou both|
```json
{
	"payload": {
		"action": {
			"type": "show-text-display",
			"showTo": "operator"
		}
	}
}
```

### RESPONDENDO O PINPAD
Após criar uma transação é necessário criar um loop que só será interrompido quando receber uma mensagem com o endpoint "finish-transaction", que nesse caso basta apenas confirmar a transação ou desfazer.
##### CONFIMAR
Em determinado momento o Pinpad pode efetuar uma pergunta de confirmação, sendo assim ele enviará a seguinte estrutura:
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.text|SIM|string|Será um pergunta de confirmação, que deverá ou ser confirmada ou não|
|payload.action.type|SIM|string|O type será o confirm nesse caso|
|payload.action.showTo|SIM|string|Será both|

```json
{
	"payload": {
		"action": {
			"type": "confirm",
			"text": "Você deseja confirmar o (...) ?",
			"showTo": "both"
		}
	}
}
```
Sua aplicação deve ou interpretar a pergunta e confirmar automaticamente ou exibir no display e deixar para o usuário se ele deseja confirmar ou não. Deve responder para o Pinpad com a seguinte estrutura:
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|endpoint|SIM|string|Deve preencher com continue-transaction|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Deve ser preenchida com confirm|
|payload.action.value|SIM|boolean|true para confirmar, false para não confirmar|
```json
{
	"endpoint": "continue-transaction",
	"payload": {
		"action": {
			"type": "confirm",
			"value": true
		}
	}
}
```

##### RESPONDENDO UM MENU
O Pinpad pode enviar uma lista de opções a qual deve ser exibida no display para que o usuário escolha alguma das opções, segue a estrutura:
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Será menu-question|
|payload.action.text|SIM|string|Será o titulo do menu|
|payload.action.options|SIM|string[]|Cada opção virá com o índice (número da opção) na frente que deve ser usado na hora da resposta|
|payload.action.showTo|SIM|string|Displays que serão exibidos|
```json
{
	'payload': {
	    "action": {
			"type": "menu-question",
			"text": "Escolha uma das opções",
			"options": [
			   "1 - Primeira opcao",
			   "2 - Segunda opcao",
			   "3 - Terceira opcao"
			],
			"showTo": 'both'
		}
	}
 }
```

A aplicação deve exibir a mensagem para o usuário e deixar ele escolher uma opção e responder ao pinpad com a seguinte estrutura:
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|endpoint|SIM|string|Deve preencher com continue-transaction|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Preencher com answer-menu|
|payload.action.answerOption|SIM|string|Se escolher a 3 - Terceira opcao deve se enviar apenas o número 3|
```json
{
	'payload': {
	    "action": {
			"type": "answer-menu",
			"answerOption": "3"
		}
	}
 }
```

##### RESPONDENDO UMA PERGUNTA
Eventualmente o Pinpad pode fazer uma pergunta do tipo "Digite os últimos quatro dígitos do cartão" ou algo do tipo, que deve ser uma resposta em texto.
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Preencher com question|
|payload.action.text|SIM|string|Pergunta|
|payload.action.showTo|SIM|string|Onde deve exibir a pergunta|
```json
{
	'payload': {
	    "action": {
			"type": "question",
			"text": "Digite os 4 últimos dígitos do cartão",
			"showTo": "both"
		}
	}
 }
```
Deverá responder com a estrutura 
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|endpoint|SIM|string|Deve preencher com continue-transaction|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Preencher com answer|
|payload.action.rawText|SIM|string|Resposta do usuário|
```json
{
	"endpoint": "continue-transaction",
	'payload': {
	    "action": {
			"type": "answer",
			"rawText": "1234"
		}
	}
 }
```

##### RESPONDENDO SE DESEJA CONTINUAR
Com uma certa frequência o Pinpad vai perguntar se deseja ou não continuar a transação.
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|será preenchido com continue|
```json
{
	'payload': {
	    "action": {
			"type": "continue"
		}
	}
 }
```
Deverá responder com a estrutura
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|endpoint|SIM|string|Deverá ser preenchido com continue-transaction|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Preencher com continue|
|payload.action.value|SIM|boolean|True se quer continuar False se deseja abortar a operação|
```json
{
	'payload': {
	    "action": {
			"type": "continue",
			"value": true
		}
	}
 }
```

### TRANSAÇÃO APROVADA
Após uma transação ser aprovada, deverá imprimir o comprovante ou exibir na tela e essa transação deve ser confirmado, mas caso ocorra algum erro na impressora ou algo do tipo a aplicação. Segue a estrutura que o Pinpad enviará:
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Será transaction-approved|
|payload.action.receipt|SIM|string|Recibo em string|
```json
{
	'payload': {
	    "action": {
			"type": "transaction-approved",
			"receipt": "COMPROVANTE\nLINHA1\nLINHA2"
		}
	}
 }
```

A aplicação deverá responder com a estrutura:
|CAMPO|OBRIGATORIO|TIPO|OBS| 
|--|--|--|--|
|endpoint|SIM|string|Preencher com finish-transaction|
|payload|SIM|object| |
|payload.action|SIM|object| |
|payload.action.type|SIM|string|Preencher com finish-transaction para confirmar a transação ou undo-transaction para desfazer|
```json
{
	'payload': {
	    "action": {
			"type": "finish-transaction ou undo-transaction",
		}
	}
 }
```
