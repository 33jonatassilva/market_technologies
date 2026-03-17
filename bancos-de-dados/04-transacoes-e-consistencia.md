# Transações e consistência

Este documento explica **ACID** (típico em SQL), **BASE** (associado a muitos sistemas NoSQL distribuídos) e o **teorema CAP**, conceitos frequentes na documentação de mercado.

---

## ACID (bancos relacionais e alguns NoSQL)

**ACID** descreve propriedades de **transações** em muitos bancos SQL:


| Propriedade      | Significado                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| **Atomicidade**  | A transação **tudo ou nada**: ou todas as operações são aplicadas, ou nenhuma.                          |
| **Consistência** | O banco passa de um **estado válido** a outro válido (regras de negócio e integridade).                 |
| **Isolamento**   | Transações concorrentes não “veem” estados intermediários uns dos outros (níveis de isolamento variam). |
| **Durabilidade** | Após **commit**, os dados persistem mesmo com falha do processo (desde que o armazenamento sobreviva).  |


Bancos relacionais maduros oferecem transações ACID em **um único nó** ou, em produtos clusterizados, dentro de limites definidos pela arquitetura (ex.: uma partição).

---

## BASE (muitos NoSQL distribuídos)

**BASE** é um acrônimo usado para contrastar com ACID em sistemas que priorizam **disponibilidade** e **escala**:


| Componente               | Ideia                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------- |
| **Basically Available**  | O sistema permanece **disponível** na maior parte do tempo, mesmo com falhas parciais. |
| **Soft state**           | O estado pode mudar sem nova entrada (ex.: replicação em andamento).                   |
| **Eventual consistency** | Dado tempo **sem novas escritas**, as réplicas **convergem** para o mesmo valor.       |


Isso **não** significa que “NoSQL não tem transações”: muitos produtos oferecem transações **limitadas** ou **fortes** em escopo reduzido. A documentação oficial de cada produto define o comportamento.

Referência de mercado: [ACID vs BASE — AWS](https://aws.amazon.com/compare/the-difference-between-acid-and-base-database/).

---

## Teorema CAP (visão prática)

Em sistemas **distribuídos**, o teorema **CAP** afirma que, em presença de **partição de rede** (P), não é possível garantir simultaneamente **consistência forte** (C) e **disponibilidade perfeita** (A) sem trade-off.

- **C (Consistency)**: todas as leituras veem a escrita mais recente (visão simplificada).
- **A (Availability)**: toda requisição recebe resposta (não erro por indisponibilidade do nó).
- **P (Partition tolerance)**: o sistema continua operando apesar de falhas de rede entre nós.

Na prática, sistemas distribuídos **devem** tolerar partição; então escolhem-se **matizes** entre consistência e disponibilidade (ex.: leituras eventualmente consistentes vs leituras com quorum forte).

**SQL em cluster** e **NoSQL** podem posicionar-se de formas diferentes; a generalização “SQL = C+A” e “NoSQL = A+P” é **didática** mas **simplificada** — depende do produto e da configuração (ex.: níveis de consistência no cliente).

---

## Resumo


| Conceito | Uso típico na documentação                                                  |
| -------- | --------------------------------------------------------------------------- |
| **ACID** | Transações fortes; comum em SQL; alguns NoSQL em escopo limitado.           |
| **BASE** | Alta disponibilidade + eventual consistency em sistemas distribuídos NoSQL. |
| **CAP**  | Entender trade-offs em cluster; não substituir leitura da doc do produto.   |


## Próximo passo

[05-escalabilidade-e-performance.md](05-escalabilidade-e-performance.md) — escala vertical vs horizontal.

## Referências

- [ACID vs BASE — AWS](https://aws.amazon.com/compare/the-difference-between-acid-and-base-database/)
- [Relational vs. NoSQL data — Microsoft Learn](https://learn.microsoft.com/dotnet/architecture/cloud-native/relational-vs-nosql-data)

