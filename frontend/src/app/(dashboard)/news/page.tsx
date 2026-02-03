"use client";

import React, { useEffect, useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { useApplicationContext } from "@/context/application-context";
import type { NewsItem } from "@/api/types";
import { DataTable } from "@/components/ui/data-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Icon } from "@/components/icons";
import type { Pagination } from "@/api/responses";

export default function NewsPage() {
  const { currentTicker, fetchNewsByTickerAndPagination } =
    useApplicationContext();

  const [news, setNews] = useState<NewsItem[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(false);

  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  // --- Debounce search ---
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setCurrentPage(1);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchInput]);

  // --- Fetch news ---
  useEffect(() => {
    if (!currentTicker) return;

    const loadNews = async () => {
      setLoading(true);
      try {
        const res = await fetchNewsByTickerAndPagination(
          currentPage,
          pageSize,
          debouncedSearch,
        );

        setNews(res?.data ?? []);
        setPagination(res?.pagination ?? null);
      } catch (err) {
        console.error("Failed to load news", err);
        setNews([]);
        setPagination(null);
      } finally {
        setLoading(false);
      }
    };

    loadNews();
  }, [
    currentTicker,
    currentPage,
    pageSize,
    debouncedSearch,
    fetchNewsByTickerAndPagination,
  ]);

  // Reset pagination on ticker change
  useEffect(() => {
    setCurrentPage(1);
  }, [currentTicker]);

  // --- Table columns ---
  const columns = useMemo<ColumnDef<NewsItem>[]>(
    () => [
      {
        accessorKey: "date",
        header: "Date",
        cell: ({ getValue }) => (
          <div className="text-xs text-muted-foreground whitespace-nowrap px-2">
            {new Intl.DateTimeFormat("en-US", {
              month: "short",
              day: "numeric",
            }).format(new Date(getValue() as string))}
          </div>
        ),
      },
      {
        accessorKey: "title",
        header: "Headline",
        cell: ({ row }) => (
          <div className="flex flex-col max-w-112.5 space-y-1 py-1 px-2">
            <span className="font-medium leading-snug line-clamp-2">
              {row.original.title}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">
              {row.original.source}
            </span>
          </div>
        ),
      },
      {
        id: "sentiment",
        header: "Sentiment",
        accessorFn: (row) => row.sentiment?.score ?? 0,
        cell: ({ getValue }) => {
          const score = getValue<number>();

          return (
            <div className="px-2">
              {score > 0.1 ? (
                <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-200 shadow-none">
                  <Icon
                    iconName="arrow-right-up-line"
                    iconSize="xs"
                    className="mr-1 h-3 w-3"
                  />
                  Positive
                </Badge>
              ) : score < -0.1 ? (
                <Badge className="bg-rose-500/10 text-rose-600 border-rose-200 shadow-none">
                  <Icon
                    iconName="arrow-right-down-line"
                    iconSize="xs"
                    className="mr-1 h-3 w-3"
                  />
                  Negative
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="text-muted-foreground italic"
                >
                  Neutral
                </Badge>
              )}
            </div>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-right px-4">View</div>,
        cell: ({ row }) => {
          const item = row.original;

          return (
            <div className="text-right px-2">
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Icon iconName="eye-line" iconSize="sm" />
                  </Button>
                </DialogTrigger>

                <DialogContent className="sm:max-w-150 max-h-[85vh] flex flex-col">
                  <DialogHeader>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">{item.ticker}</Badge>
                      <span className="text-xs text-muted-foreground italic">
                        {item.source}
                      </span>
                    </div>
                    <DialogTitle>{item.title}</DialogTitle>
                  </DialogHeader>

                  <div className="flex-1 overflow-y-auto py-4 text-sm whitespace-pre-wrap">
                    {item.body || "Detailed summary is unavailable."}
                  </div>

                  <DialogFooter className="flex flex-col sm:flex-row items-center sm:justify-between gap-4 pt-2">
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center"
                    >
                      View Original Source
                      <Icon
                        iconName="external-link-line"
                        iconSize="xs"
                        className="ml-1"
                      />
                    </a>
                    <DialogClose asChild>
                      <Button variant="secondary" size="sm">
                        Close
                      </Button>
                    </DialogClose>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          );
        },
      },
    ],
    [],
  );

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>
            Latest Headlines{currentTicker && ` — ${currentTicker}`}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {loading && (
            <div className="text-sm text-muted-foreground">Loading news…</div>
          )}

          {!loading && news.length === 0 && (
            <div className="text-sm text-muted-foreground">
              No articles found
            </div>
          )}

          <DataTable
            columns={columns}
            data={news}
            filterValue={searchInput}
            onFilterChange={setSearchInput}
            hidePagination
          />

          <div className="flex justify-between items-center text-sm text-muted-foreground">
            <div>Total Articles: {pagination?.total_count ?? 0}</div>

            <div className="flex gap-2 items-center">
              <Button
                size="sm"
                variant="outline"
                disabled={!pagination?.has_previous}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>

              <span>
                Page {pagination?.page ?? currentPage} of{" "}
                {pagination?.total_pages ?? "?"}
              </span>

              <Button
                size="sm"
                variant="outline"
                disabled={!pagination?.has_next}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
