import React from "react";
import Sidebar from "@/components/sidebar";
import DashboardHeader from "@/components/dashboard-header";

export const metadata = {
  title: "Dashboard",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <DashboardHeader />
            <div>{children}</div>
          </div>
        </main>
      </div>
    </div>
  );
}
