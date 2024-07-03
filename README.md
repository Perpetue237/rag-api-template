# rag-api-template
This repository proposes a template to set up and build a GPU-accelerated RAG-API with Docker Compose.

## Project Structure

```plaintext
|-- LICENSE
|-- README.md
|-- backend
|   |-- Dockerfile
|   |-- app
|   |-- requirements.txt
|-- docker-compose.yml
|-- frontend
|   |-- Dockerfile
|   |-- README.md
|   |-- index.html
|   |-- node_modules
|   |-- package-lock.json
|   |-- package.json
|   |-- public
|   |-- src
|   |-- tsconfig.app.json
|   |-- tsconfig.json
|   |-- tsconfig.node.json
|   `-- vite.config.ts
|-- models_loader.ipynb
`-- nginx
    `-- nginx.conf
```

## Dependencies (tested on UBUNTU 22.04) 

- NVIDIA drivers

- Docker:
    ```sh
        sudo bash install-docker.sh
    ```

- NVIDIA Container Toolkit:
    ```sh
        sudo bash install-nvidia-container-toolkit.sh
    ```

## Requirements

- Operating System: Windows, macOS, Linux
- Minimum Disk Space: 10GB
- Minimum Memory: 4GB RAM
- GPU Characteristics: NVIDIA RTX A2000 GPU with 4096MiB total memory



## Installation

1. Clone the repo:
    ```sh
    git clone https://github.com/Perpetue237/rag-api-template.git
    ```
2. Navigate to the project directory:
    ```sh
    cd rag-api-template
    ```
3. Sart the API:
    ```sh
    docker compose down
    docker volume prune
    docker-compose up --build -d
    ```
4. Visit the API
    http://localhost/
    
## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Contact

[Perpetue Kuete Tiayo](https://www.linkedin.com/in/perpetue-k-375306185)

