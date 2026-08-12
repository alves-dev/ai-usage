# Device And Sensor Contract 2.0

Este documento define os devices e entidades criados a partir do
[Payload Contract 2.0](payload-contract.md).

## Devices

A integração cria um device pai para a instância configurada e um device para
cada combinação de `provider` e `account_data.id`.

```text
device_key = <config_entry_id>:<provider>:<account_key>
```

O `account_key` é um hash estável derivado de `provider`, `account_data.id` e
do tipo do ID. Email, username e label não participam da identidade técnica.

O registro interno de providers resolve, sem dados adicionais no payload:

- nome exibido;
- fabricante;
- modelo;
- URL de configuração;
- imagem da entidade de conta.

Para `unknown`, são usados metadados e imagem genéricos quando disponíveis.

## Entidades comuns da conta

Cada device de conta possui as entidades comuns já existentes, incluindo conta,
plano, status, idade da amostra, erro, timestamps, coletor e contador de
requests.

Também possui:

```text
binary_sensor.available
binary_sensor.problem
```

`binary_sensor.available` é derivado de todas as janelas do payload. Ele fica
ligado se pelo menos uma janela tem `limit_reached: false`. Se não houver uma
janela válida ou a coleta falhar, fica desligado.

`binary_sensor.problem` representa erro do provider ou da coleta da conta; não
representa uma janela individual ter atingido o limite.

## Entidades por janela

Para cada item de `usage_data.windows`, a integração cria quatro entidades:

```text
sensor.window_<id>_used_percent
sensor.window_<id>_available_percent
binary_sensor.window_<id>_limit_reached
sensor.window_<id>_reset_at
```

O ID é convertido para um slug seguro para entidade. O `label` é usado no nome
visível; o ID é usado no `unique_id`.

### Percentual usado

```text
native_value = window.used_percent
unit = %
state_class = measurement
```

### Percentual disponível

O coletor não envia este campo. A integração calcula:

```text
native_value = 100 - window.used_percent
unit = %
state_class = measurement
```

### Limite atingido

```text
is_on = window.limit_reached
device_class = problem
```

### Reset

`window.reset_at` vira um sensor com `device_class: timestamp`. Se
`reset_after_seconds` estiver presente, ele pode ser exposto como atributo
diagnóstico; não é necessário criar uma quinta entidade.

## Atualização e persistência

Os sensores devem ser atualizados quando a conta receber novo payload. O
payload bruto não deve ser armazenado nos atributos das entidades.

As chaves das entidades devem usar o ID técnico da janela, nunca o label, a
duração ou o nome apresentado pelo provider. Isso evita que mudança de idioma
ou de nomenclatura quebre dashboards e automações.

## Providers sem janelas

Providers baseados em créditos, sugestões, métricas ou outros conceitos que
não sejam janelas estão fora do escopo deste contrato. Não devem ser forçados a
usar entidades de janela até que um novo contrato seja definido.
