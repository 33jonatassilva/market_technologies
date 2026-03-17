# Modelo de dados e esquema

## Banco SQL: tabelas e relacionamentos

No modelo **relacional**:

- Dados ficam em **tabelas**; cada linha é um registro; cada coluna tem um **tipo** definido.
- **Chave primária** identifica a linha; **chaves estrangeiras** ligam tabelas (um-para-muitos, muitos-para-muitos via tabela de junção).
- O **esquema** (CREATE TABLE, tipos, NOT NULL, UNIQUE) é normalmente **rígido**: mudar a estrutura exige **migrações** (ALTER TABLE).

**Vantagens**: integridade referencial, consultas com **JOIN** entre entidades, relatórios e agregações sobre várias tabelas.

**Desvantagens para alguns cenários**: mudanças frequentes de estrutura ou dados muito heterogêneos podem exigir muitas colunas opcionais ou tabelas EAV (entity-attribute-value), o que complica consultas.

---

## NoSQL: famílias e flexibilidade

### Documento (document store)

- Armazena **documentos** (ex.: JSON/BSON): um documento pode ter campos aninhados e listas.
- **Esquema flexível**: documentos na mesma “coleção” podem ter campos diferentes.
- Consultas costumam ser por **ID**, **índices** ou **filtros** sobre campos indexados; **JOINs** entre coleções não são o padrão — costuma-se **desnormalizar** ou fazer várias leituras na aplicação.

**Quando faz sentido**: perfis de usuário, catálogos, conteúdo com estrutura variável.

### Chave-valor (key-value)

- **Chave** única → **valor** (string, blob, objeto serializado).
- Acesso típico: **get/put/delete** por chave; pouca ou nenhuma consulta secundária sem índices adicionais.

**Quando faz sentido**: cache, sessões, filas simples, feature flags.

### Wide-column (família de colunas)

- Dados organizados em **famílias de colunas**; linhas podem ter **conjuntos diferentes de colunas**.
- Pensado para **grandes volumes** distribuídos e padrões de leitura/escrita por **partition key** + **clustering**.

**Quando faz sentido**: séries temporais, IoT, eventos em escala muito grande com padrão de acesso previsível.

### Grafo

- **Nós** e **arestas** com propriedades; consultas sobre **caminhos** e relacionamentos (ex.: “amigos de amigos”).

**Quando faz sentido**: redes sociais, recomendações, detecção de fraude em grafos, knowledge graphs.

---

## Esquema fixo vs flexível


| Abordagem              | SQL típico                               | NoSQL documento típico                                          |
| ---------------------- | ---------------------------------------- | --------------------------------------------------------------- |
| Definição de estrutura | Antes de escalar dados (schema-on-write) | Evolutiva; validação muitas vezes na aplicação (schema-on-read) |
| Migração               | ALTER TABLE, scripts de migração         | Novos campos nos documentos; eventual reindexação               |
| Validação              | Constraints no banco (CHECK, FK)         | Aplicação ou engines de validação (ex.: JSON Schema)            |


A flexibilidade do NoSQL **não elimina** a necessidade de **governança**: sem contrato claro, dados inconsistentes se acumulam.

## Próximo passo

[04-transacoes-e-consistencia.md](04-transacoes-e-consistencia.md) — ACID, BASE e consistência distribuída.

## Referências

- [NoSQL Database Types — AWS](https://aws.amazon.com/nosql/)
- [Relational vs. NoSQL data — Microsoft Learn](https://learn.microsoft.com/dotnet/architecture/cloud-native/relational-vs-nosql-data)

