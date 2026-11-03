import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, ArrowRight, Check, LoaderCircle } from "lucide-react";
import { cn } from "../../lib/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "quiet" | "danger";
  icon?: ReactNode;
  to?: string;
};

export function Button({ className, variant = "primary", icon, children, to, ...props }: ButtonProps) {
  const classes = cn("button", `button-${variant}`, className);
  if (to) return <Link className={classes} to={to}>{children}{icon}</Link>;
  return <button className={classes} {...props}>{children}{icon}</button>;
}

export function Eyebrow({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "muted" | "mint" | "amber" }) {
  return <span className={cn("eyebrow", tone !== "default" && `eyebrow-${tone}`)}>{children}</span>;
}

export function SectionHeading({ eyebrow, title, copy, action }: { eyebrow?: ReactNode; title: string; copy?: string; action?: ReactNode }) {
  return <div className="section-heading-v2"><div>{eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}<h2>{title}</h2>{copy && <p>{copy}</p>}</div>{action && <div className="section-action">{action}</div>}</div>;
}

export function PageHeader({ eyebrow, title, copy, action }: { eyebrow: ReactNode; title: string; copy: string; action?: ReactNode }) {
  return <header className="page-header-v2"><div><Eyebrow>{eyebrow}</Eyebrow><h1>{title}</h1><p>{copy}</p></div>{action && <div className="page-header-action-v2">{action}</div>}</header>;
}

export function Panel({ children, className, as: Component = "section" }: { children: ReactNode; className?: string; as?: "section" | "div" | "aside" }) {
  return <Component className={cn("panel-v2", className)}>{children}</Component>;
}

export function StatusBadge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "mint" | "amber" | "plum" | "coral" }) {
  return <span className={cn("status-badge", `status-${tone}`)}>{children}</span>;
}

export function ProgressLine({ value, tone = "plum", label }: { value: number; tone?: "plum" | "mint" | "amber" | "coral"; label?: string }) {
  return <div className="progress-line-wrap"><div className="progress-line" aria-label={label} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value * 100)}><span className={`progress-${tone}`} style={{ width: `${Math.max(0, Math.min(100, Math.round(value * 100)))}%` }} /></div>{label && <span className="progress-label">{label}</span>}</div>;
}

export function LoadingState({ label = "Loading your learning workspace" }: { label?: string }) {
  return <div className="state-card-v2"><LoaderCircle className="spin" size={21} /><span>{label}…</span></div>;
}

export function ErrorState({ message = "Check that the local Django server is running.", retry }: { message?: string; retry?: () => void }) {
  return <div className="state-card-v2 state-error"><AlertCircle size={22} /><div><strong>We couldn’t load this view.</strong><p>{message}</p>{retry && <Button variant="secondary" onClick={retry} icon={<ArrowRight size={15} />}>Try again</Button>}</div></div>;
}

export function EmptyState({ title, copy, action }: { title: string; copy: string; action?: ReactNode }) {
  return <div className="empty-state-v2"><div className="empty-mark"><Check size={16} /></div><strong>{title}</strong><p>{copy}</p>{action}</div>;
}

export function MetricTile({ label, value, detail, tone = "plum" }: { label: string; value: string | number; detail: string; tone?: "plum" | "mint" | "amber" | "coral" }) {
  return <div className={cn("metric-tile", `metric-${tone}`)}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}
