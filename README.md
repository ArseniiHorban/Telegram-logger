# Telegram-logger
A simple application I developed to learn about telethon

## Features
- Logs your online/offline status
- Logs incoming and outgoing messages
- Saves logs to separate files:
  - `log_raw.txt` — all events
  - `log_online.txt` — only online/offline status changes
  - `log_messages.txt` — only messages
- Tracks daily statistics in `stats.json`:
  - Total online time per day
  - Number of sent messages
  - Number of incoming messages
  
## Installation
1. **Clone the repository:**
   ```
   git clone https://github.com/ArseniiHorban/Telegram-logger.git
   cd telegram-logger
   ```

2. **Install dependencies:**
   ```
   pip install telethon python-dotenv
   ```
   Or use `pip install -r requirements.txt`.

3. **Create a `.env` file** in the project directory with your Telegram API credentials:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   ```
## Usage

- **Start logging:**
  ```
  python telegram_logger.py
  ```

- **Show statistics:**
  ```
  python telegram_logger.py stats
  ```

## Notes

- On first run, you will need to authorize via Telegram (a code will be sent to your account).
- All logs and statistics are saved in the same directory as the script.
- Requires Python 3.7 or higher.
 
