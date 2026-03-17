# Otimização de consultas e criação de índices (SQL)

Este guia foca em **cenários práticos** de otimização de consultas SQL e **estratégias de índices** usadas no mercado. Os exemplos são genéricos e valem para a maioria dos bancos (PostgreSQL, SQL Server, MySQL), mas sempre valide no seu SGBD e com o plano de execução.

---

## Regra de ouro: medir antes e depois

Otimização é um ciclo:

- Identificar consultas lentas (APM, logs, slow query log).
- Medir com **plano de execução**.
- Mudar índice/consulta/modelo.
- Medir de novo.

### Ferramentas por banco (referências oficiais)

- **PostgreSQL**: `EXPLAIN` / `EXPLAIN ANALYZE` ([docs](https://www.postgresql.org/docs/15/sql-explain.html))
- **SQL Server**: plano de execução + `SET STATISTICS IO, TIME` ([IO](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-io-transact-sql?view=sql-server-ver16), [TIME](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-time-transact-sql?view=sql-server-ver16))
- **MySQL**: `EXPLAIN` / `EXPLAIN ANALYZE` (ver manual do MySQL 8.x)

---

## Como saber quando uma consulta está lenta

### 1. Onde obter a métrica de “lentidão”

Você precisa de **tempo de execução** (e, se possível, **I/O** e **número de linhas**) por consulta. As fontes típicas são:

| Fonte | O que entrega | Observação |
|-------|----------------|------------|
| **Slow query log** (MySQL, PostgreSQL) | Consultas que ultrapassam um limite de tempo (ex.: 1 s) | Configurável no servidor; gera arquivo de log. |
| **pg_stat_statements** (PostgreSQL) | Tempo total, chamadas, tempo médio por query “normalizada” | Extensão; precisa habilitar. |
| **Query Store** (SQL Server) | Histórico de planos, tempo de execução, uso de recursos | Habilitado por banco; interface no SSMS. |
| **Extended Events / SQL Profiler** (SQL Server) | Captura de queries em tempo real com duração | Para análise pontual. |
| **APM / Application Performance Monitoring** | Tempo da query vista pela aplicação (incluindo rede) | New Relic, Datadog, Application Insights, etc. |
| **Log da aplicação** | Tempo que o código mede em volta da query | Útil se você instrumentar (ex.: log antes/depois do `Execute`). |

**Definição de “lenta”**: não existe número universal. Defina um limite por contexto (ex.: > 200 ms para API, > 2 s para relatório). O importante é **ter o número** (tempo médio, p95, p99) para comparar antes e depois do índice.

### 2. Exemplos práticos por banco

**PostgreSQL — habilitar log de consultas lentas** (em `postgresql.conf`):

```ini
log_min_duration_statement = 1000   # logar queries > 1 segundo (valor em ms)
# ou
log_statement = 'all'               # logar todas (pesado; use só para debug)
```

Depois, consultar **quais consultas consomem mais tempo** (com a extensão `pg_stat_statements`):

```sql
-- Instalar: CREATE EXTENSION pg_stat_statements;
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

**MySQL — slow query log** (em `my.cnf` ou variáveis):

```ini
slow_query_log = 1
long_query_time = 2
slow_query_log_file = /var/log/mysql/slow.log
```

**SQL Server — Query Store**: habilitar no banco e usar relatórios “Top resource consuming queries” ou consultar `sys.query_store_*`.

---

## Como obter a métrica (tempo e I/O) de uma consulta específica

Depois de identificar a consulta lenta (pelo log, Query Store ou APM), você precisa **medir** ela de forma reproduzível.

### PostgreSQL

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM pedidos WHERE cliente_id = 123 ORDER BY criado_em DESC LIMIT 20;
```

- **ANALYZE**: executa a query e mostra **tempo real** (actual time) e **linhas** por nó do plano.
- **BUFFERS**: mostra leituras de disco/cache (shared hit, read).

Assim você vê **quanto tempo** cada etapa levou e **se houve muitas leituras** (I/O).

### SQL Server

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT * FROM pedidos WHERE cliente_id = 123 ORDER BY criado_em DESC OFFSET 0 ROWS FETCH NEXT 20 ROWS ONLY;

SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
```

- **STATISTICS IO**: logical reads, physical reads (páginas lidas).
- **STATISTICS TIME**: tempo de CPU e tempo decorrido.

E use **plano de execução** (Ctrl+L no SSMS ou “Include Actual Execution Plan”) para ver **qual índice** (se algum) foi usado em cada operador.

### MySQL

```sql
EXPLAIN ANALYZE SELECT * FROM pedidos WHERE cliente_id = 123 ORDER BY criado_em DESC LIMIT 20;
```

O resultado inclui tempo real por etapa. Em `EXPLAIN` (sem ANALYZE), a coluna **key** indica qual índice o otimizador **escolheu**; **rows** é a estimativa de linhas.

---

## Como saber se o índice criado está sendo utilizado

### 1. Pelo plano de execução (confirmação por query)

Ao rodar a consulta com **EXPLAIN** (ou plano de execução), o banco mostra **qual índice** usa em cada passo (ou que está fazendo seq scan / table scan).

**PostgreSQL** — no texto do `EXPLAIN (ANALYZE, BUFFERS)`:

- Procure por **Index Scan** ou **Index Only Scan** usando o **nome do seu índice** (ex.: `ix_pedidos_cliente_id`).
- Se aparecer **Seq Scan** na tabela que você indexou, o otimizador **não** usou índice (pode ser porque achou mais barato o scan, ou porque o índice não atende ao filtro/ordenação).

**SQL Server** — no plano gráfico:

- Clique no operador (ex.: Index Seek); nas propriedades aparece **Index Name**.
- **Index Seek** / **Index Scan** com o nome do seu índice = índice em uso.
- **Table Scan** / **Clustered Index Scan** na tabela em questão = não está usando o índice que você criou (ou está usando o clustered).

**MySQL** — em `EXPLAIN`:

- Coluna **key**: nome do índice usado (NULL = nenhum).
- Coluna **type**: `ref` ou `range` costumam indicar uso de índice; `ALL` = full table scan.

### 2. Estatísticas de uso de índice (visão global)

Para ver se um índice **está sendo usado em geral** (não só numa query), use as visões do próprio banco:

**PostgreSQL** — `pg_stat_user_indexes`:

```sql
SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname = 'pedidos'
ORDER BY idx_scan DESC;
```

- **idx_scan**: quantas vezes o índice foi usado para scan.
- Se **idx_scan** for 0 (ou muito baixo) enquanto a tabela é consultada, esse índice provavelmente **não** está sendo utilizado.

**SQL Server** — `sys.dm_db_index_usage_stats`:

```sql
SELECT OBJECT_NAME(s.object_id) AS tabela, i.name AS indice,
       s.user_seeks, s.user_scans, s.user_lookups
FROM sys.dm_db_index_usage_stats s
JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE OBJECT_NAME(s.object_id) = 'pedidos';
```

- **user_seeks**, **user_scans**, **user_lookups**: uso em buscas, varreduras e lookups.
- Se tudo 0 após um tempo de uso normal, o índice pode ser candidato a remoção (avaliar com cuidado).

**MySQL** — no MySQL 8.0, o **Performance Schema** (tabelas como `performance_schema.events_statements_summary_by_digest`) ajuda a ver queries mais pesadas; uso de índice é visto por **EXPLAIN** por query. Em versões recentes, há também `sys.schema_unused_indexes` (se disponível) para sugerir índices não usados.

### 3. Resumo do fluxo

1. **Descobrir** a consulta lenta (slow log, pg_stat_statements, Query Store, APM).
2. **Medir** a consulta com EXPLAIN ANALYZE / plano real / STATISTICS IO,TIME.
3. **Criar ou ajustar** o índice conforme o filtro/JOIN/ORDER BY.
4. **Rodar de novo** o EXPLAIN (ANALYZE) ou o plano: confirmar que aparece **Index Scan/Seek** com o nome do índice.
5. **Acompanhar** em produção: `pg_stat_user_indexes` ou `sys.dm_db_index_usage_stats` para ver se **idx_scan** / **user_seeks** aumentam e se o tempo da query (na APM ou no log) diminui.

Se após criar o índice o plano **ainda** mostrar Seq Scan/Table Scan, causas comuns: estatísticas desatualizadas (rode `ANALYZE` no Postgres, ou atualize estatísticas no SQL Server), ou o otimizador estimar que o índice é mais caro que o scan (ex.: tabela pequena ou filtro pouco seletivo).

---

## Cenário 1: filtro por coluna sem índice (table scan)

### Sintoma

- Consulta com `WHERE coluna = ...` (ou `WHERE coluna BETWEEN ...`) em tabela grande.
- Plano mostra **seq scan / table scan**.

### Solução

- Criar índice na coluna usada no filtro (e/ou na coluna de ordenação).

```sql
CREATE INDEX ix_pedidos_status ON pedidos (status);
```

**Observação**: índices aceleram SELECT, mas têm custo em INSERT/UPDATE/DELETE (manutenção do índice).

---

## Cenário 2: índice composto (multi-coluna) com ordem errada

### Sintoma

- Você tem índice em `(A, B)` mas filtra só por `B`, ou filtra por ambos porém na prática o banco não usa bem o índice.

### Conceito

- Em vários bancos, índices compostos seguem a lógica do **prefixo à esquerda** (leftmost prefix): um índice em `(A, B, C)` é muito útil para buscas em `A` ou `A,B` ou `A,B,C`, mas nem sempre para `B` sozinho.
- Referência: **MySQL** sobre múltiplas colunas e prefixo à esquerda ([docs](https://dev.mysql.com/doc/refman/en/multiple-column-indexes.html)).
- Referência: **PostgreSQL** sobre índices multicoluna e colunas “leading” ([docs](https://www.postgresql.org/docs/current/indexes-multicolumn.html)).

### Soluções

- Reordenar o índice para refletir o padrão mais comum de filtros:

```sql
-- se o mais comum é filtrar por cliente_id e depois status
CREATE INDEX ix_pedidos_cliente_status ON pedidos (cliente_id, status);
```

- Ou criar um índice separado para o caso “B sozinho” (se realmente necessário):

```sql
CREATE INDEX ix_pedidos_status ON pedidos (status);
```

---

## Cenário 3: índice “cobrindo” a consulta (covering index / index-only scan)

### Sintoma

- A consulta filtra bem, mas ainda faz muitos “lookups” na tabela para buscar colunas do `SELECT`.

### Ideia

Criar um índice que contenha (direta ou indiretamente) **todas as colunas** necessárias para responder a query sem visitar a tabela.

- Em **SQL Server**, use `INCLUDE` em índices não clusterizados ([docs](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/create-indexes-with-included-columns?view=sql-server-ver16)).
- Em **PostgreSQL**, existe `INCLUDE` em `CREATE INDEX` ([docs](https://www.postgresql.org/docs/current/sql-createindex.html)) e o conceito de **index-only scans** ([docs](https://www.postgresql.org/docs/15/indexes-index-only-scans.html)).

### Exemplo (conceitual)

Você filtra por `(cliente_id, criado_em)` e precisa projetar `total`:

```sql
-- Postgres (exemplo)
CREATE INDEX ix_pedidos_cliente_criado_em
  ON pedidos (cliente_id, criado_em)
  INCLUDE (total);
```

Resultado esperado: menos I/O (menos leituras na heap/tabela) quando o plano consegue usar index-only.

---

## Cenário 4: ORDER BY + LIMIT lento (pagination)

### Sintoma

- `ORDER BY criado_em DESC LIMIT 20` fica lento, principalmente com filtros.

### Solução

- Índice alinhado à ordenação e ao filtro.

```sql
CREATE INDEX ix_pedidos_cliente_criado_em_desc
  ON pedidos (cliente_id, criado_em DESC);
```

### Anti-pattern: OFFSET alto

```sql
-- ruim para páginas profundas (o banco precisa “pular” muitas linhas)
SELECT *
FROM pedidos
WHERE cliente_id = :clienteId
ORDER BY criado_em DESC
OFFSET 100000 LIMIT 20;
```

**Alternativa (keyset pagination)**: usar o último valor visto:

```sql
SELECT *
FROM pedidos
WHERE cliente_id = :clienteId
  AND criado_em < :ultimoCriadoEm
ORDER BY criado_em DESC
LIMIT 20;
```

---

## Cenário 5: função na coluna do filtro (índice não aproveitado)

### Sintoma

- `WHERE LOWER(email) = '...'` ou `WHERE DATE(criado_em) = '...'`.

### Por que acontece

Aplicar função à coluna pode impedir uso do índice (depende do banco e do índice).

### Soluções

- Normalizar o dado na gravação (ex.: email já em lowercase).
- Usar índice funcional (se o banco suportar).
- Reescrever a condição para preservar a coluna “crua” (quando possível).

---

## Cenário 6: JOIN lento por falta de índice nas chaves

### Sintoma

- JOIN entre tabelas grandes, plano com nested loops caros ou hash join gigante.

### Soluções

- Indexar colunas usadas em **JOIN** (FK/PK) e filtros correlatos.

```sql
-- FK (tabela filha) geralmente precisa de índice
CREATE INDEX ix_itens_pedido_id ON itens_pedido (pedido_id);
```

Em muitos bancos, a PK já tem índice; o ponto costuma ser: **o lado “filho” (FK) precisa de índice** para evitar scans.

---

## Cenário 7: N+1 queries (na aplicação/ORM)

### Sintoma

- APM mostra várias queries pequenas repetidas (ex.: 1 query de pedidos + N queries para itens).

### Soluções

- Trazer dados com JOIN/projeção (quando fizer sentido).
- Usar carregamento adequado no ORM (ex.: eager loading).
- Criar endpoints específicos/read models para telas que precisam de agregação.

---

## Cenário 8: excesso de índices (write lento)

### Sintoma

- INSERT/UPDATE/DELETE lentos.
- Muitas chaves/índices na tabela.

### Soluções

- Remover índices não usados (confirmar com métricas do banco).
- Evitar índices muito “largos” sem necessidade.
- Preferir índices que atendam consultas críticas.

---

## Checklist rápido de índices

- A consulta usa `WHERE` / `JOIN` / `ORDER BY` frequentemente? **Candidate a índice**.
- Há combinação comum de filtros? **Índice composto**.
- Você seleciona poucas colunas sempre? **Índice cobrindo** (INCLUDE) pode ajudar.
- Há muita escrita? Evite **over-indexing**.
- Mudou índice? Sempre validar com **EXPLAIN / plano**.

---

## Outras estratégias além da criação de índices

Índices são uma das primeiras alavancas, mas **não são a única**. Abaixo, estratégias complementares usadas no mercado para otimizar consultas e reduzir carga no banco.

### 1. Reescrever a consulta

| Prática | Benefício |
|--------|-----------|
| **SELECT só as colunas necessárias** (evitar `SELECT *`) | Menos dados trafegados, menos I/O e melhor uso de índice cobrindo. |
| **Filtrar o mais cedo possível** | Reduz linhas nas etapas seguintes (JOIN, agregação). Ex.: aplicar `WHERE` antes de JOIN quando a semântica permitir. |
| **Evitar funções na coluna do WHERE** | Permite uso de índice (já citado no Cenário 5). |
| **Subquery correlacionada → JOIN ou EXISTS** | Muitas vezes o otimizador gera plano melhor com JOIN/EXISTS; vale testar com EXPLAIN. |
| **União de muitos OR → IN ou tabela temporária** | Pode simplificar o plano e usar índice de forma mais eficiente. |

Reescrever não substitui índice; **complementa**: uma query bem escrita + índice certo tende a performar melhor.

---

### 2. Views materializadas e tabelas de resumo

Quando a consulta é **pesada e repetida** (ex.: dashboard, relatório diário), você pode **pré-calcular** o resultado:

- **View materializada** (PostgreSQL: `MATERIALIZED VIEW`; SQL Server: Indexed View): o banco armazena o resultado; você atualiza com `REFRESH` ou em janelas de manutenção.
- **Tabela de resumo**: job (cron, worker) preenche uma tabela com agregações (totais por dia, por cliente, etc.); a aplicação consulta essa tabela em vez de agregar na tabela transacional.

**Trade-off**: dados não são em tempo real; você escolhe a frequência de atualização (minutos, horas, diário).

---

### 3. Particionamento de tabelas

Em tabelas **muito grandes** (ex.: eventos, logs, faturamento por ano), **particionar** por intervalo (data), lista ou hash pode:

- Reduzir o volume que o otimizador e os índices precisam considerar quando há filtro na coluna de partição (ex.: `WHERE criado_em >= '2024-01-01'`).
- Facilitar manutenção: dropar/arquivar uma partição antiga em vez de `DELETE` em massa.

Particionamento **não substitui** índice: em geral você mantém índices **por partição** (ou globais, conforme o banco). É uma estratégia de **modelagem e manutenção** que melhora o cenário para índices e consultas.

---

### 4. Cache

- **Na aplicação**: guardar em memória (ou em Redis/Memcached) o resultado de consultas que mudam pouco (ex.: catálogo, configuração). Assim você reduz chamadas ao banco.
- **Cache do próprio banco**: alguns bancos têm cache de resultado de query ou de páginas (buffer pool); garantir que as consultas quentes usem bem esse cache (evitar varreduras enormes que “lavam” o cache).
- **TTL e invalidação**: definir quando o cache expira ou quando é invalidado (ex.: após atualização do catálogo).

Cache reduz **carga e latência**; não altera o plano da query no banco, mas diminui quantas vezes ela roda.

---

### 5. Manter estatísticas atualizadas

O otimizador escolhe o plano com base em **estatísticas** (distribuição de valores, cardinalidade). Se estiverem desatualizadas, pode escolher plano ruim ou **não usar** o índice que você criou.

- **PostgreSQL**: `ANALYZE tabela;` (ou `ANALYZE` global); em muitos ambientes já roda via autovacuum.
- **SQL Server**: `UPDATE STATISTICS tabela;` ou manutenção automática.
- **MySQL**: `ANALYZE TABLE tabela;`

Depois de criar índice ou após cargas grandes, rodar análise/estatísticas costuma ajudar o otimizador a “enxergar” o novo índice.

---

### 6. Denormalização e read models

Para **leituras** muito específicas (ex.: tela de resumo do pedido com nome do cliente, total, status), manter uma **cópia desnormalizada** (tabela ou view) ou um **read model** (CQRS) evita JOINs pesados na hora da leitura. A escrita fica na modelo normalizado; a leitura usa a estrutura otimizada para aquela tela.

Detalhes em [09-modelagem-relacional-e-tabelas-intermediarias.md](09-modelagem-relacional-e-tabelas-intermediarias.md) (normalização vs denormalização).

---

### 7. Arquivar ou mover dados antigos

Consultas que **varrem** anos de dados ficam mais lentas e mantêm índices grandes. Estratégias:

- **Mover** registros antigos para uma tabela/banco de arquivo e consultar só quando necessário.
- **Particionar** por período e manter apenas partições recentes “quentes”; partições antigas em storage mais barato ou comprimido.

Assim, as consultas do dia a dia e os índices atuam sobre **menos dados**.

---

### 8. Pool de conexões e prepared statements

- **Pool de conexões**: reutilizar conexões reduz overhead de abrir/fechar; configure um tamanho adequado para a carga.
- **Prepared statements** (quando a aplicação repete a mesma query com parâmetros diferentes): o banco pode reutilizar plano e reduzir parsing; em alguns bancos também há cache de plano.

Isso otimiza **tempo de conexão e planejamento**, não o plano em si; ainda assim é parte de uma stack “rápida”.

---

### 9. Resumo: quando usar o quê

| Estratégia | Principal benefício |
|-----------|----------------------|
| Índices | Acesso rápido a linhas e ordenação; menos I/O. |
| Reescrever query | Melhor plano e menos dados processados. |
| View materializada / tabela de resumo | Evitar recalcular agregações pesadas a cada request. |
| Particionamento | Menos dados por operação; manutenção e arquivamento. |
| Cache (app/Redis) | Menos execuções da mesma query. |
| Estatísticas atualizadas | Otimizador escolhe melhor plano (incl. uso de índice). |
| Denormalização / read model | Leituras específicas sem JOINs pesados. |
| Arquivar dados antigos | Menos volume nas consultas e nos índices. |
| Pool + prepared statements | Menos overhead de conexão e de planejamento. |

Na prática, **índices + boa escrita da query + estatísticas** costumam ser o primeiro pacote; depois entram cache, materialização, particionamento e arquivamento conforme o volume e o tipo de consulta.

---

## Referências

- PostgreSQL
  - `EXPLAIN` / `EXPLAIN ANALYZE`: `https://www.postgresql.org/docs/15/sql-explain.html`
  - Examining index usage (`pg_stat_user_indexes`): `https://www.postgresql.org/docs/15/indexes-examine.html`
  - `pg_stat_statements`: `https://www.postgresql.org/docs/current/pgstatstatements.html`
  - Índices multicoluna: `https://www.postgresql.org/docs/current/indexes-multicolumn.html`
  - Tipos de índice: `https://www.postgresql.org/docs/15/indexes-types.html`
  - Index-only scans e covering indexes: `https://www.postgresql.org/docs/15/indexes-index-only-scans.html`
  - `CREATE INDEX` + `INCLUDE`: `https://www.postgresql.org/docs/current/sql-createindex.html`
- SQL Server (Microsoft Learn)
  - Index design guide: `https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide?view=sql-server-ver17`
  - Index usage stats: `https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-db-index-usage-stats-transact-sql`
  - Query Store: `https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store`
  - Included columns: `https://learn.microsoft.com/en-us/sql/relational-databases/indexes/create-indexes-with-included-columns?view=sql-server-ver16`
  - `SET STATISTICS IO`: `https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-io-transact-sql?view=sql-server-ver16`
  - `SET STATISTICS TIME`: `https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-time-transact-sql?view=sql-server-ver16`
- MySQL
  - Índices multicoluna (prefixo à esquerda): `https://dev.mysql.com/doc/refman/en/multiple-column-indexes.html`
  - Slow query log: `https://dev.mysql.com/doc/refman/en/slow-query-log.html`
  - EXPLAIN: `https://dev.mysql.com/doc/refman/en/explain-output.html`

