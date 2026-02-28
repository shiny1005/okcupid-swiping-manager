"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Overview", href: "/" },
  { label: "Accounts", href: "/accounts" },
  { label: "Jobs & Queue", href: "/jobs" },
  { label: "Logs", href: "/logs" },
  { label: "Settings", href: "/settings" },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 flex-col border-r border-zinc-200 bg-white/80 px-4 py-4 text-sm dark:border-zinc-800 dark:bg-zinc-950/60 md:flex">
      <div className="mb-6 flex items-center gap-2 px-6 py-4">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-xl bg-zinc-900 text-xs font-semibold text-zinc-50 dark:bg-zinc-50 dark:text-zinc-900">
          OKC
        </span>
        <div>
          <p className="text-xs font-semibold tracking-tight">
            Automation Panel
          </p>
          <p className="text-[11px] text-zinc-500">Multi-account control</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href ||
                pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex w-full items-center justify-between rounded-xl px-2.5 py-1.5 text-left text-[13px] transition ${
                active
                  ? "bg-zinc-900 text-zinc-50 shadow-sm dark:bg-zinc-50 dark:text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:hover:text-zinc-50"
              }`}
            >
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="mt-6 border-t border-zinc-200 pt-4 text-[11px] text-zinc-500 dark:border-zinc-800">
        <p>Okcupid Automation Panel</p>
      </div>
    </aside>
  );
}
