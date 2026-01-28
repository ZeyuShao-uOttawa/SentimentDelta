export interface AggregateData {
  _id: string ;
  sent_mean: number;
  sent_std: number;
  attention: number;
  bull_bear_ratio: number;
  date: string;
  ticker: string;
}

export interface NewsItem {
  _id: { $oid: string };
  ticker: string;
  source: string;
  title: string;
  url: string;
  date: string;
  body: string;
  sentiment: {
    score: number;
    positive: number;
    neutral: number;
    negative: number;
  };
  ingested_at: { $date: string };
}

export interface StockPrice {
  _id: string;
  Ticker: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  Datetime: { $date: string };
}

export interface TickerInfo {
    Ticker: string;
    start: string;
    end: string;
}