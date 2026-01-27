**SentimentDelta**

- **Purpose:** Aggregates news sentiment and stock-price data to support analytics and monitoring.
- **Language:** Python

**Overview**

- **Contents:** Backend service with scrapers, DB access, routes, and utility scripts. See [backend](backend/).
- **Main app:** [backend/app.py](backend/app.py)

**Quick Start**

- **Install deps:** `pip install -r backend/requirements.txt`
- **Environment:** Configure required environment variables as shown in [backend/config/config.py](backend/config/config.py).
- **Run (development):** `python backend/app.py`

**Development**

- **Run scripts:** See [backend/scripts](backend/scripts/) for aggregation and migration helpers.
- **Routes:** See [backend/routes](backend/routes/) for API endpoints.

**Files**

- **Routes:** [backend/routes](backend/routes/)
- **DB helpers:** [backend/db](backend/db/)
- **Scrapers:** [backend/scrapers](backend/scrapers/)

**Notes**

- **No license specified:** Add a `LICENSE` file if you intend to publish under an open-source license.
