# Escalabilidade e performance

## Escala vertical (scale up) — comum em SQL

**Escala vertical** significa **aumentar recursos do mesmo servidor**: mais CPU, RAM, disco mais rápido (SSD/NVMe).

- Típico em bancos **relacionais** monolíticos ou primários.
- Limite físico e de custo: chega um ponto em que “subir a máquina” fica caro ou inviável.
- **Réplicas de leitura** aliviam leituras sem particionar dados de escrita.

Documentação de mercado frequentemente associa SQL a **scale up** como padrão principal (com réplicas e, em alguns casos, sharding manual).

---

## Escala horizontal (scale out) — comum em NoSQL

**Escala horizontal** significa **adicionar mais nós** (servidores) ao cluster; dados e carga são **distribuídos**.

- Típico em **NoSQL** projetado para distribuição (Dynamo-like, Cassandra, sharded MongoDB, etc.).
- Permite crescer com **commodity hardware** e, em nuvem, com **auto-scaling**.
- Exige **modelagem** alinhada à **chave de partição** (evitar hot partitions) e aceitar trade-offs de consistência/latência conforme o produto.

---

## Padrões de acesso e performance

| Padrão | SQL | NoSQL |
|--------|-----|--------|
| Consulta por **chave primária** | Muito eficiente | Muito eficiente (chave-valor, documento por ID) |
| **JOINs** em várias tabelas | Otimizado pelo otimizador | Frequentemente **evitados**; dados desnormalizados ou múltiplas queries |
| **Agregações complexas** | SQL (GROUP BY, window functions) | Depende do produto; às vezes feito em camada de analytics (warehouse) |
| **Throughput de escrita** massivo | Pode exigir particionamento cuidadoso | Muitos NoSQL são desenhados para alta ingestão por partição |

**Performance** depende de **índices**, **modelo de dados**, **tamanho dos dados** e **hardware** — não de “SQL ser lento” ou “NoSQL ser rápido” de forma absoluta.

---

## Resumo

- **SQL**: escala vertical + réplicas; sharding possível, porém mais operacional.
- **NoSQL**: escala horizontal como diferencial em vários produtos; modelagem por chave de partição é crítica.

## Próximo passo

[06-casos-de-uso-e-quando-escolher.md](06-casos-de-uso-e-quando-escolher.md) — quando usar cada abordagem.

## Referências

- [Relational vs. NoSQL data — Microsoft Learn](https://learn.microsoft.com/dotnet/architecture/cloud-native/relational-vs-nosql-data)
- [What is NoSQL? — AWS](https://aws.amazon.com/nosql/)
