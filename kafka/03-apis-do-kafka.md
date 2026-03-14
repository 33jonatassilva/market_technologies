# APIs do Kafka

Além de ferramentas de linha de comando para administração, o Kafka oferece **APIs** para integrar e construir aplicações. Abaixo, um resumo de cada uma e quando usá-las.

## Producer API

Permite **enviar** fluxos de dados para um ou mais tópicos no cluster.

- **Quando usar**: sempre que sua aplicação precisar publicar eventos no Kafka (logs, métricas, eventos de negócio, etc.).

## Consumer API

Permite **ler** fluxos de dados de um ou mais tópicos.

- **Quando usar**: quando sua aplicação precisa consumir e processar eventos. Geralmente usado junto com **consumer groups** para distribuir o trabalho entre várias instâncias.

## Streams API (Kafka Streams)

Permite **transformar** fluxos de dados: ler de um ou mais tópicos de entrada e escrever em um ou mais tópicos de saída (ou em sistemas externos). Oferece operações como agregações, joins, janelas e processamento por event-time.

- **Quando usar**: aplicações de processamento de streams em tempo real (microserviços de stream, pipelines de dados, CEP).

## Connect API (Kafka Connect)

Permite construir e rodar **conectores** reutilizáveis que importam dados de sistemas externos para o Kafka (source) ou exportam do Kafka para sistemas externos (sink).

- **Quando usar**: integração contínua com bancos de dados, filas, sistemas de arquivos, etc. Na prática, muitas vezes você usa conectores prontos da comunidade sem implementar a API.

## Admin API

Permite **gerenciar e inspecionar** tópicos, brokers e outros objetos do Kafka (criar tópicos, alterar configs, listar recursos).

- **Quando usar**: ferramentas de administração, scripts de provisionamento ou aplicações que precisam criar/ajustar tópicos dinamicamente.

## Share Consumer API

Permite que aplicações em um **share group** consumam e processem dados dos tópicos de forma cooperativa. É uma alternativa ao modelo clássico de consumer groups.

- **Quando usar**: quando você precisa de compartilhamento mais fino de partições, contagem de tentativas de entrega ou mais consumidores do que partições (cada record pode ser “emprestado” por um tempo com lock e acknowledment individual).

## Visão geral

| API | Função principal |
|-----|------------------|
| Producer | Publicar eventos em tópicos |
| Consumer | Ler eventos de tópicos |
| Streams | Processar e transformar streams (entrada → saída) |
| Connect | Conectar Kafka a sistemas externos (source/sink) |
| Admin | Gerenciar tópicos, brokers e configurações |
| Share Consumer | Consumo cooperativo com locks e acks por record |

As APIs Producer, Consumer, Admin e Share Consumer usam a biblioteca `kafka-clients`. Kafka Streams usa `kafka-streams`. O Connect é um framework à parte, com sua própria API para quem desenvolve conectores.

## Referências

- [Kafka APIs — Apache Kafka Documentation](https://kafka.apache.org/documentation/#api)
- [Producer API (javadoc)](https://kafka.apache.org/documentation.html#producerapi)
- [Consumer API (javadoc)](https://kafka.apache.org/documentation.html#consumerapi)
