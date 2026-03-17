# Casos de uso e quando escolher

Este documento resume **quando a documentação de mercado recomenda** SQL, NoSQL ou uma **combinação**, sem substituir análise de requisitos do seu projeto.

---

## Quando SQL (relacional) costuma ser a escolha natural

- Dados **altamente estruturados** e **relacionados** (clientes, pedidos, itens, pagamentos).
- Necessidade de **integridade referencial** e **constraints** no banco.
- **Relatórios** e **consultas ad hoc** com JOINs, agregações e ferramentas de BI.
- Requisitos **regulatórios** ou de negócio que exijam **ACID** forte em transações (financeiro, estoque crítico).
- Equipe já madura em **SQL**, ORMs e migrações de esquema.

---

## Quando NoSQL costuma ser considerado

| Cenário | Família NoSQL típica |
|---------|----------------------|
| **Sessão, cache, rate limit** | Chave-valor (Redis, DynamoDB) |
| **Catálogo / perfil com JSON variável** | Documento (MongoDB, Cosmos DB API for MongoDB) |
| **Telemetria, eventos em massa, séries temporais** | Wide-column (Cassandra) ou documento + particionamento |
| **Rede social, recomendação, fraude em grafos** | Grafo (Neo4j, Neptune) |
| **Escala horizontal** com padrão de acesso por chave/partição bem definido | Conforme produto |

Motivos frequentes: **volume** ou **taxa de escrita** muito altos, **latência** baixa em acesso por chave, **esquema** que muda rápido sem migrações pesadas em todas as linhas.

---

## Arquiteturas híbridas

É comum usar:

- **SQL** como **fonte da verdade** transacional (pedidos, contas).
- **NoSQL** para **cache** (Redis), **busca** (Elasticsearch/OpenSearch), **sessão**, ou **read models** desnormalizados para telas rápidas.

A escolha não precisa ser **exclusiva**.

---

## Checklist rápido

| Pergunta | Se “sim” tende a... |
|----------|---------------------|
| Preciso de JOINs complexos e relatórios SQL? | **SQL** |
| Preciso de transações multi-tabela fortes? | **SQL** (ou NoSQL com suporte explícito verificado) |
| Preciso de escala massiva com acesso por chave/partição? | **NoSQL** (modelado corretamente) |
| Dados muito heterogêneos no mesmo “tipo” de registro? | **Documento** pode ajudar |
| Grafos e consultas de caminho são o core? | **Grafo** |

Sempre valide com **POC**, **custos** (licença, operação, backup) e **habilidades** do time.

## Próximo passo

[07-exemplos-de-tecnologias.md](07-exemplos-de-tecnologias.md) — exemplos de produtos no mercado.

## Referências

- [NoSQL vs. relational — Microsoft Cosmos DB](https://devblogs.microsoft.com/cosmosdb/nosql-vs-relational-which-database-should-you-use-for-your-app/)
- [Relational vs. NoSQL data — Microsoft Learn](https://learn.microsoft.com/dotnet/architecture/cloud-native/relational-vs-nosql-data)
