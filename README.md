# Digikala-Seller-Assistant

## Table of Contents

- [Digikala-Seller-Assistant](#Digikala-Seller-Assistant)
  - [Introduction](#introduction)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
  - [License](#license)

## Introduction

## Getting Started

1. **Clone the Repository**
   To get this repository, run the following command inside your terminal
   ```shell
   git clone https://github.com/alimashayekhy/Digikala-Seller-Assistant
   ```

### Installation

Make sure to perform the following step:

1. **Running the Project:**

Important -> **_Run project in linux_**

To run the project, use the following command:

```shell
unicorn main:app --host 127.0.0.1 --port 8000 --reload
```

This command will start the Fast API and run your project.

2. **Install dependencies:**

```shell
pip3 install pika
pip3 install asyncio
sudo rabbitmq-plugins enable rabbitmq_management
sudo service rabbitmq-server restart
pip3 install fastapi
pip install pytz
pip install pathlib
```

3. **Access rabbitmq:**

```shell
http://127.0.0.1:your-port
```

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
