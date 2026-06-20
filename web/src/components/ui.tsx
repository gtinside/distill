import Link from "next/link";
import type { ComponentProps, ReactNode, SVGProps } from "react";

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

// Shared keyboard-focus ring — applied to every interactive primitive.
const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const buttonStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-accent-fg hover:brightness-110 shadow-[0_1px_0_rgba(255,255,255,0.15)_inset]",
  secondary:
    "bg-surface-2 border border-border text-foreground hover:border-border-strong hover:bg-surface",
  ghost: "text-muted hover:text-foreground hover:bg-surface-2",
  danger: "text-danger hover:bg-danger-soft",
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: ButtonVariant }) {
  return (
    <button
      className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-[transform,background-color,border-color,filter,color] duration-150 active:scale-[0.97] disabled:pointer-events-none disabled:opacity-40 ${focusRing} ${buttonStyles[variant]} ${className}`}
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
      className={`rounded-2xl border border-border bg-surface bg-[image:var(--card-grad)] p-5 shadow-[var(--shadow-card)] ${className}`}
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

// ---------------------------------------------------------------- Form inputs

export function Field({
  label,
  htmlFor,
  hint,
  children,
  className = "",
}: {
  label: string;
  htmlFor: string;
  hint?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <label
        htmlFor={htmlFor}
        className="mb-1.5 block text-[13px] font-medium text-foreground"
      >
        {label}
      </label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function Input({ className = "", ...props }: ComponentProps<"input">) {
  return (
    <input
      className={`w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground transition-colors duration-150 outline-none placeholder:text-faint hover:border-border-strong focus:border-accent focus:ring-4 focus:ring-accent-soft disabled:opacity-50 ${className}`}
      {...props}
    />
  );
}

// Pill chip — topics, tags, source links.
export function Chip({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1 text-xs text-muted ${className}`}
    >
      {children}
    </span>
  );
}

export function NavBar({ active }: { active: "home" | "topics" }) {
  const tab = (href: string, key: string, label: string) => {
    const isActive = active === key;
    return (
      <Link
        href={href}
        aria-current={isActive ? "page" : undefined}
        className={`relative rounded-sm py-1 font-mono text-xs uppercase tracking-[0.14em] transition-colors ${focusRing} ${
          isActive ? "text-accent" : "text-faint hover:text-foreground"
        }`}
      >
        {label}
        {isActive && (
          <span className="absolute -bottom-[14px] left-0 right-0 h-px bg-accent" />
        )}
      </Link>
    );
  };
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3.5">
        <Link href="/" className={`rounded-md ${focusRing}`}>
          <Logo />
        </Link>
        <nav className="flex items-center gap-6">
          {tab("/", "home", "Today")}
          {tab("/topics", "topics", "Topics")}
        </nav>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------- Icons (SVG)
// Inline 1.6px-stroke icons (Lucide-style) — replace emoji used as structural
// icons, so they scale crisply and inherit currentColor for theming.

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Svg({ size = 16, children, ...props }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function IconClose(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M18 6 6 18M6 6l12 12" />
    </Svg>
  );
}

export function IconPlus(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M12 5v14M5 12h14" />
    </Svg>
  );
}

export function IconCheck(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M20 6 9 17l-5-5" />
    </Svg>
  );
}

export function IconRefresh(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6" />
    </Svg>
  );
}

export function IconDrag(p: IconProps) {
  return (
    <Svg {...p}>
      <circle cx="9" cy="6" r="1" />
      <circle cx="9" cy="12" r="1" />
      <circle cx="9" cy="18" r="1" />
      <circle cx="15" cy="6" r="1" />
      <circle cx="15" cy="12" r="1" />
      <circle cx="15" cy="18" r="1" />
    </Svg>
  );
}

export function IconArrowUpRight(p: IconProps) {
  return (
    <Svg {...p}>
      <path d="M7 17 17 7M8 7h9v9" />
    </Svg>
  );
}
