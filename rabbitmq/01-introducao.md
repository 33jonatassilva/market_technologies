# Introdução ao RabbitMQ

## O que é um message broker?

Um **message broker** (intermediário de mensagens) é um sistema que recebe mensagens de aplicações produtoras (**publishers**) e as entrega às aplicações consumidoras (**consumers**). Ele desacopla quem produz daquele que consome: o publisher não precisa conhecer quantos consumers existem nem onde estão; o consumer não precisa saber quem publicou a mensagem.

Em resumo: garantir que a mensagem certa chegue ao destino certo, de forma confiável e assíncrona.

## Para que serve um message broker?

Alguns exemplos de uso:

- **Filas de tarefas**: distribuir trabalho entre vários workers (ex.: processamento de imagens, envio de e-mails).
- **Desacoplamento entre microserviços**: um serviço publica eventos; outros assinam apenas o que lhes interessa.
- **Broadcast**: notificar vários sistemas sobre o mesmo evento (ex.: “pedido criado” → estoque, notificações, analytics).
- **Roteamento por padrão**: entregar mensagens só para quem se inscreveu em certos “tópicos” (ex.: `pedidos.*.pago`).
- **Resiliência**: mensagens persistem até serem processadas; se um consumer cair, outra instância pode pegar a mensagem.

## O que é o RabbitMQ?

O **RabbitMQ** é um **message broker** que implementa o protocolo **AMQP 0-9-1** (Advanced Message Queuing Protocol). Ele oferece:

1. **Roteamento flexível**: mensagens são publicadas em **exchanges** e encaminhadas a **queues** por regras (**bindings**), com vários tipos de exchange (direct, fanout, topic, headers).
2. **Armazenamento em filas**: as mensagens ficam em **queues** até serem consumidas, com suporte a durabilidade e persistência em disco.
3. **Confiabilidade**: acknowledgements (confirmações) garantem que mensagens só são removidas da fila após processamento; publicador pode usar **publisher confirms** para saber se a mensagem foi aceita pelo broker.

Tudo isso de forma **escalável**, com **clustering** e **quorum queues** para alta disponibilidade, e suporte a múltiplos protocolos além do AMQP (MQTT, STOMP, etc., via plugins).

## Como o RabbitMQ funciona em poucas palavras?

O RabbitMQ é um servidor (broker) que implementa o modelo AMQP:

- **Publishers** enviam mensagens para **exchanges** (não diretamente para filas).
- **Exchanges** roteiam as mensagens para uma ou mais **queues** com base no **tipo do exchange** e nas **bindings** (regras que ligam exchange → queue).
- **Consumers** se inscrevem em **queues** e recebem mensagens (modelo **push**: o broker entrega quando há mensagem disponível).
- **Conexões** são longas; dentro delas, **canais** (channels) multiplexam as operações, evitando muitas conexões TCP.

O protocolo é **programável**: as aplicações declaram exchanges, queues e bindings; não é obrigatório que um administrador crie tudo manualmente.

## Próximo passo

No próximo documento você verá os **conceitos e a terminologia** do RabbitMQ: mensagens, publishers, consumers, exchanges, queues e bindings.

## Referências

- [RabbitMQ Documentation](https://www.rabbitmq.com/docs)
- [What is AMQP?](https://www.rabbitmq.com/tutorials/amqp-concepts.html)
- [Introduction — RabbitMQ](https://www.rabbitmq.com/docs#introduction)

