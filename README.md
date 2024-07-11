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
|   |-- package-lock.json
|   |-- package.json
|   |-- public
|   |-- src
|   |-- tsconfig.app.json
|   |-- tsconfig.json
|   |-- tsconfig.node.json
|   `-- vite.config.ts
|-- install-docker.sh
|-- install-nvidia-container-toolkit.sh
|-- models_loader.ipynb
`-- nginx
    `-- nginx.conf
```

## Requirements

- Operating System: Windows, macOS, Linux
- Minimum Disk Space: 10GB
- Minimum Memory: 4GB RAM
- GPU Characteristics: NVIDIA RTX A2000 GPU with 4096MiB total memory

## Dependencies (tested on UBUNTU 22.04) 

- NVIDIA drivers
- Visual Studio Code (optional, for development)
- Jupyter Notebook (for downloading pre-trained models)

## Installation

### 1. Clone the repo:
```sh
git clone https://github.com/Perpetue237/rag-api-template.git
```

After cloning the repository, follow these steps to set up the project:

1. Install Docker and nvidia-container-toolkit.sh

> **Note:** The execution of this shell files reboot the notebook. To avoid this you may want to comment the corresponding lines out.

Navigate to the project directory:
```sh
cd rag-api-template
```

- Docker Desktop:
    ```sh
    echo   "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu lunar stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo bash install-docker.sh
    ```
    Reboot the system after a succesfull installation. 

- NVIDIA Container Toolkit:
    ```sh
        sudo bash install-nvidia-container-toolkit.sh
    ```


2. Create Directories
Create directories to store the models, tokenizers, and data. You can create these directories anywhere on your file system. Here is an example of how to create them in the project's root directory:

```sh
mkdir -p ~/rag-template/models/models
mkdir -p ~/rag-template/models/tokenizers
mkdir -p ~/rag-template/rag-uploads
```

3. Update `docker-compose.yml`
Modify the [docker-compose.yml](`docker-compose.yml`) file to mount these directories:

```yaml
services:
    backend:
        ...
        volumes:
        - /home/perpetue/rag-template/models/models:/app/models  # Mount the models directory
        - /home/perpetue/rag-template/models/tokenizers:/app/tokenizers  # Mount the tokenizers directory
        - /home/perpetue/rag-template/rag-uploads:/app/rag-uploads  # Mount the uploads directory
        ...
```
Replace `/home/perpetue/rag-template` with the path where you created the directories.

4. Update `.devcontainer/devcontainer.json`
If you are using VSCode for development, you need to mount these paths in the [.devcontainer/devcontainer.json](`devcontainer.json`) file:

```json
    ...
    "mounts": [
            "source=/home/perpetue/rag-template/models/models,target=/app/models,type=bind,consistency=cached",
            "source=/home/perpetue/rag-template/models/tokenizers,target=/app/tokenizers,type=bind,consistency=cached",
            "source=/home/perpetue/rag-template/rag-uploads,target=/app/rag-uploads,type=bind,consistency=cached"
        ],
    ...
```
Replace `/home/perpetue/rag-template` with the path where you created the directories.

5. Download Pre-trained Models
Use the [models_loader.ipynb](models_loader.ipynb) notebook to download the pre-trained models you want to use. Open the notebook in Jupyter Notebook or JupyterLab and follow the instructions to download the necessary models. You can put your huggingface token and openai keys in an `.env` file in the projekt root folder, according to the sample in [.env.sample](`.env.sample`). 

### 2. Navigate to the project directory:
    ```sh
    cd rag-api-template
    ```
### 3. Sart the API:
    ```sh
    docker compose down
    docker volume prune
    docker-compose up --build -d
    ```
### 4. Visit the API
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

