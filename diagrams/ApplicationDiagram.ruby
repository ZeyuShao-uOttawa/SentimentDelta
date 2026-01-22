flowchart TB
    Start(["App Start"]) --> InitSubgraph
    subgraph InitSubgraph["Initialization"]
        Init["App Initialization"]
        Config["Load Config"]
        DB["Connect to MongoDB"]:::db
        Embeddings["Setup Embeddings"]
        Managers["Initialize Managers"]
        Scheduler["Start Scheduler"]
    end
    InitSubgraph --> SchedulerSubgraph

    subgraph SchedulerSubgraph["Scheduler Jobs"]
        StockJob["Stock Price Job"]:::job
        YahooJob["Yahoo News Job"]:::job
        FinvizJob["Finviz News Job"]:::job
        AggJob["Aggregate Job"]:::job
    end

    StockJob --> StockFetch["Fetch Stock Prices"]
    StockFetch --> StockStore["Store Stock Prices"]:::store

    YahooJob --> NewsFetch["Fetch News Articles"]
    FinvizJob --> NewsFetch
    NewsFetch --> NewsProcess["Process Articles<br>(Sentiment + Embeddings)"]
    NewsProcess --> NewsStore["Store News"]:::store

    AggJob --> AggCalc["Calculate Aggregates"]
    AggCalc --> AggStore["Store Aggregates"]:::store

    Maintenance["Migration / Update Scripts"]:::maintenance --> NewsStore

    classDef init fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px
    classDef job fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef fetch fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px
    classDef store fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    classDef maintenance fill:#ECEFF1,stroke:#455A64,stroke-width:2px
    classDef db fill:#FFEBEE,stroke:#C62828,stroke-width:2px