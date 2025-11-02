# GMod Stat Tracker

This project scrapes, processes, and visualizes player data for a GMod server.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Add Credentials:**
    * Place your `google_sheets_service_account.json` file in this main directory.
    * Create a `.env` file by copying `.env.example`.
    * Fill in your `BATTLEMETRICS_USERNAME`, `BATTLEMETRICS_PASSWORD`, and `STEAM_API_KEY` in the `.env` file.

## How to Run

Execute the main script from this directory:

```bash
python main.py