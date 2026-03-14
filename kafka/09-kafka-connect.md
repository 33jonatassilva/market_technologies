# Kafka Connect

O **Kafka Connect** é o framework do ecossistema Kafka para **integrar o cluster com sistemas externos** de forma contínua: importar dados para o Kafka (source) e exportar do Kafka para outros sistemas (sink).

## Visão geral

- **Connect** roda como um serviço (workers): em modo **standalone** (um processo) ou **distributed** (vários workers formando um cluster).
- **Conectores** (connectors) são os componentes que sabem falar com um sistema específico (PostgreSQL, S3, Elasticsearch, etc.). Cada connector é configurado com um nome, classe e parâmetros (tópicos, tabelas, credenciais, etc.).
- Você **não precisa escrever código** na maioria dos casos: a comunidade e fornecedores oferecem centenas de conectores prontos.

## Source e Sink

| Tipo | Direção | Exemplo |
|------|---------|---------|
| **Source** | Sistema externo → Kafka | Lê alterações de um banco (CDC) e publica em um tópico |
| **Sink** | Kafka → Sistema externo | Lê de um tópico e grava em um data lake ou em outra fila |

Um mesmo cluster pode ter vários source e sink connectors rodando ao mesmo tempo.

## Conceitos principais

- **Connector**: define *o que* fazer (qual sistema, quais tópicos/tabelas, etc.). Cria e gerencia **tasks**.
- **Task**: unidade de trabalho que efetivamente lê ou escreve dados. Um connector pode criar várias tasks para paralelismo.
- **Worker**: processo que executa connectors e tasks. No modo distributed, os workers se coordenam para distribuir o trabalho.
- **Converters / Serializers**: formato dos dados no Kafka (JSON, Avro, etc.). Configurados no worker ou por connector.

## Uso típico (sem código)

1. Instalar ou disponibilizar o JAR (ou plugin) do connector no **plugin.path** do worker.
2. Configurar o worker (bootstrap servers, converters, etc.).
3. Criar uma instância do connector via REST API ou arquivo de configuração (nome, classe, connection URL, tópicos, etc.).
4. O Connect inicia as tasks; os dados fluem continuamente entre o sistema externo e o Kafka.

Exemplo de fluxo: um **source** lê de um arquivo ou banco e escreve em um tópico; um **sink** lê desse tópico e grava em outro arquivo ou sistema. O Quick Start oficial mostra esse fluxo com conectores de arquivo.

## Desenvolvimento de conectores

Quem precisa integrar um sistema sem connector pronto usa a **Connect API**: implementar `SourceConnector` / `SinkConnector` e as classes **Task** correspondentes. A documentação oficial traz o [Connector Development Guide](https://kafka.apache.org/documentation/#connect_development) para isso.

## Referências

- [Kafka Connect — Apache Kafka](https://kafka.apache.org/documentation/#connect)
- [Connect Overview](https://kafka.apache.org/documentation/#connect_overview)
- [Connect User Guide](https://kafka.apache.org/documentation/#connect_userguide)
