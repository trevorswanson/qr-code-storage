# qr-code-storage
Storage for all my smart home device's QR codes.

## Running with Docker

A Docker image is published to GitHub Container Registry whenever changes are
merged to the `main` branch. You can run it with docker compose:

```bash
docker compose up -d
```

The compose file mounts `qr_data_store.json` from the local `data` folder so
your codes persist between container restarts. QR codes are now rendered
client-side in the browser instead of storing image files.
