# rag-api-template
This repository propose a template to set up and build a RAG-API with docker

## Project Structure

```plaintext
|-- LICENSE
|-- README.md
|-- backend
|   |-- Dockerfile
|   `-- app
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
```

## Dependencies

- Docker

## Requirements

- Operating System: Windows, macOS, Linux
- Minimum Disk Space: 500MB
- Minimum Memory: 4GB RAM


## Installation

1. Clone the repo:
    ```sh
    git clone https://github.com/Perpetue237/rag-api-template.git
    ```
2. Navigate to the project directory:
    ```sh
    cd rag-api-templat
    ```
3. Install dependencies:
    ```sh
    docker compose down
    docker compose build  --no-cache
    docker compose up -d
    ```
    
## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - [Perpetue237](https://www.linkedin.com/in/perpetue-k-375306185)

