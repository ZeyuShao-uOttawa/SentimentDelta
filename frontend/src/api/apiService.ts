import axiosInstance from '@/api';
import { AggregateData, NewsItem, StockPrice, TickerInfo } from '@/api/types';
import { aggregateResponse, NewsApiResponse, PriceRangeResponse } from './responses';

// --- Health ---
export const getHealth = () => axiosInstance.get('/health').then(res => res.data);

// --- Stock Prices ---
export const getTickers = () => axiosInstance.get<TickerInfo[]>('/stock_prices/tickers').then(res => res.data);

export const getLatestPrice = (ticker: string) => axiosInstance.get<StockPrice>(`/stock_prices/${ticker}/latest`).then(res => res.data);

export const getPriceRange = (ticker: string, start: string, end: string) => axiosInstance.get<PriceRangeResponse>(`/stock_prices/${ticker}`, { params: { start, end } }).then(res => res.data);

// --- News ---
export const getNewsList = (limit = 100) => axiosInstance.get<NewsItem[]>('/news/list', { params: { limit } }).then(res => res.data);

export const getNewsSummary = () => axiosInstance.get('/news/summary').then(res => res.data);

export const getNewsByTicker = (ticker: string, limit = 10) => axiosInstance.get<NewsItem[]>(`/news/ticker/${ticker}/list`, { params: { limit } }).then(res => res.data);

export const getNewsByTickerAndPagination = (ticker: string, page: number, limit: number, search: string) => axiosInstance.get<NewsApiResponse>(`/news/ticker/${ticker}/paginated`, { params: { page, limit, search } }).then(res => res.data);

export const getNewsByTickerAndDate = (ticker: string, date: string) => axiosInstance.get(`/news/ticker/${ticker}/date/${date}`).then(res => res.data);

export const getNewsRange = (ticker: string, start: string, end: string) => axiosInstance.get(`/news/ticker/${ticker}/range`, { params: { start, end } }).then(res => res.data);

// --- Aggregates ---
export const getAggregateDates = (ticker: string) => axiosInstance.get(`/aggregates/dates`, { params: { ticker } }).then(res => res.data);

export const getAggregates = (limit = 10) => axiosInstance.get<AggregateData[]>('/aggregates', { params: { limit } }).then(res => res.data);

export const getAggregatesByTicker = (ticker: string) =>
  axiosInstance
    .get<aggregateResponse>(
      `/aggregates/ticker/${ticker}`
    )
    .then((res) => res.data);

export const getAggregateRange = (ticker: string, start: string, end: string) => axiosInstance.get(`/aggregates/ticker/${ticker}`, { params: { start, end } }).then(res => res.data);

export const getAggregateByDate = (ticker: string, date: string) => axiosInstance.get(`/aggregates/ticker/${ticker}`, { params: { date } }).then(res => res.data);

export const getLatestAggregate = (ticker: string) => axiosInstance.get<AggregateData>(`/aggregates/ticker/${ticker}/latest`).then(res => res.data);

// Deprecated: Use individual exports instead
export const SentimentDeltaAPI = {
  getHealth,
  getTickers,
  getLatestPrice,
  getPriceRange,
  getNewsList,
  getNewsSummary,
  getNewsByTicker,
  getNewsByTickerAndPagination,
  getNewsByTickerAndDate,
  getNewsRange,
  getAggregateDates,
  getAggregates,
  getAggregatesByTicker,
  getAggregateRange,
  getAggregateByDate,
  getLatestAggregate,
};
