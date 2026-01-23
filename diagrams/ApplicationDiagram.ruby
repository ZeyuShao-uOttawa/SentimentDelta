---
config:
  flowchart:
    curve: linear
  layout: dagre
---
flowchart TB
 subgraph InitSubgraph["Initialization"]
        Init["App Initialization"]
        Config["Load Config"]
        DB["Connect to MongoDB"]
        Embeddings["Setup Embeddings"]
        Managers["Initialize DB Managers"]
        Scheduler["Start Scheduler"]
  end
 subgraph SchedulerSubgraph["Scheduler Jobs"]
        StockJob["Stock Price Job"]
        YahooJob["Yahoo News Job"]
        FinvizJob["Finviz News Job"]
        AggJob["Aggregate Job"]
  end
    Start(["App Start"]) --> InitSubgraph
    StockJob --> StockFetch["Fetch Stock Prices"]
    StockFetch --> StockStore["Store Stock Prices"]
    YahooJob --> NewsFetch["Fetch News Articles"]
    FinvizJob --> NewsFetch
    NewsFetch --> NewsProcess["Process Articles<br>(Sentiment + Embeddings)"]
    NewsProcess --> NewsStore["Store News"]
    AggJob --> AggCalc["Calculate Aggregates"]
    AggCalc --> AggStore["Store Aggregates"]
    Maintenance["Migration / Update Scripts"] --> NewsStore
    Scheduler --> SchedulerSubgraph

     DB:::db
     StockJob:::job
     YahooJob:::job
     FinvizJob:::job
     AggJob:::job
     StockStore:::store
     NewsStore:::store
     AggStore:::store
     Maintenance:::maintenance
    classDef init fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px
    classDef job fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef fetch fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px
    classDef store fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    classDef maintenance fill:#ECEFF1,stroke:#455A64,stroke-width:2px
    classDef db fill:#FFEBEE,stroke:#C62828,stroke-width:2px