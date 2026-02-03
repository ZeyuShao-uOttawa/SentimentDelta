"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import * as API from "@/api/apiService";
import { AggregateData, NewsItem, StockPrice, TickerInfo } from "@/api/types";
import {
  aggregateResponse,
  NewsApiResponse,
  PriceRangeResponse,
  PriceRangeWithMeta,
} from "@/api/responses";

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

  const fetchTickers = useCallback(async () => {
    try {
      if (tickers.length > 0) return;
      const data = await API.getTickers();
      setTickers(data);
    } catch (error) {
      console.error("Failed to fetch tickers", error);
    }
  }, [tickers.length]);

  const fetchLatestPrices = useCallback(
    async (ticker: string) => {
      try {
        if (latestPrices[ticker] === undefined) {
          const data = await API.getLatestPrice(ticker);
          setLatestPrices((prevPrices) => ({ ...prevPrices, [ticker]: data }));
        }
      } catch (error) {
        console.error("Failed to fetch latest prices", error);
      }
    },
    [latestPrices],
  );

  const fetchStockPriceWithDateRange = useCallback(
    async (ticker: string, start: string, end: string) => {
      try {
        const data = await API.getPriceRange(ticker, start, end);

        const tickerMeta = tickers.find((t) => t.Ticker === ticker);

        const processedData = data.data.map((item: any) => {
          const [date, time] = item.Datetime.split("T");
          return { ...item, date, time };
        });

        const enrichedData: PriceRangeWithMeta = {
          ...data,
          data: processedData,
          start: tickerMeta?.start ?? start,
          end: tickerMeta?.end ?? end,
        };

        return enrichedData;
      } catch (error) {
        console.error("Failed to fetch stock prices with date range", error);
      }
    },
    [tickers],
  );

  const fetchNewsByTickerAndPagination = useCallback(
    async (page: number, limit: number, search: string) => {
      try {
        if (currentTicker) {
          const data = await API.getNewsByTickerAndPagination(
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
    },
    [currentTicker],
  );

  const fetchAggregatesByTicker = useCallback(async () => {
    try {
      if (currentTicker) {
        const data = await API.getAggregatesByTicker(currentTicker);
        return data;
      }
    } catch (error) {
      console.error("Failed to fetch aggregates", error);
    }
  }, [currentTicker]);

  useEffect(() => {
    const initializeTicker = async () => {
      await fetchTickers();
    };
    initializeTicker();
  }, [fetchTickers]);

  useEffect(() => {
    if (tickers.length > 0 && !currentTicker) {
      setCurrentTicker(tickers[0].Ticker);
    }
  }, [tickers, currentTicker]);

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
