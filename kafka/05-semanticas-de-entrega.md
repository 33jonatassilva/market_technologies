# Semânticas de entrega

As **garantias de entrega** dizem o que acontece com uma mensagem do ponto de vista do producer e do consumer: se pode ser perdida, duplicada ou processada exatamente uma vez.

## Três semânticas clássicas

| Semântica | Descrição |
|-----------|-----------|
| **At most once** | A mensagem pode ser perdida, mas não será reenviada. |
| **At least once** | A mensagem não é perdida, mas pode ser entregue/processada mais de uma vez. |
| **Exactly once** | A mensagem é processada uma única vez. |

Isso se desdobra em dois lados: **durabilidade na publicação** (producer) e **garantias no consumo** (consumer).

## No Kafka: mensagem “committed”

Uma mensagem só é considerada **committed** quando todas as réplicas **in-sync** (ISR) daquela partição a receberam. Enquanto pelo menos uma réplica in-sync estiver viva, uma mensagem committed não se perde.

Se o producer não recebe resposta (por exemplo, por falha de rede), ele não sabe se a escrita foi committed ou não. Antes da versão 0.11, o producer normalmente reenviaria, o que podia gerar **at-least-once** (duplicatas no log). A partir de 0.11, o producer pode usar **entrega idempotente** e **transações** para evitar duplicatas e permitir exactly-once em cenários adequados.

## No consumer

O consumer controla o **offset** (posição) em cada partição. Dependendo de quando ele atualiza esse offset em relação ao processamento, temos:

1. **Ler → processar → salvar offset**: se o processo cair depois de processar mas antes de salvar o offset, outro processo pode reprocessar as mesmas mensagens → **at-least-once**.
2. **Ler → salvar offset → processar**: se cair depois de salvar o offset mas antes de processar, algumas mensagens podem nunca ser processadas → **at-most-once**.

Para **exactly-once** no Kafka (ler de um tópico, processar e escrever em outro), o Kafka oferece:

- **Producer transacional**: gravações em vários tópicos/partições e atualização do offset do consumer na mesma transação (tudo ou nada).
- **Consumer com `isolation.level=read_committed`**: só vê mensagens de transações committed; ignora aborts.

Em destinos externos (banco, fila fora do Kafka), exactly-once exige coordenar offset e efeitos (por exemplo, salvar offset junto com o resultado no mesmo sistema ou usar idempotência no destino).

## Transações (resumo)

- O **producer transacional** usa um `transactional.id`. Ele pode enviar múltiplos records e atualizar o “committed offset” do consumer atomicamente.
- O **consumer** deve usar `enable.auto.commit=false` e `isolation.level=read_committed` para não ver mensagens de transações abortadas.
- Em caso de abort, a aplicação deve resetar a posição do consumer e reprocessar; o producer transacional e o read_committed garantem que não haja duplicatas nem perdas dentro do Kafka.

## Referências

- [Message Delivery Semantics — Apache Kafka](https://kafka.apache.org/documentation/#semantics)
- [Using Transactions](https://kafka.apache.org/documentation/#design_transactions)
