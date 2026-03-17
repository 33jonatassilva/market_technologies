# Introdução: bancos SQL e NoSQL

## O que é um banco de dados SQL (relacional)?

Um banco **relacional** armazena dados em **tabelas** com **linhas** e **colunas**. As tabelas se relacionam por **chaves** (primárias e estrangeiras). A linguagem padrão para consultar e manipular esses dados é o **SQL** (Structured Query Language).

Características típicas:

- **Esquema definido antecipadamente** (schema): colunas, tipos e restrições são planejados antes de inserir dados em grande volume.
- **Integridade referencial**: relacionamentos entre tabelas são garantidos pelo banco.
- **Transações ACID** (na maioria dos produtos maduros): atomicidade, consistência, isolamento e durabilidade.
- **Consultas complexas**: junções (JOINs), agregações, filtros em múltiplas tabelas.

Exemplos de produtos: PostgreSQL, MySQL, Microsoft SQL Server, Oracle Database, SQLite.

## O que é um banco de dados NoSQL?

**NoSQL** (“not only SQL” ou “não SQL”) é um termo amplo para bancos que **não seguem o modelo relacional de tabelas com SQL como única interface**. Em geral priorizam **flexibilidade de esquema**, **escalabilidade horizontal** e **modelos de dados** diferentes do relacional.

Famílias comuns de NoSQL:


| Família                        | Ideia principal                                                                 |
| ------------------------------ | ------------------------------------------------------------------------------- |
| **Documento**                  | Documentos (ex.: JSON) com campos aninhados; ex.: MongoDB, Amazon DocumentDB    |
| **Chave-valor**                | Chave → valor opaco; ex.: Redis, Amazon DynamoDB (modo chave-valor)             |
| **Coluna larga (wide-column)** | Famílias de colunas, linhas com colunas dinâmicas; ex.: Apache Cassandra, HBase |
| **Grafo**                      | Nós e arestas para relacionamentos complexos; ex.: Neo4j, Amazon Neptune        |


Não existe um único “NoSQL”: cada família resolve problemas diferentes.

## Por que existem os dois?

- **SQL**: excelente para dados **estruturados**, **relacionamentos fortes**, **consultas ad hoc** e **garantias transacionais** fortes em um único sistema.
- **NoSQL**: útil quando há necessidade de **escala massiva**, **esquema evolutivo**, **latência muito baixa** em padrões de acesso simples (por chave ou por documento), ou **modelagem em grafo**.

Muitas aplicações modernas usam **ambos** (SQL + NoSQL) em serviços diferentes.

## Próximo passo

Em [02-principais-diferencas.md](02-principais-diferencas.md) há uma **visão comparativa** direta entre SQL e NoSQL.

## Referências

- [What is NoSQL? — AWS](https://aws.amazon.com/nosql/)
- [Relational vs. NoSQL data — Microsoft Learn](https://learn.microsoft.com/dotnet/architecture/cloud-native/relational-vs-nosql-data)

