# Quick Start

Este é um resumo dos passos para subir um ambiente Kafka local e testar o básico. Para detalhes e opções, use a [documentação oficial](https://kafka.apache.org/quickstart).

## Pré-requisitos

- **Java 17+** instalado (para rodar o Kafka com os scripts oficiais).

## 1. Obter o Kafka

Baixe o release (ex.: 4.2.0) e extraia:

```bash
tar -xzf kafka_2.13-4.2.0.tgz
cd kafka_2.13-4.2.0
```

## 2. Iniciar o ambiente

### Com arquivos (KRaft, standalone)

Gerar um Cluster UUID e formatar os diretórios de log:

```bash
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format --standalone -t $KAFKA_CLUSTER_ID -c config/server.properties
```

Iniciar o servidor:

```bash
bin/kafka-server-start.sh config/server.properties
```

### Com Docker

```bash
docker pull apache/kafka:4.2.0
docker run -p 9092:9092 apache/kafka:4.2.0
```

## 3. Criar um tópico

Em outro terminal (ajuste o caminho se necessário):

```bash
bin/kafka-topics.sh --create --topic quickstart-events --bootstrap-server localhost:9092
```

Ver detalhes do tópico (partições, líder, etc.):

```bash
bin/kafka-topics.sh --describe --topic quickstart-events --bootstrap-server localhost:9092
```

## 4. Escrever eventos (console producer)

```bash
bin/kafka-console-producer.sh --topic quickstart-events --bootstrap-server localhost:9092
```

Digite algumas linhas (cada linha = um evento) e encerre com `Ctrl-C`.

## 5. Ler os eventos (console consumer)

```bash
bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092
```

Você deve ver as mensagens escritas no passo anterior. Encerre com `Ctrl-C`.

## 6. Kafka Connect (opcional)

O Quick Start oficial mostra como rodar o Connect em modo standalone com conectores de arquivo (source: arquivo → tópico; sink: tópico → arquivo). É preciso configurar o `plugin.path` em `config/connect-standalone.properties` e subir:

```bash
bin/connect-standalone.sh config/connect-standalone.properties config/connect-file-source.properties config/connect-file-sink.properties
```

## 7. Kafka Streams (opcional)

A documentação inclui um exemplo de aplicação Kafka Streams (ex.: Word Count) que lê de um tópico, processa e escreve em outro. Consulte o [Streams Quick Start](https://kafka.apache.org/documentation/streams/quickstart) e o [tutorial](https://kafka.apache.org/documentation/streams/tutorial) para código completo.

## 8. Encerrar

- Parar o broker (e Connect/Streams, se estiverem rodando) com `Ctrl-C`.
- Para apagar todos os dados locais (logs):

```bash
rm -rf /tmp/kafka-logs /tmp/kraft-combined-logs
```

## Próximo passo

Depois de rodar o Quick Start, vale revisar [Operações e monitoramento](12-operacoes-e-monitoramento.md) e a documentação oficial de configuração e produção.

## Referências

- [Quick Start — Apache Kafka](https://kafka.apache.org/quickstart)
- [Download Kafka](https://kafka.apache.org/community/downloads/)
