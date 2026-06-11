import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <span className="grid h-7 w-7 place-items-center rounded-md bg-accent font-display text-[15px] font-semibold text-accent-fg shadow-[0_0_20px_-2px_var(--accent-soft)]">
        D
      </span>
      <span className="font-display text-[19px] font-medium tracking-tight text-foreground">
        Distill
      </span>
    </span>
  );
}

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const buttonStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-accent-fg hover:brightness-110 shadow-[0_1px_0_rgba(255,255,255,0.15)_inset]",
  secondary:
    "bg-surface-2 border border-border text-foreground hover:border-border-strong",
  ghost: "text-muted hover:text-foreground",
  danger: "text-danger hover:bg-danger-soft",
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: ButtonVariant }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-40 disabled:pointer-events-none ${buttonStyles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(0,0,0,0.4)] ${className}`}
    >
      {children}
    </div>
  );
}

// Small uppercase mono eyebrow label — the "focus/terminal" texture.
export function Eyebrow({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`font-mono text-[11px] uppercase tracking-[0.18em] text-faint ${className}`}
    >
      {children}
    </span>
  );
}

export function NavBar({ active }: { active: "home" | "topics" }) {
  const tab = (href: string, key: string, label: string) => (
    <Link
      href={href}
      className={`font-mono text-xs uppercase tracking-[0.14em] transition ${
        active === key
          ? "text-accent"
          : "text-faint hover:text-foreground"
      }`}
    >
      {label}
    </Link>
  );
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3.5">
        <Link href="/">
          <Logo />
        </Link>
        <nav className="flex items-center gap-5">
          {tab("/", "home", "Today")}
          {tab("/topics", "topics", "Topics")}
        </nav>
      </div>
    </header>
  );
}
