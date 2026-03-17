# Principais diferenças: SQL vs NoSQL

Este documento resume as **diferenças mais citadas** na documentação de mercado entre bancos **relacionais (SQL)** e **NoSQL**. Os detalhes aparecem nos arquivos seguintes.

---

## Tabela comparativa


| Aspecto                      | SQL (relacional)                                                                                      | NoSQL                                                                                        |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Modelo de dados**          | Tabelas, linhas, colunas, relacionamentos                                                             | Documento, chave-valor, colunas largas, grafo (conforme o produto)                           |
| **Esquema**                  | Em geral **fixo** e definido antes (schema-on-write)                                                  | Em geral **flexível** ou evolutivo (schema-less / schema-on-read em muitos casos)            |
| **Linguagem de consulta**    | **SQL** padronizado (com variações por produto)                                                       | APIs específicas, às vezes SQL-like (ex.: CQL) ou consultas por chave/caminho                |
| **Junções complexas**        | **JOINs** nativos e comuns                                                                            | Menos comuns ou limitados; muitas vezes **desnormalização** e múltiplas leituras             |
| **Transações**               | **ACID** forte em um único nó/cluster (conforme produto)                                              | Varia: de transações limitadas a **eventual consistency** (BASE)                             |
| **Consistência**             | Forte consistência em transações típicas                                                              | Muitos sistemas distribuídos priorizam **disponibilidade** e **tolerância a partição** (CAP) |
| **Escalabilidade típica**    | **Vertical** (mais CPU/RAM no servidor) e réplicas de leitura; sharding possível mas mais operacional | **Horizontal** (mais nós) como padrão em vários produtos                                     |
| **Casos de uso clássicos**   | ERP, financeiro, relatórios, dados altamente relacionados                                             | Catálogos, sessões, feeds, IoT em alta taxa, grafos sociais                                  |
| **Maturidade / ecossistema** | Muito maduro; ferramentas ETL, BI, ORMs                                                               | Maduro por família; ecossistema variável por produto                                         |


---

## Em uma frase

- **SQL**: dados **estruturados** e **relacionados**, com **consultas ricas** e **transações fortes**.
- **NoSQL**: **flexibilidade** de modelo e **escala horizontal**, com **trade-offs** em consistência e em padrões de consulta.

---

## Avisos importantes

1. **“NoSQL” não é um único tipo**: comparar “SQL vs MongoDB” é diferente de “SQL vs Redis” ou “SQL vs Neo4j”.
2. **SQL moderno evoluiu**: alguns bancos relacionais oferecem JSON, particionamento e réplicas; a linha entre categorias pode borrar em produtos híbridos.
3. **NoSQL com transações**: vários produtos NoSQL adicionaram transações multi-documento ou multi-chave em versões recentes — sempre verifique o **produto** e a **documentação oficial**.

## Próximo passo

- [03-modelo-de-dados-e-esquema.md](03-modelo-de-dados-e-esquema.md) — modelos e esquema em detalhe.
- [04-transacoes-e-consistencia.md](04-transacoes-e-consistencia.md) — ACID, BASE e CAP.

## Referências

- [Relational vs. NoSQL data — Microsoft Learn](https://learn.microsoft.com/dotnet/architecture/cloud-native/relational-vs-nosql-data)
- [NoSQL vs. relational — Microsoft Cosmos DB](https://devblogs.microsoft.com/cosmosdb/nosql-vs-relational-which-database-should-you-use-for-your-app/)

