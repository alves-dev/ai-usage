# Account Stable ID Decision

Data: 2026-06-03

Status: nao aprovado para o contrato atual.

## Contexto

Durante a definicao do contrato de devices e sensores, foi considerada a
inclusao de um campo de conta estavel e opaco no payload:

```json
{
  "account_data": {
    "stable_id": "provider-generated-or-source-generated-stable-id"
  }
}
```

A motivacao era evitar o uso de dados alteraveis, como email ou username, na
base de criacao do `account_key`.

## Analise

Para `codex`, o payload ja pode fornecer identificadores melhores:

```text
account_data.account_id
account_data.user_id
```

Para `ollama_cloud`, a pagina atualmente nao expoe um ID visivel ou oculto que
possa ser extraido de forma confiavel. Os dados disponiveis para identificar a
conta sao:

```text
account_data.email
account_data.username
```

Entre esses dois campos, `email` foi considerado mais adequado para a chave
pratica da conta, pois tende a mudar menos que `username`.

## Decisao

Nao adicionar `account_data.stable_id` ao contrato atual.

Para providers sem `account_id` ou `user_id`, como `ollama_cloud`, usar:

```text
account_key = "acct_" + sha256("<provider>:email:<email_normalizado>")[0:16]
```

Exemplo:

```text
provider = "ollama_cloud"
email_normalizado = "user@example.com"
account_key = "acct_91x6b51xx7f03227"
```

O email normalizado deve ser usado apenas como entrada do hash. O valor cru nao
deve ser usado em `unique_id` ou `DeviceInfo.identifiers`.

## Consequencias

- Nao sera necessario alterar o contrato de payload para incluir um campo novo.
- `ollama_cloud` podera criar devices dinamicos com base nos dados ja
  disponiveis.
- Se o usuario trocar o email da conta no provider, a integracao podera criar
  um novo device, pois o `account_key` mudara.
- Email e username continuam permitidos como dados de exibicao em atributos e no
  nome do device.

## Revisao Futura

Esta decisao pode ser reavaliada se um provider passar a expor um ID de conta
estavel ou se houver necessidade real de suportar troca de email sem criar novo
device no Home Assistant.
