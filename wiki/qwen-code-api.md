# `Qwen Code` API

<h2>Table of contents</h2>

- [What is `Qwen Code` API](#what-is-qwen-code-api)
- [`Qwen Code` API key](#qwen-code-api-key)
- [`Qwen Code` API host port](#qwen-code-api-host-port)
  - [`<qwen-code-api-host-port>` placeholder](#qwen-code-api-host-port-placeholder)
- [`Qwen Code` API base URL](#qwen-code-api-base-url)
  - [`<qwen-code-api-base-url>` placeholder](#qwen-code-api-base-url-placeholder)
- [Set up the `Qwen Code` API (REMOTE)](#set-up-the-qwen-code-api-remote)
  - [Set up the `Qwen Code` CLI (REMOTE)](#set-up-the-qwen-code-cli-remote)
  - [Clone the `Qwen Code` API repository (REMOTE)](#clone-the-qwen-code-api-repository-remote)
  - [Pull the latest changes from the `Qwen Code` API repository (REMOTE)](#pull-the-latest-changes-from-the-qwen-code-api-repository-remote)
  - [Enter the `Qwen Code` API repository directory (REMOTE)](#enter-the-qwen-code-api-repository-directory-remote)
  - [Prepare the environment in the `Qwen Code` API repository (REMOTE)](#prepare-the-environment-in-the-qwen-code-api-repository-remote)
  - [Start the `Qwen Code` API (REMOTE)](#start-the-qwen-code-api-remote)
  - [Check that the `Qwen Code` API is accessible](#check-that-the-qwen-code-api-is-accessible)

## What is `Qwen Code` API

<!-- TODO visualize -->

The `Qwen Code` API is an [OpenAI-compatible API](./llm.md#openai-compatible-api) that uses the [`Qwen Code` credentials file](./qwen-code.md#qwen-code-credentials-file) to provide access to the [`Qwen` API](./qwen-code.md#qwen-api).

The `Qwen Code` API is deployed using [`qwen-code-api`](https://github.com/inno-se-toolkit/qwen-code-api).

## `Qwen Code` API key

The [API key](./web-api.md#api-key) that is used to authorize requests to the [`Qwen Code` API](#what-is-qwen-code-api).

You can use almost any (alphanumeric) string as the `Qwen Code` API key.

You store the key in [`QWEN_CODE_API_KEY`](./qwen-code-api-dotenv-secret.md#qwen_code_api_key) in [`qwen-code-api/.env.secret`](./qwen-code-api-dotenv-secret.md#qwen_code_api_key).

## `Qwen Code` API host port

The [port](./computer-networks.md#port) at which the [`Qwen Code` API](./qwen-code-api.md#what-is-qwen-code-api) is available on the [host](./computer-networks.md#host) where it is deployed.

### `<qwen-code-api-host-port>` placeholder

The [`Qwen Code` API host port](#qwen-code-api-host-port) (without `<` and  `>`).

## `Qwen Code` API base URL

- (REMOTE) When running the request on the VM (does not depend on whether the [LMS API is deployed on the VM](./lms-api-setup.md#deploy-the-lms-remote)):
  
  `http://localhost:<qwen-code-api-host-port>/v1`

- (REMOTE or LOCAL) When the [LMS API is deployed on the VM](./lms-api-setup.md#deploy-the-lms-remote):
  
  `<lms-api-base-url>/utils/qwen-code-api/v1`
  
Replace the placeholders:

- [`<qwen-code-api-host-port>`](#qwen-code-api-host-port-placeholder)
- [`<lms-api-base-url>`](./lms-api.md#lms-api-base-url-placeholder)

See:

- [`localhost`](./computer-networks.md#localhost)

### `<qwen-code-api-base-url>` placeholder

[`Qwen Code` API base URL](#qwen-code-api-base-url) (without `<` and `>`).

## Set up the `Qwen Code` API (REMOTE)

Complete these steps:

1. [Set up the `Qwen Code` CLI (REMOTE)](#set-up-the-qwen-code-cli-remote).
2. [Clone the `Qwen Code` API repository (REMOTE)](#clone-the-qwen-code-api-repository-remote).
3. [Pull the latest changes from the `Qwen Code` API repository (REMOTE)](#pull-the-latest-changes-from-the-qwen-code-api-repository-remote).
4. [Enter the `Qwen Code` API repository directory (REMOTE)](#enter-the-qwen-code-api-repository-directory-remote).
5. [Prepare the environment in the `Qwen Code` API repository (REMOTE)](#prepare-the-environment-in-the-qwen-code-api-repository-remote).
6. [Start the `Qwen Code` API (REMOTE)](#start-the-qwen-code-api-remote).
7. [Check that the `Qwen Code` API is accessible](#check-that-the-qwen-code-api-is-accessible) on the VM (REMOTE).

### Set up the `Qwen Code` CLI (REMOTE)

1. [Connect to the VM](./vm-access.md#connect-to-the-vm).

2. [Install `Node.js`](./nodejs.md#install-nodejs).

3. [Install `pnpm`](./nodejs.md#install-pnpm).

4. To install [`Qwen Code`](./qwen-code.md#what-is-qwen-code),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   pnpm add -g @qwen-code/qwen-code
   ```

5. [Open a chat with `Qwen Code` using the CLI](./qwen-code.md#open-a-chat-with-qwen-code-using-the-cli).

6. Type `/auth` in the chat to [authenticate via Qwen OAuth](https://github.com/QwenLM/qwen-code?tab=readme-ov-file#authentication).

7. Open the link in a browser to complete the authentication procedure.

8. [Quit the chat with `Qwen Code`](./qwen-code.md#quit-the-chat-with-qwen-code).

### Clone the `Qwen Code` API repository (REMOTE)

1. [Clone the repository](./git-vscode.md#clone-the-repo-using-the-vs-code-terminal) with the URL `https://github.com/inno-se-toolkit/qwen-code-api` to `~/qwen-code-api`.

### Pull the latest changes from the `Qwen Code` API repository (REMOTE)

1. To pull the latest changes,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git pull
   ```

### Enter the `Qwen Code` API repository directory (REMOTE)

1. To enter the repository directory,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd ~/qwen-code-api
   ```

### Prepare the environment in the `Qwen Code` API repository (REMOTE)

1. To create the [`.env`](./file-formats.md#env) file,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.example .env.secret
   ```

2. To open the `.env` file in `nano`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   nano .env.secret
   ```

3. Write an arbitrary value for `QWEN_CODE_API_KEY`.

   This key will protect your `Qwen Code` API.

4. Save the file (`Ctrl + O`).

### Start the `Qwen Code` API (REMOTE)

1. To start the `Qwen Code` API via [`Docker Compose`](./docker-compose.md#what-is-docker-compose),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.secret up --build -d
   ```

   > <h3>Troubleshooting</h3>
   >
   > [`Bind for <host>:<port> failed: port is already allocated`](./docker.md#bind-for-hostport-failed-port-is-already-allocated)

### Check that the `Qwen Code` API is accessible

1. To send an [`HTTP` request](./http.md#http-request) to the [`Qwen Code` API](#what-is-qwen-code-api),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   curl -s <qwen-code-api-base-url>/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <qwen-code-api-key>" \
     -d '{"model":"<qwen-model>","messages":[{"role":"user","content":"What is 2+2?"}]}' \
     | jq .
   ```

   Replace the placeholders:

   - [`<qwen-code-api-base-url>`](#qwen-code-api-base-url-placeholder)
   - `<qwen-code-api-key>` with the value of [`QWEN_CODE_API_KEY`](./qwen-code-api-dotenv-secret.md#qwen_code_api_key) from [`qwen-code-api/.env.secret` (REMOTE)](./qwen-code-api-dotenv-secret.md#about-qwen-code-apienvsecret)
   - `<qwen-model>` with one of the [available models](./qwen-code.md#view-available-models)

2. When you run it, the output should be similar to this:

   ```terminal
   {
      "created": 1773379590,
      "usage": {
         "completion_tokens": 8,
         "prompt_tokens": 15,
         "prompt_tokens_details": {
            "cached_tokens": 0
         },
         "total_tokens": 23
      },
      "model": "coder-model",
      "id": "chatcmpl-9c04fd89-7d16-469f-af7b-8e64a9418bb3",
      "choices": [
         {
            "finish_reason": "stop",
            "index": 0,
            "message": {
            "role": "assistant",
            "content": "2 + 2 = 4."
            }
         }
      ],
      "object": "chat.completion"
   }
   ```
