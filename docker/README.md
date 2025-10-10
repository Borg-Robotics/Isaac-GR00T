# Docker

The image can be created in two ways:
- By building the local Dockerfile with
  ```bash
  docker compose -f docker/compose.yaml up --build
  ```
- By pulling the image from DockerHub with
  ```bash
  docker compose -f docker/cloud_compose.yaml up --build
  ```

