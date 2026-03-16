# Design e arquitetura

Este documento resume aspectos centrais do **design** do RabbitMQ: conexões, canais, virtual hosts e modelo de entrega (push).

## Conexões (connections)

- **AMQP 0-9-1** roda sobre **TCP**; cada cliente mantém uma **conexão** longa com o broker.
- Conexões usam **autenticação** e podem ser protegidas com **TLS**.
- Quando a aplicação não precisar mais do broker, deve **fechar a conexão de forma graciosa** (close AMQP) em vez de apenas derrubar o TCP, para o broker liberar recursos e encerrar canais corretamente.

## Canais (channels)

- Abrir muitas **conexões TCP** (uma por thread ou por operação) consome recursos e complica firewall. O AMQP **multiplexa** várias sessões lógicas em uma mesma conexão por meio de **canais (channels)**.
- Cada **operação** do protocolo (publicar, consumir, declarar queue, etc.) ocorre em um **canal**. Cada método AMQP carrega um **channel ID** para o broker e o cliente saberem a qual canal a operação pertence.
- Um canal existe apenas no contexto de uma conexão; ao fechar a conexão, todos os canais são fechados.
- **Boas práticas**: reutilizar **uma conexão** por processo e abrir **um canal por thread** (ou por fluxo de trabalho), sem compartilhar o mesmo canal entre threads.

## Virtual hosts (vhosts)

- **Virtual hosts** são namespaces de isolamento no mesmo broker: usuários, exchanges, queues e bindings pertencem a um vhost.
- O cliente escolhe o **vhost** na negociação da conexão (ex.: `/` é o default). Recursos de um vhost não são visíveis em outro; é possível ter `/producao` e `/homolog` no mesmo broker.
- Permite **multi-tenancy** e separação lógica de ambientes sem precisar de vários brokers.

## Modelo push (entrega pelo broker)

- No AMQP, o modelo recomendado é **push**: o consumer **se inscreve** em uma queue e o **broker entrega** as mensagens quando chegam (ou quando há mensagens disponíveis).
- Existe também **basic.get** (pull / polling), mas a documentação desaconselha para a maioria dos casos: é menos eficiente e aumenta latência. O push permite que o broker envie assim que houver mensagem e que o consumer controle a carga via **prefetch**.

## Resumo

| Aspecto | Ideia principal |
|--------|-------------------|
| Conexões | Longas, autenticadas, preferencialmente com TLS; fechar graciosamente |
| Canais | Multiplexam operações em uma conexão; um canal por thread, não compartilhar entre threads |
| Virtual hosts | Isolamento lógico (queues, exchanges, usuários) no mesmo broker |
| Entrega | Modelo push (inscrição na queue); pull (basic.get) não recomendado |

## Referências

- [Connections — RabbitMQ](https://www.rabbitmq.com/docs/connections)
- [Channels — RabbitMQ](https://www.rabbitmq.com/docs/channels)
- [Virtual Hosts — RabbitMQ](https://www.rabbitmq.com/docs/vhosts)
- [AMQP 0-9-1 Model — Consumers](https://www.rabbitmq.com/tutorials/amqp-concepts.html#consumers)
