# Design e arquitetura

Este documento resume as ideias centrais do design do Kafka, conforme a documentação oficial.

## Motivação

O Kafka foi pensado como uma **plataforma única** para feeds de dados em tempo real em grande escala. Isso exigiu:

- **Alto throughput** para grandes volumes de eventos (ex.: agregação de logs).
- **Suporte a grandes backlogs** para cargas periódicas de sistemas offline.
- **Baixa latência** para casos de mensageria mais tradicionais.
- **Processamento particionado e distribuído** para criar novos fluxos a partir dos existentes.
- **Tolerância a falhas** quando o fluxo alimenta outros sistemas.

O resultado é um design mais próximo de um **log de banco de dados** do que de um sistema de mensageria clássico.

## Persistência

### Uso do filesystem

O Kafka usa intensamente o **filesystem** para armazenar e cachear mensagens. Discos são lentos para seeks aleatórios, mas muito bons para leitura e escrita **sequencial**. O sistema operacional usa pagecache e técnicas de read-ahead/write-behind, então confiar no filesystem (e no pagecache) permite alto throughput e evita manter tudo em memória no processo. Dados escritos vão para um log persistente no filesystem (e para o pagecache do kernel).

### Operações em tempo constante

O log do Kafka é baseado em **append** e leitura sequencial, não em estruturas como B-tree. As operações são O(1), e o desempenho não degrada com o tamanho dos dados. Isso permite reter dados por muito tempo (ex.: uma semana) sem penalidade, dando flexibilidade aos consumers.

## Eficiência

Dois pilares da eficiência:

1. **Batching**: mensagens são agrupadas em “message sets”. Várias mensagens são enviadas em uma requisição, escritas em bloco no log e lidas em blocos grandes, reduzindo round-trips e I/O pequeno.
2. **Zero-copy**: o broker mantém o log no mesmo formato usado pelo producer e consumer. O sistema pode usar `sendfile` (ou equivalentes) para enviar dados do pagecache direto para a rede, reduzindo cópias de bytes.

A compressão (GZIP, Snappy, LZ4, ZStandard) é feita em **batch** de mensagens, o que melhora a taxa de compressão quando há repetição entre mensagens.

## O Producer

- **Balanceamento de carga**: o producer envia diretamente ao broker **líder** da partição. O cliente pode escolher a partição (aleatório ou por uma função da chave). Chaves iguais vão para a mesma partição, preservando ordem.
- **Envio assíncrono**: o producer acumula mensagens em memória e envia em lotes (por número de mensagens ou tempo, ex.: 64 KB ou 10 ms). Isso troca um pouco de latência por muito mais throughput.

## O Consumer

- **Pull, não push**: o consumer **busca** (pull) dados dos brokers, em vez de receber push. Assim o consumer controla o ritmo e não é sobrecarregado; o broker não precisa “adivinhar” a capacidade do consumer. O consumer pode fazer long poll (bloquear até chegar dado ou um limite de bytes).
- **Posição (offset)**: o consumer informa o **offset** de onde quer ler e recebe um trecho do log. Quem controla o progresso é o consumer (e o consumer group). O estado é apenas um número por partição, o que torna checkpoint e “replay” baratos.

## Resumo

| Aspecto | Ideia principal |
|--------|------------------|
| Persistência | Log no filesystem + pagecache; append e leitura sequencial |
| Eficiência | Batching, zero-copy, compressão em batch |
| Producer | Envia ao líder da partição; batching assíncrono; partição por chave |
| Consumer | Modelo pull; offset por partição; controle de ritmo pelo consumer |

## Referências

- [Design — Apache Kafka Documentation](https://kafka.apache.org/documentation/#design)
- [Persistence](https://kafka.apache.org/documentation/#design_persistence)
- [The Producer / The Consumer](https://kafka.apache.org/documentation/#design_producer)
