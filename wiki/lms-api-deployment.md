# LMS API deployment

<h2>Table of contents</h2>

- [About the LMS API deployment](#about-the-lms-api-deployment)
- [Deploy the LMS API on the VM](#deploy-the-lms-api-on-the-vm)
  - [Clone the repository (REMOTE)](#clone-the-repository-remote)
  - [Configure the environment (REMOTE)](#configure-the-environment-remote)
  - [Start the services (REMOTE)](#start-the-services-remote)
  - [Populate the database (LOCAL)](#populate-the-database-local)
  - [Verify the deployment (LOCAL)](#verify-the-deployment-local)

## About the LMS API deployment

This page describes how to deploy the [LMS API](./lms-api.md#about-the-lms-api) and additional [services](./docker-compose-yml.md#services) on [your VM](./vm.md#your-vm) using [`Docker Compose`](./docker-compose.md#what-is-docker-compose).

## Deploy the LMS API on the VM

1. [Connect to the VM as the user `admin` (LOCAL)](./vm-access.md#connect-to-the-vm-as-the-user-user-local).
2. [Clone the repository (REMOTE)](#clone-the-repository-remote).
3. [Configure the environment (REMOTE)](#configure-the-environment-remote).
4. [Start the services (REMOTE)](#start-the-services-remote).
5. [Populate the database (LOCAL)](#populate-the-database-local).
6. [Verify the deployment (LOCAL)](#verify-the-deployment-local).

### Clone the repository (REMOTE)

1. [Clone the repository](./git-vscode.md#clone-the-repo-using-the-vs-code-terminal) with the URL `https://github.com/<your-github-username>/se-toolkit-lab-6` to `~/se-toolkit-lab-6` using the `VS Code Terminal`.

   Replace the placeholder [`<your-github-username>`](./github.md#your-github-username).

4. To enter the [repository](./git.md#repository) directory,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd se-toolkit-lab-6
   ```

### Configure the environment (REMOTE)

1. To create the [environment file](./environments.md#env-file) for [`Docker`](./docker.md#what-is-docker),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

2. To open [`.env.docker.secret`](./dotenv-docker-secret.md#what-is-envdockersecret) in an editor,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   nano .env.docker.secret
   ```

3. Set the [`Autochecker` API credentials](./autochecker-api.md#autochecker-api-credentials):

   ```text
   AUTOCHECKER_API_LOGIN=<autochecker-api-login>
   AUTOCHECKER_API_PASSWORD=<autochecker-api-password>
   ```

   Replace the placeholders:

   - [`<autochecker-api-login>`](./autochecker-api.md#autochecker-api-login-placeholder)
   - [`<autochecker-api-password>`](./autochecker-api.md#autochecker-api-password-placeholder)

4. Set the [LMS API key](./lms-api.md#lms-api-key).

   ```text
   LMS_API_KEY=<lms-api-key>
   ```

   Replace the placeholder [`<lms-api-key>`](./lms-api.md#lms-api-key-placeholder).

5. Save and exit:

   1. Press `Ctrl+O`.
   2. Press `Enter`.
   3. Press `Ctrl+X`.

### Start the services (REMOTE)

1. To start all services in the background,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret up --build -d
   ```

   > <h3>Troubleshooting</h3>
   >
   > [**Port conflict (`port is already allocated`)**](./docker.md#port-conflict-port-is-already-allocated)
   >
   > [**Containers exit immediately**](./docker-compose.md#containers-exit-immediately)
   >
   > [**Image pull fails**](./docker.md#image-pull-fails)
   >
   > [**DNS resolution errors (`getaddrinfo EAI_AGAIN`)**](./docker.md#dns-resolution-errors-getaddrinfo-eai_again)

2. To check that the [containers](./docker.md#container) are running,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"
   ```

   You should see all four services running:

   ```text
   SERVICE    STATUS
   app        Up 50 seconds
   caddy      Up 49 seconds
   pgadmin    Up 50 seconds
   postgres   Up 55 seconds (healthy)
   ```

### Populate the database (LOCAL)

The [database](./database.md#what-is-a-database) starts empty.
You need to run the ETL pipeline to populate it with data from the [`Autochecker` API](./autochecker-api.md#about-the-autochecker-api).

1. Open in a browser: `<lms-api-base-url>/docs`.

   Replace the placeholders:

   - [`<lms-api-base-url>`](./lms-api.md#lms-api-base-url-placeholder)

   You should see the [`Swagger UI`](./swagger.md#what-is-swagger-ui) page.

2. [Authorize in `Swagger UI`](./swagger.md#authorize-in-swagger-ui) with the [`LMS_API_KEY`](./dotenv-docker-secret.md#lms_api_key) that you set in [`.env.docker.secret`](./dotenv-docker-secret.md#what-is-envdockersecret).

3. [Try the endpoint](./swagger.md#try-an-endpoint-in-swagger-ui) `POST /pipeline/sync`.

   You should get a response showing the number of items and logs loaded:

   ```json
   {
     "items_loaded": 120,
     "logs_loaded": 5000
   }
   ```

   > 🟦 **Note**
   >
   > The exact numbers depend on how much data the [`Autochecker` API](./autochecker-api.md#about-the-autochecker-api) has.
   > As long as both numbers are greater than 0, the sync worked.

4. [Try the endpoint](./swagger.md#try-an-endpoint-in-swagger-ui) `GET /items/`.

   You should get a non-empty array of items.

### Verify the deployment (LOCAL)

1. [Open `Swagger UI`](./swagger.md#open-swagger-ui).

2. Open in a browser: `<lms-api-base-url>/`.

   Replace the placeholder [`<lms-api-base-url>`](./lms-api.md#lms-api-base-url-placeholder).

   You should see the [frontend](./lms-frontend.md#about-the-lms-frontend).

3. Enter the [LMS API key](./lms-api.md#lms-api-key) to authenticate in the frontend.

4. Switch to the **Dashboard** tab.

   You should see charts with analytics data:

   - submissions timeline
   - score distribution
   - group performance
   - task pass rates

   > <h3>Troubleshooting</h3>
   >
   > If the dashboard shows no data or errors, make sure that:
   >
   > - The ETL sync completed successfully ([Populate the database](#populate-the-database-local)).
   > - You entered the correct LMS API key in the frontend.
   > - At least one lab works:
   >    1. Select a different lab in the dropdown (e.g., `lab-04`).
