# Modelagem relacional: tabelas intermediárias, joins e índices

Este documento adiciona cenários e soluções “de mercado” para modelagem em bancos **SQL**: **tabelas intermediárias** (N:N), índices em chaves, normalização vs denormalização e padrões que ajudam (ou atrapalham) consultas.

---

## Relacionamento muitos-para-muitos (N:N) e tabela intermediária

### O problema

Você tem duas entidades e cada uma pode se relacionar com muitas da outra:

- Pedido tem muitos Produtos
- Produto aparece em muitos Pedidos

### A solução relacional padrão

Criar uma **tabela intermediária** (junction/join table), por exemplo `pedido_itens`:

```sql
CREATE TABLE pedidos (
  id            BIGINT PRIMARY KEY,
  cliente_id    BIGINT NOT NULL,
  criado_em     TIMESTAMP NOT NULL
);

CREATE TABLE produtos (
  id            BIGINT PRIMARY KEY,
  nome          TEXT NOT NULL
);

CREATE TABLE pedido_itens (
  pedido_id     BIGINT NOT NULL,
  produto_id    BIGINT NOT NULL,
  quantidade    INT NOT NULL,
  preco_unitario NUMERIC(12,2) NOT NULL,
  PRIMARY KEY (pedido_id, produto_id),
  FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
  FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
```

**Por que `PRIMARY KEY (pedido_id, produto_id)`?**

- Evita duplicar o mesmo produto no mesmo pedido (dependendo da regra).
- Já cria um índice eficiente para buscar itens por `pedido_id`.

### Índices recomendados na intermediária

Mesmo com PK composta, costuma ser útil indexar o outro lado para consultas “invertidas”:

```sql
CREATE INDEX ix_pedido_itens_produto ON pedido_itens (produto_id);
```

Assim, você consegue consultar “todos os pedidos que contêm o produto X” com melhor performance.

---

## Cenário: JOINs frequentes e índice em Foreign Key

### Sintoma

Consultas como:

```sql
SELECT p.*
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
WHERE c.email = :email;
```

### Solução

Garanta índices nas colunas usadas em:

- `JOIN` (FKs no lado “filho”)
- `WHERE` (filtros)

Exemplo:

```sql
CREATE INDEX ix_pedidos_cliente_id ON pedidos (cliente_id);
CREATE INDEX ix_clientes_email ON clientes (email);
```

**Nota**: muitos bancos criam índice automaticamente para PK/UNIQUE, mas **não** necessariamente para todas as FKs. Em geral, indexar FK é boa prática quando há JOIN/filtro por ela.

---

## Normalização vs denormalização (quando usar)

### Normalização (mais comum em OLTP)

**Vantagens**:

- Evita duplicação de dados (menos inconsistência).
- Facilita integridade (FKs) e atualizações corretas.
- Modelo “clássico” para transações.

**Custo**:

- Mais JOINs para montar telas/relatórios.

### Denormalização (com cuidado, por necessidade)

Quando há consultas muito críticas e previsíveis, você pode:

- Duplicar alguns campos em tabelas de leitura (ex.: `pedido.cliente_nome`).
- Criar tabelas agregadas/materializadas (dependendo do banco).

**Trade-off**: você ganha leitura mais rápida, mas precisa manter consistência (via triggers, jobs, eventos, ou lógica na aplicação).

Uma abordagem comum é manter:

- SQL normalizado como **fonte da verdade**
- “read model” denormalizado (ou cache) para consultas específicas

---

## Índices em tabelas intermediárias: padrões úteis

### 1) PK composta com ordem certa

Se o padrão principal é “buscar por pedido”, então `(pedido_id, produto_id)` é ótimo.

Se o padrão principal fosse “buscar por produto”, você poderia optar por `(produto_id, pedido_id)` como PK — ou manter PK e criar índice adicional.

### 2) Índices para filtros adicionais

Se você consulta frequentemente por data e cliente:

```sql
CREATE INDEX ix_pedidos_cliente_criado_em ON pedidos (cliente_id, criado_em);
```

Isso combina com o guia de índices em `08-otimizacao-de-consultas-e-indexes.md`.

---

## Anti-patterns comuns (e alternativas)

### Anti-pattern 1: guardar lista de IDs em uma coluna (CSV/JSON) para N:N

Ex.: `pedido.produtos = '1,2,3'` ou `pedido.produtos_json`.

**Problemas**:

- Dificulta indexação.
- JOINs e filtros ficam caros.
- Integridade referencial vira “manual”.

**Alternativa**: tabela intermediária.

### Anti-pattern 2: EAV (Entity-Attribute-Value) para tudo

Transformar tudo em `entidade_id, atributo, valor` dá flexibilidade, mas costuma destruir performance e legibilidade para consultas comuns.

**Alternativa**: use EAV só onde faz sentido, ou use JSON/documento quando o domínio for realmente dinâmico (avaliando NoSQL/híbridos).

---

## Resumo prático

- Relacionamento N:N em SQL → **tabela intermediária**.
- Índices:
  - FK frequentemente usada em JOIN/WHERE → **indexar**.
  - Tabela intermediária → PK composta + índice no lado inverso (quando necessário).
- Normalização é padrão; denormalização é **tática** para leitura (com cuidado).

## Próximo passo

Se você está investigando lentidão, volte para:

- [08-otimizacao-de-consultas-e-indexes.md](08-otimizacao-de-consultas-e-indexes.md)

