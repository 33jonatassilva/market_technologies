# Introdução aos testes de software

## Por que testar?

Testes automatizados servem para:

- **Detectar regressões**: garantir que mudanças (refactors, novas features) não quebrem comportamento já existente.
- **Documentar comportamento**: um teste bem nomeado descreve o que o código deve fazer; testes são documentação executável.
- **Permitir refatorar com segurança**: com cobertura de testes, você pode melhorar o código sem medo de quebrar funcionalidades.
- **Reduzir bugs em produção**: falhas são encontradas antes do deploy, quando corrigir é mais barato.

## Benefícios em resumo

| Benefício | Descrição |
|-----------|-----------|
| Feedback rápido | Unitários rodam em segundos; você sabe na hora se algo quebrou. |
| Confiança | Integração e E2E validam que as partes funcionam juntas. |
| Menos medo de mudar | Refatoração e novas features com rede de segurança. |
| Menos bugs em produção | Problemas são encontrados no desenvolvimento ou no pipeline. |

## Pirâmide de testes

A **pirâmide de testes** é um modelo que sugere a proporção ideal de cada tipo de teste:

```
        /\
       /  \     E2E (poucos): fluxos críticos de ponta a ponta
      /----\
     /      \   Integração (alguns): APIs, banco, serviços
    /--------\
   /          \ Unitários (muitos): lógica isolada, rápidos
  /------------\
```

- **Base (maioria)**: **testes unitários** — muitos, rápidos, baratos, testam uma unidade (classe/método) isolada com mocks.
- **Meio**: **testes de integração** — menos que unitários, mais lentos, validam que componentes funcionam juntos (API + banco, serviços).
- **Topo (menoria)**: **testes E2E** — poucos, mais lentos e frágeis, simulam o usuário real e o sistema completo.

A ideia é ter **muita** confiança local (unitários) e **alguma** confiança em integração e E2E, sem que a suíte inteira fique lenta e difícil de manter.

## TDD (Test-Driven Development)

**TDD** é uma prática em que você **escreve o teste antes** do código de produção: primeiro define o comportamento esperado (teste falhando), depois implementa o mínimo para o teste passar e, por fim, refatora. O ciclo é conhecido como **Red — Green — Refactor**. Os testes desta documentação (unitários, integração, E2E) são a base para aplicar TDD: começar por um teste que falha e então implementar a funcionalidade.

## Próximo passo

No próximo documento você verá **conceitos e tipos** de testes em detalhe e em **qual escopo** utilizar cada um.

## Referências

- [Testes no .NET — Microsoft Learn](https://learn.microsoft.com/pt-br/dotnet/core/testing/)
- [Test Pyramid — Martin Fowler](https://martinfowler.com/articles/practical-test-pyramid.html)
