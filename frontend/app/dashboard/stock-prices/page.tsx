import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function StockPricesPage() {
  return (
    <div>
      <div className="grid grid-cols-1 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Market Snapshot</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Stock prices and charts will appear here.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
