# Coletor manual

O script [`scripts/manual_collector.py`](../scripts/manual_collector.py) gera
um payload 2.0 válido e, opcionalmente, envia esse payload para um webhook do
Home Assistant.

## Apenas imprimir o payload

```bash
python3 scripts/manual_collector.py
```

## Testar valores e limites

```bash
python3 scripts/manual_collector.py \
  --provider codex \
  --account-id manual-account-001 \
  --short-used 100 \
  --long-used 45
```

O script imprime duas janelas (`short` e `long`). O coletor envia somente
`used_percent`; `available_percent` deve aparecer apenas como sensor calculado
no Home Assistant.

## Enviar ao webhook

```bash
python3 scripts/manual_collector.py \
  --url "http://homeassistant.local:8123/api/webhook/<WEBHOOK_ID>"
```

O ID do webhook deve ser tratado como segredo. O script não envia tokens ou
credenciais adicionais.

Opções úteis:

```text
--provider
--account-id
--account-label
--plan
--short-used
--long-used
--short-label
--long-label
--url
```
