# Development Notes

## Copy Integration To Local Core

Use the helper script to copy this custom integration into the local Home
Assistant Core checkout:

```bash
.dev/copy-to-core.sh
```

The script expects these local paths:

```text
/home/alves-dev/projects/python/ai-usage
/home/alves-dev/projects/others/core
```

## Reset Local Core Password

From the Home Assistant Core checkout, reset the local development user password
with:

```bash
hass --script auth --config config change_password igor dev
```
