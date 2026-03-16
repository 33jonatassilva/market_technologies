# Conceitos e tipos de testes

Este documento define **conceitos** comuns e os **tipos** de teste (unitário, integração, E2E e outros), com **escopo** e **quando usar** cada um.

---

## Conceitos fundamentais

### Unidade (unit)

A menor parte testável do código com sentido — em geral uma **classe** ou um **método** com responsabilidade clara. No teste unitário essa unidade é testada **isolada**: dependências externas (banco, HTTP, arquivos) são substituídas por **mocks** ou **stubs**.

### Mock (simulado)

Objeto que **simula** um dependência e permite **verificar** se foi chamado como esperado (quantas vezes, com quais argumentos). Ex.: “o repositório foi chamado com esse ID?”. Usado para garantir que a **unidade** interage corretamente com as dependências.

### Stub

Objeto que devolve **respostas fixas** para que a unidade rode sem depender do real. Ex.: “quando pedir o usuário por ID, retorne este usuário fake”. Foco em **comportamento da unidade**, não em verificar chamadas (embora mocks também possam fazer stub).

### Test double

Termo genérico para qualquer objeto que substitui o real em testes: mock, stub, fake, spy. Em .NET costuma-se usar “mock” para bibliotecas como Moq/NSubstitute que fazem tanto stub quanto verificação.

### Arrange-Act-Assert (AAA)

Padrão para estruturar um teste em três partes:

1. **Arrange**: preparar dados e dependências (objetos, mocks, estado).
2. **Act**: executar a única ação que está sendo testada.
3. **Assert**: verificar o resultado (valor retornado, chamadas a dependências, exceções).

Deixa o teste legível e com responsabilidade clara.

### Cobertura (coverage)

Medida do quanto do código é **executado** pelos testes (linhas, branches, métodos). Cobertura alta não garante bons testes, mas ajuda a encontrar trechos não exercitados. Não confunda cobertura com qualidade: testes ruins podem ter 100% de cobertura.

---

## Tipos de teste e escopo

### Teste unitário


| Aspecto                | Descrição                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| **O que testa**        | Uma unidade (classe/método) **isolada**, com dependências mockadas.                           |
| **Escopo**             | Pequeno: uma classe, um método, uma regra de negócio.                                         |
| **Dependências**       | Substituídas por mocks/stubs (sem banco, HTTP, disco real).                                   |
| **Velocidade**         | Muito rápido (milissegundos por teste).                                                       |
| **Quando usar**        | Sempre que houver lógica de negócio, validação, cálculos, orquestração que possa ser isolada. |
| **Proporção sugerida** | Maior parte da pirâmide (ex.: 60–70% dos testes).                                             |


**Exemplo de escopo**: serviço que calcula desconto; validator de CPF; mapper de entidade para DTO; orquestrador que chama repositório e envia evento (repositório e publicador mockados).

---

### Teste de integração


| Aspecto                | Descrição                                                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| **O que testa**        | Vários **componentes juntos**: API + banco, API + fila, serviço + repositório real (ou em memória).             |
| **Escopo**             | Médio: um fluxo que cruza fronteiras (HTTP → controller → serviço → banco).                                     |
| **Dependências**       | Reais ou substitutos realistas (banco em memória, TestContainers, API fake).                                    |
| **Velocidade**         | Mais lento que unitário (segundos).                                                                             |
| **Quando usar**        | Para validar que a API responde certo, que o banco persiste/recupera, que serialização e middlewares funcionam. |
| **Proporção sugerida** | Parte média da pirâmide (ex.: 20–30%).                                                                          |


**Exemplo de escopo**: “POST /clientes retorna 201 e o cliente aparece no banco”; “GET /pedidos/{id} retorna 404 quando não existe”.

---

### Teste end-to-end (E2E)


| Aspecto                | Descrição                                                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **O que testa**        | **Fluxo completo** como o usuário final: UI ou API pública, passando por todos os sistemas (app, banco, filas, outros serviços). |
| **Escopo**             | Grande: cenário de uso inteiro (ex.: “usuário faz login, cria pedido, vê confirmação”).                                          |
| **Dependências**       | Ambiente o mais próximo possível do real (ou produção-like).                                                                     |
| **Velocidade**         | Lento e mais frágil (minutos, dependendo do número de cenários).                                                                 |
| **Quando usar**        | Para poucos fluxos **críticos** (checkout, login, relatórios principais).                                                        |
| **Proporção sugerida** | Topo da pirâmide (ex.: 10–20%).                                                                                                  |


**Exemplo de escopo**: “do login ao pagamento aprovado” em um único teste; ou “upload de arquivo e notificação por e-mail”.

---

### Outros tipos (resumo)


| Tipo               | O que é                                                                                | Escopo típico                          |
| ------------------ | -------------------------------------------------------------------------------------- | -------------------------------------- |
| **Contrato**       | Garante que consumer e provider (ex.: API) seguem o mesmo contrato (request/response). | Integração entre serviços (ex.: Pact). |
| **Performance**    | Mede tempo, throughput, uso de recursos.                                               | Cenários críticos de carga.            |
| **Fumaça (smoke)** | Poucos testes que verificam se o sistema “sobe” e responde.                            | Após deploy ou em ambientes.           |


---

## Quando usar cada tipo (resumo)


| Objetivo                                         | Tipo recomendado      |
| ------------------------------------------------ | --------------------- |
| Validar regra de negócio, cálculo, validação     | Unitário              |
| Validar que API + banco/serviço funcionam juntos | Integração            |
| Validar fluxo completo crítico (como o usuário)  | E2E                   |
| Validar contrato entre serviços                  | Contrato (integração) |
| Validar tempo/resposta sob carga                 | Performance           |


---

## Referências

- [Unit testing — Microsoft Learn](https://learn.microsoft.com/pt-br/dotnet/core/testing/unit-testing-best-practices)
- [Integration tests — ASP.NET Core](https://learn.microsoft.com/pt-br/aspnet/core/test/integration-tests)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

