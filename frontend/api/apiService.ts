import axiosInstance from '@/api'; // Your existing axios file
import { AggregateData, NewsItem, StockPrice, TickerInfo } from '@/api/types';
import { aggregateResponse, NewsApiResponse, PriceRangeResponse } from './resposne';

export const SentimentDeltaAPI = {
  // --- Health ---
  getHealth: () => axiosInstance.get('/health').then(res => res.data),

  // --- Stock Prices ---
  getTickers: () => axiosInstance.get<TickerInfo[]>('/stock_prices/tickers').then(res => res.data),

  getLatestPrice: (ticker: string) => axiosInstance.get<StockPrice>(`/stock_prices/${ticker}/latest`).then(res => res.data),

  getPriceRange: (ticker: string, start: string, end: string) => axiosInstance.get<PriceRangeResponse>(`/stock_prices/${ticker}`, { params: { start, end } }).then(res => res.data),

  // --- News ---
  getNewsList: (limit = 100) => axiosInstance.get<NewsItem[]>('/news/list', { params: { limit } }).then(res => res.data),

  getNewsSummary: () => axiosInstance.get('/news/summary').then(res => res.data),

  getNewsByTicker: (ticker: string, limit = 10) => axiosInstance.get<NewsItem[]>(`/news/ticker/${ticker}/list`, { params: { limit } }).then(res => res.data),

  getNewsByTickerAndPagination : (ticker: string, page: number, limit: number, search: string) => axiosInstance.get<NewsApiResponse>(`/news/ticker/${ticker}/paginated`, { params: { page, limit, search } }).then(res => res.data),

  getNewsByTickerAndDate: (ticker: string, date: string) => axiosInstance.get(`/news/ticker/${ticker}/date/${date}`).then(res => res.data),

  getNewsRange: (ticker: string, start: string, end: string) => axiosInstance.get(`/news/ticker/${ticker}/range`, { params: { start, end } }).then(res => res.data),

  // --- Aggregates ---
  getAggregateDates: (ticker: string) => axiosInstance.get(`/aggregates/dates`, { params: { ticker } }).then(res => res.data),

  getAggregates: (limit = 10) => axiosInstance.get<AggregateData[]>('/aggregates', { params: { limit } }).then(res => res.data),

  getAggregatesByTicker: (ticker: string) =>
    axiosInstance
      .get<aggregateResponse>(
        `/aggregates/ticker/${ticker}`
      )
      .then((res) => res.data),

  getAggregateRange: (ticker: string, start: string, end: string) => axiosInstance.get(`/aggregates/ticker/${ticker}`, { params: { start, end } }).then(res => res.data),

  getAggregateByDate: (ticker: string, date: string) => axiosInstance.get(`/aggregates/ticker/${ticker}`, { params: { date } }).then(res => res.data),

  getLatestAggregate: (ticker: string) => axiosInstance.get<AggregateData>(`/aggregates/ticker/${ticker}/latest`).then(res => res.data),
};