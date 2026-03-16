# Testes E2E e outros tipos

Este documento cobre **testes end-to-end (E2E)** e outros tipos (contrato, fumaça, performance) no ecossistema .NET.

---

## Testes end-to-end (E2E)

### Escopo

- Simular o **usuário** ou o **cliente** do sistema: fluxo completo do início ao fim.
- Incluir **todos** os componentes necessários: aplicação, banco, filas, APIs externas (ou stubs contratados), e quando aplicável a **interface** (browser ou cliente da API).

### Quando usar

- **Poucos** cenários **críticos**: login, checkout, geração de relatório principal, fluxo de aprovação.
- Validação antes de release ou em pipeline (nightly, staging).
- Não substituir unitários e integração: E2E é lento e mais frágil; use para confiança final em fluxos importantes.

### Exemplo conceitual (API como “fim” do fluxo)

Se o “fim” for a API (sem UI), o E2E pode ser um teste de integração “grande” que percorre um cenário completo:

```csharp
[Fact]
public async Task FluxoCompleto_ClienteCriaPedido_RecebeConfirmacao()
{
    // 1. Criar cliente
    var createCliente = await _client.PostAsJsonAsync("/api/clientes", new { Nome = "E2E User", Email = "e2e@test.com" });
    createCliente.EnsureSuccessStatusCode();
    var cliente = await createCliente.Content.ReadFromJsonAsync<ClienteResponse>();

    // 2. Criar pedido
    var createPedido = await _client.PostAsJsonAsync("/api/pedidos", new { ClienteId = cliente!.Id, Itens = new[] { new { ProdutoId = 1, Quantidade = 2 } } });
    createPedido.EnsureSuccessStatusCode();
    var pedido = await createPedido.Content.ReadFromJsonAsync<PedidoResponse>();

    // 3. Simular pagamento aprovado (ou chamar API de pagamentos em ambiente de teste)
    var pagamento = await _client.PostAsJsonAsync($"/api/pedidos/{pedido!.Id}/pagamento", new { Aprovado = true });
    pagamento.EnsureSuccessStatusCode();

    // 4. Verificar estado final
    var pedidoAtualizado = await _client.GetFromJsonAsync<PedidoResponse>($"/api/pedidos/{pedido.Id}");
    pedidoAtualizado!.Status.Should().Be("Pago");
}
```

Para E2E com **navegador** (UI), use **Playwright** ou **Selenium** com .NET; a ideia é a mesma: um fluxo completo como o usuário.

### Ferramentas E2E no .NET

| Ferramenta | Uso |
|------------|-----|
| **Playwright** | Automação de browser (Chromium, Firefox, WebKit); muito usado para E2E de UI. |
| **Selenium** | Clássico para automação de browser. |
| **WebApplicationFactory + HttpClient** | E2E “só API”: fluxo completo via HTTP, sem UI. |

---

## Testes de contrato

- Garantem que **consumer** e **provider** (ex.: sua API e quem a consome) respeitam o mesmo **contrato** (request/response, schema).
- **Pact** (consumer-driven): o consumer define o contrato; o provider é testado contra ele. Evita que mudanças na API quebrem consumidores.
- Escopo: integração entre serviços; uso em microserviços.

---

## Testes de fumaça (smoke)

- **Poucos** testes que verificam se o sistema “sobe” e responde (ex.: GET /health retorna 200).
- Úteis após deploy ou em ambientes (homolog, staging) para detectar falha grosseira.

Exemplo:

```csharp
[Fact]
public async Task Health_DeveRetornar200()
{
    var response = await _client.GetAsync("/health");
    response.StatusCode.Should().Be(HttpStatusCode.OK);
}
```

---

## Testes de performance

- Medem **tempo**, **throughput** ou **uso de recursos** sob carga.
- Ferramentas: **NBomber**, **k6**, **JMeter**, **BenchmarkDotNet** (para micro-benchmarks).
- Escopo: cenários críticos (ex.: “GET /relatorio deve responder em < 2s com 100 usuários concorrentes”).

---

## Resumo

| Tipo | Objetivo | Escopo |
|------|----------|--------|
| E2E | Validar fluxo completo crítico | Sistema inteiro (API + serviços ou UI + API). |
| Contrato | Garantir compatibilidade consumer/provider | Request/response entre serviços. |
| Fumaça | Verificar se o sistema responde | Poucos endpoints (ex.: health). |
| Performance | Medir tempo e carga | Cenários críticos. |

## Próximo passo

Em [06-tecnologias-dotnet.md](06-tecnologias-dotnet.md) você verá as **tecnologias de mercado** no .NET para testes (xUnit, Moq, FluentAssertions, etc.).

## Referências

- [Playwright .NET](https://playwright.dev/dotnet/)
- [Pact — contract testing](https://pact.io/)
- [NBomber](https://nbomber.com/)
