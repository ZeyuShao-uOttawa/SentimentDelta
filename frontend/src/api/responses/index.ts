import { AggregateData, NewsItem, StockPrice } from "../types";

export interface Pagination {
  has_next: boolean;
  has_previous: boolean;
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
}

export interface NewsApiResponse {
  data: NewsItem[];
  pagination: Pagination;
  ticker: string;
}

export type aggregateResponse = { count: number; data: AggregateData[]; ticker: string }

export interface PriceRangeResponse {
  count: number;
  data: StockPrice[]; 
}

export type PriceRangeWithMeta = PriceRangeResponse & {
  start: string;
  end: string;
};