# Versionamento

A integração segue o formato de versão do Home Assistant:

```text
YYYY.M.patch
```

Exemplo de release:

```text
2026.8.1
```

Builds da branch `develop` usam o sufixo:

```text
2026.8.1-dev
```

O mesmo padrão deve ser usado pelos coletores mantidos junto com o projeto,
incluindo a versão enviada em `collector_data.version`. A extensão de
navegador é mantida em um repositório separado:

https://github.com/alves-dev/ai-usage-extension

O workflow `create-release.yml` usa `scripts/set_version.py` para atualizar as
fontes de versão do repositório:

- `custom_components/ai_usage/manifest.json`;
- `custom_components/ai_usage/const.py`;
- `pyproject.toml`;
- badge de versão do `README.md`.

Uso local:

```bash
python3 scripts/set_version.py 2026.8.1
```
