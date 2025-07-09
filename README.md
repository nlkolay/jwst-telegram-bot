# JWST Telegram Bot

A Telegram bot that displays James Webb Space Telescope (JWST) telemetry, NASA news, image of the day, and JWST orbital information. It also includes a subscription feature and comprehensive logging.

## Features

*   Configurable telemetry display
*   NASA news feed integration
*   NASA Image of the Day with translation
*   JWST orbital position and trajectory visualization
*   Subscription service for updates
*   Extensive logging

## Setup

1.  **Obtain a Telegram Bot Token:**
    *   Talk to BotFather on Telegram (search for `@BotFather`).
    *   Send `/newbot` and follow the instructions to create a new bot.
    *   BotFather will give you an API token. Copy this token.

2.  **Install Dependencies (Local):**
    *   Navigate to the `jwst-telegram-bot` directory in your terminal.
    *   Run the following command to install the required Python libraries:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Configure Bot Token (Local):**
    *   Open `bot.py` in a text editor.
    *   Find the line `BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"`.
    *   Replace `"YOUR_BOT_TOKEN_HERE"` with the actual token you obtained from BotFather.

## Usage

### Running Locally

1.  **Run the Bot:**
    *   In your terminal, navigate to the `jwst-telegram-bot` directory.
    *   Run the bot using the command:
        ```bash
        python bot.py
        ```
    *   The bot will start running and you should see log messages in your terminal and in `bot.log`.

2.  **Interact with the Bot:**
    *   Open Telegram and search for your bot by its username.
    *   Start a chat with your bot and send the `/start` command.
    *   The bot should respond with a welcome message.

### Running with Docker (Recommended for Deployment)

1.  **Create a `.env` file:**
    *   In the root of the `jwst-telegram-bot` directory, create a file named `.env`.
    *   Add your bot token to this file in the following format:
        ```
        BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
        ```
    *   Replace `YOUR_TELEGRAM_BOT_TOKEN` with the actual token.

2.  **Build and Run the Docker Container:**
    *   Make sure you have Docker and Docker Compose installed.
    *   Navigate to the `jwst-telegram-bot` directory in your terminal.
    *   Run the following command to build and start the container:
        ```bash
        docker-compose up --build -d
        ```
    *   The `-d` flag runs the container in detached mode (in the background).

3.  **Check Logs:**
    *   You can view the container logs using:
        ```bash
        docker-compose logs -f
        ```

4.  **Stop the Container:**
    *   To stop the running container:
        ```bash
        docker-compose down
        ```

## Testing

To run the unit tests:

1.  **Install Test Dependencies:**
    *   Ensure you have `pytest` and `pytest-asyncio` installed (they are included in `requirements.txt`). If you haven't already, run:
        ```bash
        pip install -r requirements.txt
        ```

2.  **Run Tests:**
    *   Navigate to the `jwst-telegram-bot` directory in your terminal.
    *   Run the tests using the command:
        ```bash
        pytest
        ```
    *   You should see output indicating the test results.

## GitHub Repository

To push this project to a GitHub repository:

1.  **Initialize Git (if not already done):**
    ```bash
    git init
    ```

2.  **Add all files to the repository:**
    ```bash
    git add .
    ```

3.  **Commit your changes:**
    ```bash
    git commit -m "Initial commit: JWST Telegram Bot setup"
    ```

4.  **Create a new repository on GitHub:**
    *   Go to [GitHub](https://github.com/).
    *   Click on the "+" sign in the top right corner and select "New repository."
    *   Give your repository a name (e.g., `jwst-telegram-bot`) and choose whether it's public or private.
    *   Do NOT initialize with a README, .gitignore, or license, as you already have these files.

5.  **Link your local repository to the GitHub repository and push:**
    *   Follow the instructions provided by GitHub after creating the repository under the "...or push an existing repository from the command line" section. It will look something like this:
        ```bash
        git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
        git branch -M main
        git push -u origin main
        ```
        (Replace `YOUR_USERNAME` and `YOUR_REPOSITORY_NAME` with your actual GitHub username and repository name.)