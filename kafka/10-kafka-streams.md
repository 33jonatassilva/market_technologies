# Kafka Streams

O **Kafka Streams** é uma biblioteca de **processamento de streams** (Java/Scala) que usa o Kafka como armazenamento e transporte. A entrada e a saída são tópicos Kafka; a aplicação roda nos seus próprios processos (não dentro do cluster).

## Características

- **Cliente**: sua aplicação é um consumer e producer; não precisa de cluster de processamento separado.
- **Escalável e tolerante a falhas**: escala com mais instâncias; usa consumer groups e estado local (stores) com changelog em tópicos Kafka.
- **Exactly-once**: suporta processamento exatamente uma vez quando configurado corretamente (transações, state stores com changelog).
- **Operações ricas**: filtros, map, agregações, joins (stream-stream, stream-table, table-table), janelas (tempo, sessão), processamento por event-time.

## Conceitos principais

- **KStream**: fluxo de eventos (chave-valor) “ilimitado”; cada record é independente (ex.: cliques, pedidos).
- **KTable**: visão “atual” por chave; representa um snapshot ou changelog (ex.: saldo por conta, último valor por sensor). Atualizado quando chega um novo record para a mesma chave.
- **Topology**: grafo de operações (sources → transformações → sinks). Você monta a topology no código e a biblioteca a executa.

Exemplo conceitual (Word Count): ler um stream de linhas de texto → quebrar em palavras → agrupar por palavra → contar → escrever o resultado em um tópico (KTable convertida em stream).

## Quando usar

- Microserviços que reagem a eventos em tempo real (enriquecimento, agregação, alertas).
- Pipelines de dados em tempo real (ETL, CEP).
- Manter estado derivado (agregações, joins) com backup no Kafka via changelog topics.

O Kafka Streams é uma das formas de implementar exatamente-uma-vez “read → process → write” dentro do ecossistema Kafka, pois coordena consumer offset, state stores e producer transacional.

## Referências

- [Kafka Streams — Apache Kafka](https://kafka.apache.org/documentation/streams/)
- [Streams Introduction](https://kafka.apache.org/documentation/streams/#streams_intro)
- [Streams Developer Guide](https://kafka.apache.org/documentation/streams/developer-guide/)
