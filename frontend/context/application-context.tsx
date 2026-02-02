"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { SentimentDeltaAPI } from "@/api/apiService";
import { AggregateData, NewsItem, StockPrice, TickerInfo } from "@/api/types";
import {
  aggregateResponse,
  NewsApiResponse,
  PriceRangeResponse,
  PriceRangeWithMeta,
} from "@/api/resposne";

type ApplicationContextType = {
  tickers: TickerInfo[];
  latestPrices: Record<string, StockPrice>;
  news: Record<string, NewsItem[]>;
  aggregates: Record<string, AggregateData[]>;
  currentTicker?: string | null;
  setCurrentTicker: React.Dispatch<React.SetStateAction<string | null>>;
  fetchTickers: () => Promise<void>;
  fetchLatestPrices: (ticker: string) => Promise<void>;
  fetchAggregatesByTicker: () => Promise<aggregateResponse | undefined>;
  fetchNewsByTickerAndPagination: (
    page: number,
    limit: number,
    search: string,
  ) => Promise<NewsApiResponse | undefined>;
  fetchStockPriceWithDateRange: (
    ticker: string,
    start: string,
    end: string,
  ) => Promise<PriceRangeWithMeta | undefined>;
};

const ApplicationContext = createContext<ApplicationContextType | undefined>(
  undefined,
);

export const ApplicationProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [currentTicker, setCurrentTicker] = useState<string | null>(null);
  const [tickers, setTickers] = useState<TickerInfo[]>([]);
  const [latestPrices, setLatestPrices] = useState<Record<string, StockPrice>>(
    {},
  );
  const [news, setNews] = useState<Record<string, NewsItem[]>>({});
  const [aggregates, setAggregates] = useState<Record<string, AggregateData[]>>(
    {},
  );

  const fetchTickers = async () => {
    try {
      if (tickers.length > 0) return;
      const data = await SentimentDeltaAPI.getTickers();
      setTickers(data);
    } catch (error) {
      console.error("Failed to fetch tickers", error);
    }
  };

  const fetchLatestPrices = async (ticker: string) => {
    try {
      const prices: Record<string, StockPrice> = {};
      if (prices[ticker] === undefined) {
        prices[ticker] = await SentimentDeltaAPI.getLatestPrice(ticker);
        setLatestPrices((prevPrices) => ({ ...prevPrices, ...prices }));
      }
    } catch (error) {
      console.error("Failed to fetch latest prices", error);
    }
  };

  const fetchStockPriceWithDateRange = async (
    ticker: string,
    start: string,
    end: string,
  ) => {
    try {
      const data = await SentimentDeltaAPI.getPriceRange(ticker, start, end);

      const tickerMeta = tickers.find((t) => t.Ticker === ticker);

      const enrichedData: PriceRangeWithMeta = {
        ...data,
        start: tickerMeta?.start ?? start,
        end: tickerMeta?.end ?? end,
      };

      return enrichedData;
    } catch (error) {
      console.error("Failed to fetch stock prices with date range", error);
    }
  };

  const fetchNewsByTickerAndPagination = async (
    page: number,
    limit: number,
    search: string,
  ) => {
    try {
      if (currentTicker) {
        const data = await SentimentDeltaAPI.getNewsByTickerAndPagination(
          currentTicker,
          page,
          limit,
          search,
        );
        return data;
      }
    } catch (error) {
      console.error("Failed to fetch news", error);
    }
  };

  const fetchAggregatesByTicker = async () => {
    try {
      if (currentTicker) {
        const data =
          await SentimentDeltaAPI.getAggregatesByTicker(currentTicker);
        return data;
      }
    } catch (error) {
      console.error("Failed to fetch aggregates", error);
    }
  };

  useEffect(() => {
    const initializeTicker = async () => {
      await fetchTickers();
      if (tickers.length > 0 && !currentTicker) {
        setCurrentTicker(tickers[0].Ticker);
      }
    };
    initializeTicker();
  }, [fetchTickers]);

  return (
    <ApplicationContext.Provider
      value={{
        tickers,
        latestPrices,
        news,
        aggregates,
        fetchTickers,
        fetchLatestPrices,
        fetchNewsByTickerAndPagination,
        fetchStockPriceWithDateRange,
        fetchAggregatesByTicker,
        currentTicker,
        setCurrentTicker,
      }}
    >
      {children}
    </ApplicationContext.Provider>
  );
};

export const useApplicationContext = () => {
  const context = useContext(ApplicationContext);
  if (!context) {
    throw new Error(
      "useApplicationContext must be used within an ApplicationProvider",
    );
  }
  return context;
};
