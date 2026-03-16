# Comparativo: Apache Kafka vs RabbitMQ

Este documento compara **Apache Kafka** e **RabbitMQ** com base nas documentações oficiais e no material disponível nas pastas [kafka/](kafka/) e [rabbitmq/](rabbitmq/) deste repositório. O objetivo é ajudar a escolher a ferramenta mais adequada conforme o caso de uso.

---

## 1. Natureza e propósito

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Classificação** | Plataforma de **event streaming** | **Message broker** (intermediário de mensagens) |
| **Protocolo** | Protocolo próprio sobre TCP (e APIs) | AMQP 0-9-1 (e outros via plugins: MQTT, STOMP) |
| **Modelo mental** | Log distribuído, append-only; eventos são registros num log que pode ser relido | Filas e roteamento; mensagem é entregue a consumidores e removida após ack |
| **Foco** | Alto throughput, retenção longa, replay, processamento de streams | Entrega confiável, roteamento flexível, filas de tarefas, pub/sub |

- **Kafka**: pensado para **fluxos de eventos** em grande escala — capturar, armazenar e processar eventos (logs, métricas, eventos de negócio), com possibilidade de **replay** e múltiplos consumidores independentes.
- **RabbitMQ**: pensado para **mensageria** — desacoplar produtores e consumidores, rotear mensagens (direct, fanout, topic, headers), garantir entrega e distribuir trabalho em filas.

---

## 2. Modelo de dados e roteamento

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Unidade principal** | **Topic** (log particionado) | **Exchange** + **Queue** (roteamento + armazenamento) |
| **Roteamento** | Producer escolhe partição (por chave ou round-robin); consumer lê de partições atribuídas | Publisher envia ao **exchange**; exchange roteia para **queues** por tipo (direct, fanout, topic, headers) e **bindings** |
| **Armazenamento** | Eventos ficam no **log** do tópico (por tempo ou tamanho); **não são apagados** após leitura (retenção configurável) | Mensagens ficam na **queue** até serem consumidas e **confirmadas** (ack); depois são removidas |
| **Múltiplos consumidores** | Vários **consumer groups** podem ler o mesmo tópico de forma independente (cada um com seu offset) | Vários consumers na **mesma queue** compartilham as mensagens (uma mensagem → um consumer); para “uma cópia para cada um”, usa-se uma **queue por consumer** ligada a um exchange (ex.: fanout) |

- **Kafka**: não há conceito de “exchange”; o produtor publica num **topic** (e opcional partição). Quem quer “filtrar” por tipo de evento usa **tópicos separados** ou **consumo seletivo** (e.g. por partição ou por processamento no consumer).
- **RabbitMQ**: o **exchange** é o ponto de entrada; a topologia (queues + bindings) define quem recebe o quê. Muito flexível para padrões request/reply, work queue, pub/sub, routing por tópico ou headers.

---

## 3. Entrega e consumo

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Modelo de entrega** | **Pull**: consumer busca (fetch) dados do broker | **Push**: broker entrega mensagens ao consumer quando há disponível |
| **Progresso do consumer** | **Offset** por partição; consumer controla de onde ler; permite **replay** | Mensagem removida após **ack**; não há replay nativo (mensagem sai da fila) |
| **Ordem** | Ordem **por partição** (eventos com mesma chave na mesma partição); entre partições não há ordem global | Ordem **por queue** (FIFO na queue); entre queues depende do roteamento |
| **Semânticas** | At-most-once, at-least-once, exactly-once (com transações e idempotência) | At-most-once (auto ack), at-least-once (manual ack); exactly-once exige idempotência no consumer |
| **Confirmações** | Producer: acks (0, 1, all); consumer: commit de offset | Publisher: **publisher confirms**; consumer: **basic.ack** / **basic.nack** |

- **Kafka**: ideal quando você precisa **reler** o mesmo stream (novo consumer group, reprocessamento, analytics). O consumer “puxa” e controla o ritmo.
- **RabbitMQ**: ideal quando a mensagem deve ser **processada uma vez** e removida; o broker “empurra” e o consumer confirma.

---

## 4. Persistência e retenção

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Persistência** | Log em disco (append-only); alto throughput por I/O sequencial e batching | Mensagens podem ser **persistent** (disco); queues **durable**; metadados em disco |
| **Retenção** | Por **tempo** e/ou **tamanho** por tópico (ex.: 7 dias, 1 GB); dados antigos podem ser compactados (log compaction) ou removidos | Mensagens permanecem até **consumo + ack**; opcional **TTL** (por mensagem ou por queue) para expirar mensagens não consumidas |
| **Replay** | **Sim**: novo consumer (ou novo group) pode ler do início ou de um offset arbitrário | **Não**: após entrega e ack, a mensagem sai da fila |

- **Kafka**: armazena o **histórico** do stream; suporta retenção longa e múltiplos consumidores em momentos diferentes.
- **RabbitMQ**: armazena mensagens **até o consumo**; não é um log de eventos reutilizável.

---

