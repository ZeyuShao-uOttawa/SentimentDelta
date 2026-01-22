flowchart TD
    %% ===== Styles =====
    classDef core fill:#F5F5F5,stroke:#333;
    classDef job fill:#FFF8E1,stroke:#F9A825;
    classDef process fill:#E8F5E9,stroke:#2E7D32;
    classDef db fill:#F3E5F5,stroke:#6A1B9A;

    %% ===== Core =====
    App([App Start]):::core
    Init["Initialize App<br/>(load config · register routes · init DB · setup embeddings)"]:::core
    Scheduler["Scheduler<br/>(in-app or system cron)"]:::job

    %% ===== Jobs =====
    StockJob["Stock Price Job<br/>(fetch_and_store_stock_prices)"]:::job
    NewsJob["News Jobs<br/>(Yahoo + Finviz)"]:::job
    AggJob["Aggregates Job<br/>(process_missing_aggregates)"]:::job

    %% ===== Stock Flow =====
    StockFetch["Fetch Prices<br/>(Yahoo scraper)"]:::process
    StockProcess["Process Prices<br/>(normalize · dedupe · save)"]:::process

    %% ===== News Flow =====
    NewsFetch["Fetch News<br/>(Yahoo / Finviz scrapers)"]:::process
    NewsBody["Get Article Body<br/>(safe fetch, Multi-threading)"]:::process
    NewsProcess["Process News<br/>(metadata · dedupe · sentiment · embeddings)"]:::process

    %% ===== Aggregates =====
    AggCalc["Calculate Aggregates"]:::process
    AggProcess["Daily Aggregates<br/>(compute & save)"]:::process

    %% ===== Shared =====
    Managers["DB Managers<br/>(stock · news · aggregates)"]:::db
    DB[(MongoDB)]:::db

    %% ===== Flow =====
    App --> Init --> Scheduler

    Scheduler --> StockJob --> StockFetch --> StockProcess --> Managers --> DB
    Scheduler --> NewsJob --> NewsFetch --> NewsBody --> NewsProcess --> Managers
    Scheduler --> AggJob --> AggCalc --> AggProcess --> Managers