# Payload Contract 2.0

Este é o contrato atual da integração `ai_usage`. O payload é normalizado pelo
coletor antes de ser enviado ao webhook. Nesta versão, o escopo é uso baseado
em janelas de tempo.

Providers que não usam janelas ficam fora deste contrato e deverão receber uma
extensão própria quando sua semântica estiver definida.

## Exemplo completo

```json
{
  "schema_version": "2.0",
  "collected_at": "2026-08-11T18:40:00.000Z",
  "provider": "codex",
  "status": "ok",
  "collector_data": {
    "id": "manual_test",
    "version": "2026.8.0",
    "transport": "webhook"
  },
  "account_data": {
    "id": "acct-provider-123",
    "id_kind": "provider_account_id",
    "label": "Personal",
    "username": "alves-dev",
    "email": "user@example.com",
    "plan": {"type": "plus"}
  },
  "usage_data": {
    "windows": [
      {
        "id": "short",
        "label": "5-hour window",
        "duration_seconds": 18000,
        "used_percent": 15,
        "reset_at": "2026-08-11T20:00:00.000Z",
        "limit_reached": false
      },
      {
        "id": "long",
        "label": "Weekly window",
        "duration_seconds": 604800,
        "used_percent": 21,
        "reset_at": "2026-08-16T18:40:00.000Z",
        "limit_reached": false
      }
    ]
  },
  "error": null
}
```

## Envelope

| Campo            | Obrigatório | Regra                                                                                                                  |
|------------------|-------------|------------------------------------------------------------------------------------------------------------------------|
| `schema_version` | sim         | Deve ser `2.0`.                                                                                                        |
| `collected_at`   | sim         | ISO 8601 com timezone. A integração normaliza para UTC.                                                                |
| `provider`       | sim         | Identificador estável em lowercase e `snake_case`. Pode ser `unknown`.                                                 |
| `status`         | sim         | `ok`, `not_authenticated`, `provider_unavailable`, `parse_error`, `rate_limited`, `ha_unavailable` ou `unknown_error`. |
| `collector_data` | sim         | Identifica o coletor, não a conta.                                                                                     |
| `account_data`   | sim         | Dados da conta e seu ID estável.                                                                                       |
| `usage_data`     | sim         | Lista de janelas em `usage_data.windows`.                                                                              |
| `error`          | condicional | `null` em sucesso; objeto com `code` e `message` em erro.                                                              |

`provider_data` não faz parte do contrato 2.0. Nome, fabricante, modelo, URL
de configuração, imagem da entidade e demais metadados são resolvidos pela
integração a partir de `provider`. Para `unknown`, são usados metadados
genéricos.

## Dados do coletor

```json
"collector_data": {
  "id": "browser_extension",
  "version": "2026.8.0",
  "transport": "webhook"
}
```

`id` identifica a implementação que coletou o dado. Valores conhecidos:
`browser_extension`, `shell_script`, `python_collector` e `manual_test`.
`version` é obrigatória. `transport` é opcional e descreve o meio de entrega.

O ID do coletor nunca participa da identidade da conta. Dois coletores podem
atualizar a mesma conta.

## Dados da conta

`account_data.id` é obrigatório em payloads com `status: "ok"`. Deve ser opaco,
estável e único dentro do provider. A integração compõe a identidade com
`provider + id`.

Valores recomendados para `id_kind`: `provider_account_id`,
`provider_user_id` ou `collector_generated_hash`.

Email, username e label são dados de apresentação. Não devem ser usados
diretamente em `unique_id`. O plano fica dentro de `account_data.plan`.

## Dados de uso

Em payloads bem-sucedidos, `usage_data.windows` deve conter uma ou mais
janelas. Cada janela possui:

| Campo                 | Obrigatório | Regra                                                              |
|-----------------------|-------------|--------------------------------------------------------------------|
| `id`                  | sim         | ID técnico estável e único dentro do payload. Não usar `window_1`. |
| `label`               | sim         | Nome legível da janela. Usado na apresentação das entidades.       |
| `duration_seconds`    | sim         | Duração positiva. 5 horas = `18000`; 7 dias = `604800`.            |
| `used_percent`        | sim         | Número entre `0` e `100`. O coletor envia este valor.              |
| `reset_at`            | sim         | ISO 8601 com timezone, representando o próximo reset.              |
| `limit_reached`       | sim         | Booleano que indica se a janela atingiu o limite.                  |
| `reset_after_seconds` | não         | Valor informativo. `reset_at` é a fonte principal.                 |

O coletor deve enviar `duration_seconds` mesmo quando a API original usa nomes
como `primary`, `secondary`, `session` ou `weekly`.

O coletor não envia `available_percent`. A integração calcula:

```text
available_percent = 100 - used_percent
```

## Disponibilidade

Não existe campo `availability` no payload. A integração cria
`binary_sensor.available` e calcula seu estado olhando todas as janelas:

```text
available = existe uma janela com limit_reached == false
```

Se não houver janelas válidas, ou se a coleta falhar, o sensor fica desligado.
Falhas de coleta, autenticação ou provider continuam sendo representadas por
`status` e `error`.

## Erros

Em sucesso, `error` deve ser `null`. Em erro, deve conter `code` e `message`.
Payloads de erro podem omitir `account_data.id` e enviar `usage_data.windows`
vazio. Nesse caso, a integração registra o erro como não associado a uma
conta.

## Segurança

Collectors nunca devem enviar cookies, tokens, HTML bruto, chaves de API,
headers de autenticação ou URLs privadas. Email pode ser enviado como dado de
apresentação, mas não deve participar diretamente da identidade técnica.
