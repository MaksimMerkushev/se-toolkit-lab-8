# Lab setup

- [1. Required steps](#1-required-steps)
  - [1.1. Set up your fork](#11-set-up-your-fork)
    - [1.1.1. Fork the course instructors' repo](#111-fork-the-course-instructors-repo)
    - [1.1.2. Go to your fork](#112-go-to-your-fork)
    - [1.1.3. Enable issues](#113-enable-issues)
    - [1.1.4. Add a classmate as a collaborator](#114-add-a-classmate-as-a-collaborator)
    - [1.1.5. Protect your `main` branch](#115-protect-your-main-branch)
  - [1.2. Clean up the previous lab (LOCAL)](#12-clean-up-the-previous-lab-local)
  - [1.3. Clone your fork and open it in `VS Code` (LOCAL)](#13-clone-your-fork-and-open-it-in-vs-code-local)
  - [1.4. Set up the environment](#14-set-up-the-environment)
  - [1.5. Set up a coding agent](#15-set-up-a-coding-agent)
  - [1.6. Deploy the LMS API](#16-deploy-the-lms-api)
  - [1.7. Deploy the `Qwen Code` API](#17-deploy-the-qwen-code-api)
  - [1.8. Set up the agent environment](#18-set-up-the-agent-environment)

## 1. Required steps

> [!NOTE]
> This lab builds on the same tools and setup from Lab 5.
>
> If you completed Lab 5, most tools are already installed.
>
> The main changes are: a new repo, local deployment, and setting up LLM access.

### 1.1. Set up your fork

#### 1.1.1. Fork the course instructors' repo

1. [Fork](../../wiki/github.md#fork-a-repo) the [course instructors' repo](https://github.com/inno-se-toolkit/se-toolkit-lab-6).

We refer to your fork as `fork` and to the original repo as `upstream`.

#### 1.1.2. Go to your fork

1. [Go to your fork](../../wiki/github.md#go-to-your-fork).

   It should look like `https://github.com/<your-github-username>/se-toolkit-lab-6`.

#### 1.1.3. Enable issues

1. [Enable issues](../../wiki/github.md#enable-issues).

#### 1.1.4. Add a classmate as a collaborator

1. [Add a collaborator](../../wiki/github.md#add-a-collaborator) — your partner.
2. Your partner should add you as a collaborator in their repo.

#### 1.1.5. Protect your `main` branch

1. [Protect the `main` branch](../../wiki/github.md#protect-a-branch).

### 1.2. Clean up the previous lab (LOCAL)

1. [Open in `VS Code` the directory](../../wiki/vs-code.md#open-the-directory) where you store lab repositories.

2. To stop Lab 5 services that might be still running,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd se-toolkit-lab-5
   docker compose --env-file .env.docker.secret down
   cd ..
   ```

### 1.3. Clone your fork and open it in `VS Code` (LOCAL)

1. To clone your fork,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git clone https://github.com/<your-github-username>/se-toolkit-lab-6
   ```

   Replace the placeholder [`<your-github-username>`](../../wiki/github.md#your-github-username).

   > <h3>Troubleshooting</h3>
   >
   > [**`git` asks for a password**](./github.md#git-asks-for-a-password)
   >
   > [**`fatal: destination path <directory-path> already exists and is not an empty directory.`**](./github.md#fatal-destination-path-directory-path-already-exists-and-is-not-an-empty-directory)

2. [Open in `VS Code` the directory](../../wiki/vs-code.md#open-the-file-or-the-directory-using-code):
   `se-toolkit-lab-6`.

3. [Check that the current directory is `se-toolkit-lab-6`](../../wiki/shell.md#check-the-current-directory-is-directory-name).

### 1.4. Set up the environment

1. To install `Python` dependencies,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   uv sync --dev
   ```

2. To create the [environment file](../../wiki/environments.md#env-file) for [`Docker`](../../wiki/docker.md#what-is-docker),

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

3. [Open in `VS Code` the file](../../wiki/vs-code.md#open-the-file): [`.env.docker.secret`](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret)

4. Set the [`Autochecker` API credentials](../../wiki/autochecker-api.md#autochecker-api-credentials) in [`.env.docker.secret`](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret):

   ```text
   AUTOCHECKER_API_LOGIN=<autochecker-api-login>
   AUTOCHECKER_API_PASSWORD=<autochecker-api-password>
   ```

   Replace the placeholders:

   - [`<autochecker-api-login>`](../../wiki/autochecker-api.md#autochecker-api-login-placeholder)
   - [`<autochecker-api-password>`](../../wiki/autochecker-api.md#autochecker-api-password-placeholder)

5. Set the [LMS API key](../../wiki/lms-api.md#lms-api-key) in `.env.docker.secret`:

   ```text
   LMS_API_KEY=<lms-api-key>
   ```

   Replace the placeholder [`<lms-api-key>`](../../wiki/lms-api.md#lms-api-key-placeholder).

### 1.5. Set up a coding agent

> [!NOTE]
> You should already have a [coding agent](../../wiki/coding-agents.md#what-is-a-coding-agent) from Lab 5.

1. If you don't have an agent, [set one up](../../wiki/coding-agents.md#choose-and-use-a-coding-agent).

### 1.6. Deploy the LMS API

> [!NOTE]
> The [`Autochecker`](../../wiki/autochecker.md#what-is-the-autochecker) tests your agent against your **deployed backend on your VM**.
>
> You need to deploy the services there.

1. [Deploy the LMS API on your VM](../../wiki/lms-api-deployment.md#deploy-the-lms-api-on-the-vm).

### 1.7. Deploy the `Qwen Code` API

> Your agent needs an [LLM](../../wiki/llm.md) to answer questions.
>
> [`Qwen Code`](../../wiki/qwen-code.md#what-is-qwen-code) provides **1000 free requests per day** and works from Russia — no VPN or credit card needed.

1. [Deploy the `Qwen Code` API on your VM](../../wiki/qwen-code-api-deployment.md#deploy-the-qwen-code-api-remote).

2. [Check that the `Qwen Code` API is accessible](../../wiki/qwen-code-api-deployment.md#check-that-the-qwen-code-api-is-accessible) on your local machine.

### 1.8. Set up the agent environment

1. To create the agent [environment file](../../wiki/environments.md#env-file),

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.agent.example .env.agent.secret
   ```

2. Set the values in [`.env.agent.secret`](../../wiki/dotenv-agent-secret.md#about-envagentsecret):

   ```text
   LLM_API_KEY=<qwen-code-api-key>
   LLM_API_BASE_URL=<qwen-code-api-base-url>
   LLM_API_MODEL=coder-model
   ```

   Replace the placeholders:

   - [`<qwen-code-api-key>`](../../wiki/qwen-code-api.md#qwen-code-api-key)
   - [`<qwen-code-api-base-url>`](../../wiki/qwen-code-api.md#qwen-code-api-base-url-placeholder)

3. (Alternative) Use `OpenRouter`

   If you prefer [OpenRouter](https://openrouter.ai), register and get an API key.

   Then set in [`.env.agent.secret`](../../wiki/dotenv-agent-secret.md#about-envagentsecret):

   ```text
   LLM_API_KEY=<your-openrouter-key>
   LLM_API_BASE_URL=https://openrouter.ai/api/v1
   LLM_API_MODEL=meta-llama/llama-3.3-70b-instruct:free
   ```

---

You're all set.
Now go to the [tasks](../../README.md#tasks).
