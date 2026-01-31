# Running Flow on Docker

> Source: [Flow Support - Running Flow on Docker](https://support.flow-software.com/hc/en-us/articles/13724930621202-Running-Flow-on-Docker)

From Flow 7.0, the Flow Bootstrap can be installed and configured to run on Docker. This means that you can deploy Data Engines, Integration Engines, Message Engines, Data Sources, and Data Consumers to Docker containers.

## Prerequisites

- A basic understanding of what a Docker container is and how to configure it
- An advanced understanding of Docker networking is required if you intend to use Flow in Docker containers that need to communicate with each other, or with other nodes on a domain
- One or more hosts on which your Docker containers will run. This may be an instance of Docker Desktop running on your Windows, Linux, or macOS computer; or you may choose to run a Docker daemon and client on a Linux machine, either on-premise or in the cloud. The following resources are helpful:
  - [Docker docs: Docker overview](https://docs.docker.com/get-started/overview/)
  - [Docker docs: Overview of Docker Desktop](https://docs.docker.com/desktop/)

## Using a Console Terminal to execute Docker Commands

Once you have your environment running a Docker client, use the following command to pull the latest version of the Flow Bootstrap:

```bash
sudo docker pull flowsoftwareinc/flowbootstrap:latest
```

The above command pulls a Docker Image from Docker Hub.

> **Note:** This will stop the Flow components that are currently running in your environment. Please exercise caution when doing this in Production and plan for Flow to be unavailable while the components are being upgraded to the latest version and then are restarted.

To run a docker container hosting the Flow Bootstrap, execute the following command in a terminal:

```bash
sudo docker run --name flowbootstrap -h HOSTNAME -p 4501:4501 -p 80:80 -p 443:443 -td flowsoftwareinc/flowbootstrap:latest
```

### Parameter Reference

| Parameter | Description |
|-----------|-------------|
| `--name flowbootstrap` | You are explicitly naming your docker container "flowbootstrap". You can change this name according to your organization's policies. Note that a docker container name must be unique. If you leave out this parameter, your system will generate a container name for you, which may be acceptable. This parameter is not used by the Flow Bootstrap. |
| `-h HOSTNAME` | You are specifying a name (in this case HOSTNAME) that will be referenced internally by the Flow Bootstrap inside the Docker container. It may be the same as the --name specified. However, keep a record of this name because it is used by the Flow instance when configuring and communicating with this container. Your hostname must be unique across all containers on the same host. |
| `-p HOST_PORT:CONTAINER_PORT` | This creates a mapping between a network port in the container and a network port in the host. |
| `-t` | This allocates a terminal or console inside the container which allows you to interact with the container as if it were a standard UNIX-like system. |
| `-d` | This runs the container in a "detached mode" to make sure it starts in the background and does not block the terminal that started it. Note, in the example above both the t and d options have been combined into `-td`. |
| `flowsoftwareinc/flowbootstrap:latest` | This creates a container using the image named "flowsoftwareinc/flowbootstrap:latest". |

### Port Mappings

In the example provided, three ports are mapped:

| Port | Purpose |
|------|---------|
| **4501** | Default port that Flow components use to communicate with each other. The container port must align with the Flow instance's system configuration. The host port must be unique per host. |
| **80** | Default port that the Flow Server is configured to use. |
| **443** | Default port that the Flow components use if HTTPS is configured. |

## Flow System Configuration

From within a Linux or Docker system, you typically need to specify a SQL username and password for the Bootstrap to communicate with the Flow Database.

**In the Flow Config tool, open the `SYSTEM\Properties` and make sure to set the Username and Password properties.**

## Flow Platform Naming

Naming a Flow Platform requires an additional reference to bind it to the correct Docker container. This is why the HOSTNAME parameter is required when creating the container.

### Platform Name Format

```
<host name or IP address>:<host port>;<docker host name>
```

**Important:** Notice the colon to designate the port, and semicolon to designate the docker host name.

### Example

```
123.45.67.89:4501;Bootstrap1
```

Where the Docker HOSTNAME was specified as `Bootstrap1`.

## Useful Docker Commands

### View pulled images

```bash
sudo docker images
```

### View running containers

```bash
sudo docker ps
```

Pay attention to the "Container ID" and "Names" fields, because either of these may be used to reference your container in other Docker commands. The Container ID is a hexadecimal string of 64 characters, but is usually abbreviated to the first 12 characters - these 12 characters are sufficient to reference the Docker container.

You can even use just the first 1 or 2 characters of the Container ID to reference the container, as long as those characters uniquely identify the container on your host.

### Stop a container

```bash
sudo docker stop CONTAINER_ID (or CONTAINER_NAME)
```

### Remove a container

```bash
sudo docker rm CONTAINER_ID (or CONTAINER_NAME)
```

### View container statistics (CPU, Memory)

```bash
sudo docker stats
```

Use `Ctrl+C` to exit.

### View live logs (similar to Windows Event Viewer)

```bash
sudo docker container logs CONTAINER_ID (or CONTAINER_NAME) --since 360m --follow
```

Use `Ctrl+C` to exit.

### Access the shell within a container

```bash
sudo docker exec -it CONTAINER_ID (or CONTAINER_NAME) sh
```

After executing the above command, you'll be within the shell of the container. This allows you to access Linux commands, such as to edit files within the container (e.g. the `/app/Bootstrap.settings` file). To exit the shell, type the word `exit` and press Enter.

### View detailed container configuration

```bash
sudo docker inspect CONTAINER_ID (or CONTAINER_NAME)
```

### View mapped ports

```bash
sudo docker port CONTAINER_ID (or CONTAINER_NAME)
```

## Using Docker Desktop

If you are using Docker Desktop, you can search for the Flow Bootstrap image by typing "flowsoftwareinc" in the Search bar at the top - you should find two options for the Flow Bootstrap:

- One for **Intel processors** (standard)
- One for **Arm processors** (suffixed by the word "Arm")

Once you've pulled the image, you will see the latest version of the Flow Bootstrap image available.

> **Recommendation:** Use Docker console/terminal commands to create your Docker containers because these provide the flexibility required to specify the hostname, map ports, etc.

---

## ProveIT Edge Stack Notes

For the ProveIT Analytics stack deployment:

| Setting | Value |
|---------|-------|
| Container Name | `proveit-analytics-flow-bootstrap` |
| Docker Hostname | `analytics-flow-bootstrap` |
| Bootstrap Port | `4501` |
| Platform Name Format | `<server-ip>:4501;analytics-flow-bootstrap` |

### Example Platform Names

- Local Windows: `localhost:4501;analytics-flow-bootstrap`
- Ubuntu Server: `192.168.30.231:analytics-flow-bootstrap`

---

## Database Configuration via Flow Config Tool

**Important:** Flow Bootstrap does NOT use environment variables for database configuration. The database must be configured through the Flow Config Tool.

### Step 1: Connect to Flow Bootstrap

1. Open **Flow Config Tool**
2. Enter platform name: `localhost:4501;analytics-flow-bootstrap`
3. Click Connect

### Step 2: Configure Database

1. Navigate to `SYSTEM\Properties`
2. Set the following values:

| Property | Value (Local Windows) | Value (Docker Internal) |
|----------|----------------------|------------------------|
| Server | `localhost,1433` | `analytics-mssql,1433` |
| Database | `FlowSoftware` | `FlowSoftware` |
| Username | `sa` | `sa` |
| Password | `Password1@` | `Password1@` |

**Note:** Use `localhost,1433` when running Config Tool from the host machine. Use `analytics-mssql,1433` only if Config Tool is running inside the Docker network.

### Step 3: Verify Connection

After saving the database configuration, Flow should create the `FlowSoftware` database in MSSQL automatically.

To verify the database was created:
```bash
docker exec proveit-analytics-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Password1@" -C -Q "SELECT name FROM sys.databases WHERE name = 'FlowSoftware'"
```

---

## Quick Start (Local Windows)

```bash
# 1. Create network (if not exists)
docker network create operations-network

# 2. Start the stack
cd stacks/analytics
docker compose up -d

# 3. Verify containers
docker ps --filter "name=proveit-analytics"

# 4. Connect Flow Config Tool
# Platform name: localhost:4501;analytics-flow-bootstrap

# 5. Configure database in SYSTEM\Properties:
#    Server: localhost,1433
#    Database: FlowSoftware
#    Username: sa
#    Password: Password1@
```
