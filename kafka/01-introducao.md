# Introdução ao Apache Kafka

## O que é event streaming?

**Event streaming** é a prática de capturar dados em tempo real a partir de fontes de eventos (bancos de dados, sensores, dispositivos móveis, aplicações) na forma de **fluxos de eventos**; armazenar esses fluxos de forma durável; processar e reagir a eles em tempo real ou de forma retrospectiva; e rotear os fluxos para outras tecnologias conforme a necessidade.

Em resumo: garantir que a informação certa esteja no lugar certo, no momento certo.

## Para que serve event streaming?

Alguns exemplos de uso:

- Base para **plataformas de dados**, **arquiteturas orientadas a eventos** e **microserviços**
- Conectar e disponibilizar dados produzidos por diferentes áreas da empresa
- Coletar e reagir a interações e pedidos de clientes (varejo, viagens, apps)
- Capturar e analisar dados de sensores (IoT, fábricas)
- Rastrear frotas e entregas em tempo real (logística)
- Processar pagamentos e transações financeiras em tempo real

## O que é o Apache Kafka?

O **Apache Kafka** é uma **plataforma de event streaming**. Isso significa que ele reúne três capacidades principais:

1. **Processar** fluxos de eventos em tempo real ou de forma retrospectiva
2. **Armazenar** fluxos de eventos de forma durável e confiável pelo tempo que você definir
3. **Publicar e assinar** fluxos de eventos (escrever e ler), incluindo integração contínua com outros sistemas

Tudo isso de forma **distribuída**, **escalável**, **elástica**, **tolerante a falhas** e **segura**. O Kafka pode rodar em hardware físico, VMs, containers, on-premise ou na nuvem.

## Como o Kafka funciona em poucas palavras?

O Kafka é um sistema distribuído com **servidores** e **clientes** que se comunicam por um protocolo de rede TCP de alto desempenho.

- **Servidores**: formam um cluster. Parte deles é a camada de armazenamento (**brokers**). Outros podem rodar **Kafka Connect** para importar/exportar dados entre o Kafka e sistemas externos (bancos, outros clusters). O cluster é escalável e tolerante a falhas.
- **Clientes**: permitem construir aplicações e microserviços que leem, escrevem e processam eventos em paralelo e de forma tolerante a falhas. Existem clientes oficiais (Java/Scala, incluindo Kafka Streams) e de terceiros para várias linguagens.

## Próximo passo

No próximo documento você verá os **conceitos e a terminologia** do Kafka: eventos, producers, consumers, topics, partições e replicação.

## Referências

- [Introduction — Apache Kafka Documentation](https://kafka.apache.org/documentation/#intro)
- [What is event streaming?](https://kafka.apache.org/documentation/#intro_events)
