# Exemplos de tecnologias no mercado

Lista **ilustrativa** (não exaustiva) de produtos **SQL** e **NoSQL** citados em documentação e nuvem. Sempre consulte a documentação oficial do produto para recursos e limites.

---

## Bancos relacionais (SQL)

| Produto | Notas típicas |
|---------|----------------|
| **PostgreSQL** | Open source; JSON/JSONB; extensível; muito usado em aplicações web e dados. |
| **MySQL / MariaDB** | Open source; amplamente usado em LAMP e hospedagens. |
| **Microsoft SQL Server** | Ecossistema Microsoft; on-prem e Azure SQL. |
| **Oracle Database** | Enterprise; grandes corporações. |
| **SQLite** | Embarcado; arquivo único; ideal para apps locais e testes. |
| **Amazon RDS** | Serviço gerenciado para PostgreSQL, MySQL, SQL Server, etc. |

---

## NoSQL — por família

### Documento

| Produto | Notas típicas |
|---------|----------------|
| **MongoDB** | Documentos BSON; índices; replica sets; sharding. |
| **Amazon DocumentDB** | Compatível com API MongoDB (ver doc AWS para diferenças). |
| **Azure Cosmos DB** | APIs múltiplas (incl. MongoDB, Cassandra, etc.). |

### Chave-valor

| Produto | Notas típicas |
|---------|----------------|
| **Redis** | Em memória; cache, sessão, filas leves; persistência opcional. |
| **Amazon DynamoDB** | Totalmente gerenciado; chave-valor e documento; escala horizontal. |

### Wide-column

| Produto | Notas típicas |
|---------|----------------|
| **Apache Cassandra** | Alta escrita distribuída; modelo por partition key. |
| **ScyllaDB** | Compatível com modelo Cassandra em muitos casos. |
| **Google Bigtable** | Wide-column gerenciado (GCP). |

### Grafo

| Produto | Notas típicas |
|---------|----------------|
| **Neo4j** | Grafo com Cypher. |
| **Amazon Neptune** | Grafo gerenciado (Gremlin, openCypher). |
| **Azure Cosmos DB (Gremlin)** | API de grafo. |

---

## Produtos que misturam conceitos

Alguns serviços oferecem **SQL sobre dados não relacionais** ou **JSON em SQL**:

- **PostgreSQL** com tipo JSONB.
- **Azure Cosmos DB** com API SQL para documentos.
- **BigQuery**, **Snowflake**: warehouses analíticos com SQL sobre dados semi-estruturados.

Isso mostra que a fronteira **SQL vs NoSQL** é útil para aprender, mas o **mercado** converge em **ferramentas híbridas** conforme a necessidade.

---

## Referências

- [AWS Database services](https://aws.amazon.com/products/databases/)
- [Azure databases](https://azure.microsoft.com/products/category/databases/)
- [MongoDB documentation](https://www.mongodb.com/docs/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