## 5. Escalabilidade e desempenho

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Particionamento** | **Partições** por tópico; paralelismo de leitura/escrita por partição; escala horizontal adicionando brokers e partições | **Queues** são a unidade; múltiplos consumers na mesma queue distribuem a carga; escala horizontal com mais nós no cluster e mais consumers |
| **Throughput** | Muito alto para **grandes volumes** de eventos (milhões de msgs/s em clusters grandes); batching, zero-copy, log sequencial | Alto para filas de mensagens; pode ser limitado pelo disco e pela complexidade do roteamento (muitas bindings, muitos destinos) |
| **Latência** | Tipicamente **alguns ms** (batching pode aumentar um pouco); otimizado para throughput | **Sub-ms** a poucos ms em cenários simples; adequado para filas de tarefas e mensageria tradicional |

- **Kafka**: melhor para **grandes volumes** e **streams** que podem crescer no tempo (logs, eventos, pipelines de dados).
- **RabbitMQ**: muito bom para **filas de trabalho**, **roteamento rico** e cenários onde a mensagem é “consumida e esquecida”.

---

## 6. Alta disponibilidade e replicação

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Replicação** | **Partições replicadas** em vários brokers; líder + followers; escrita no líder, réplicas sincronizadas (ISR) | **Quorum queues** (Raft) replicadas em nós do cluster; classic mirrored queues foram descontinuadas |
| **Consenso** | Líder por partição; commit quando réplicas in-sync confirmam | Raft; quorum (maioria) confirma mensagens |
| **Tolerância a falhas** | Até f-1 falhas com f réplicas; rebalance de líder quando necessário | Quorum: sobrevive a falha de minoria dos nós da queue |

Ambos oferecem **HA** em cluster; Kafka é maduro em clusters muito grandes e multi-datacenter; RabbitMQ é forte em clusters de tamanho pequeno/médio com quorum queues.

---

## 7. Ecossistema e uso típico

| Aspecto | Apache Kafka | RabbitMQ |
|--------|----------------|----------|
| **Uso típico** | Event streaming, pipelines de dados, CEP, integração de sistemas (logs, métricas, eventos de negócio), replay, analytics em tempo real | Filas de tarefas, desacoplamento entre serviços, pub/sub, roteamento por tópico/headers, request/reply |
| **Extensões** | Kafka Connect (source/sink), Kafka Streams (processamento), Schema Registry | Plugins: Management, Federation, Shovel, MQTT, STOMP, etc. |
| **Operação** | Mais complexa (brokers, partições, retenção, consumer groups, KRaft/ZooKeeper) | Mais simples para começar; Management UI e HTTP API amigáveis; cluster e quorum queues para HA |

---

## 8. Quando usar qual?

### Prefira **Kafka** quando:

- Você precisa de **event streaming**: capturar, armazenar e processar fluxos de eventos em grande volume.
- **Replay** é importante: vários consumidores ou reprocessamento a partir de um ponto no tempo.
- **Retenção longa** de eventos (dias/semanas) é requisito.
- Há necessidade de **processamento de stream** (agregações, joins, janelas) com Kafka Streams ou similar.
- O modelo é “log” e “offset”, não “fila que esvazia após consumo”.

### Prefira **RabbitMQ** quando:

- O foco é **mensageria** e **filas de tarefas**: uma mensagem processada e removida.
- Você precisa de **roteamento rico**: direct, fanout, topic, headers, exchange-to-exchange.
- **Latência baixa** e padrões clássicos (work queue, pub/sub, request/reply) são suficientes.
- O ecossistema já usa AMQP ou você quer um broker leve de configurar e operar (Management UI, menos conceitos que Kafka).
- Não há necessidade de replay nem de retenção longa do mesmo “stream”.

### Ambos podem conviver:

- **RabbitMQ** para filas operacionais (pedidos, notificações, jobs).
- **Kafka** para streams de eventos (auditoria, analytics, pipelines de dados, CEP).

---

## 9. Resumo em uma tabela

| Critério | Kafka | RabbitMQ |
|----------|--------|----------|
| Modelo | Log de eventos (stream) | Filas + roteamento (message broker) |
| Entrega | Pull (consumer busca) | Push (broker entrega) |
| Replay | Sim (offset por partição) | Não (mensagem removida após ack) |
| Roteamento | Por tópico/partição | Por exchange + bindings (direct, fanout, topic, headers) |
| Retenção | Longa (configurável por tópico) | Até consumo (+ TTL opcional) |
| Throughput | Muito alto (milhões/s) | Alto (adequado a filas e pub/sub) |
| Complexidade operacional | Maior | Menor para começar |
| Exactly-once | Suportado (transações + idempotência) | Via idempotência no consumer |
| HA | Réplicas de partição (ISR) | Quorum queues (Raft) |

---

## Referências

- Documentação e arquivos em [kafka/](kafka/) e [rabbitmq/](rabbitmq/) deste repositório.
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/docs)
- [AMQP 0-9-1 Model Explained](https://www.rabbitmq.com/tutorials/amqp-concepts.html)
