import { useEffect, useState, type ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { BookOpen, BrainCircuit, CalendarDays, Command, FlaskConical, GraduationCap, LayoutDashboard, LogOut, Menu, Network, RefreshCcw, Search, Settings, Target, Users, X } from "lucide-react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import type { Role, User } from "../lib/api";
import { logoutDemo } from "../lib/api";
import { SearchCommand } from "../features/search/SearchCommand";
import { NotificationCenter } from "../features/notifications/NotificationCenter";

type NavItem = { label: string; path: string; icon: typeof LayoutDashboard };
const nav: Record<Role, NavItem[]> = {
  STUDENT: [
    { label: "Home", path: "/student/dashboard", icon: LayoutDashboard },
    { label: "My path", path: "/student/my-path", icon: Network },
    { label: "Learn", path: "/student/learn", icon: BookOpen },
    { label: "Practice", path: "/student/practice", icon: Target },
    { label: "Knowledge map", path: "/student/my-knowledge", icon: BrainCircuit },
    { label: "Progress", path: "/student/progress", icon: CalendarDays },
  ],
  TEACHER: [
    { label: "Home", path: "/teacher/dashboard", icon: LayoutDashboard },
    { label: "Classes", path: "/teacher/classes", icon: Users },
    { label: "Concept insights", path: "/teacher/concept-insights", icon: BrainCircuit },
    { label: "Interventions", path: "/teacher/interventions", icon: RefreshCcw },
  ],
  COORDINATOR: [{ label: "Home", path: "/coordinator/dashboard", icon: LayoutDashboard }, { label: "Content map", path: "/coordinator/content", icon: BookOpen }],
  GUARDIAN: [{ label: "Home", path: "/guardian/dashboard", icon: LayoutDashboard }],
};

export function homeFor(role: Role) { if (role === "TEACHER") return "/teacher/dashboard"; if (role === "COORDINATOR") return "/coordinator/dashboard"; if (role === "GUARDIAN") return "/guardian/dashboard"; return "/student/dashboard"; }

export function AppShell({ user, children }: { user: User; children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const client = useQueryClient();
  const logout = useMutation({ mutationFn: logoutDemo, onSuccess: () => { client.clear(); navigate("/"); } });
  useEffect(() => { const handler = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setSearchOpen(true); } }; window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler); }, []);
  const items = nav[user.role];
  return <div className="app-frame">
    <aside className={`side-rail ${mobileOpen ? "open" : ""}`}>
      <div><Link to={homeFor(user.role)} className="brand"><span className="brand-mark" /><span>pathloom</span></Link><button className="mobile-menu rail-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={17} /></button></div>
      <div className="rail-context"><span className="avatar">{user.avatar_initials}</span><div><small>{user.role === "STUDENT" ? "Learner space" : `${user.role[0]}${user.role.slice(1).toLowerCase()} space`}</small><strong>{user.display_name}</strong></div></div>
      <nav className="primary-nav" aria-label="Primary navigation"><span className="nav-group-label">Workspace</span>{items.map((item) => <NavLink to={item.path} key={item.path} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}><item.icon size={17} /><span>{item.label}</span></NavLink>)}</nav>
      <div className="rail-bottom"><div className="connection-chip"><span className="live-dot" /><div><strong>Local demo connected</strong><small>Django · fictional records</small></div></div>{user.role === "STUDENT" && <NavLink to="/student/lab/concept-surgery/MATH-ALG-07" className="nav-item" onClick={() => setMobileOpen(false)}><FlaskConical size={17} /><span>Investigation lab</span></NavLink>}<NavLink to="/settings" className="nav-item" onClick={() => setMobileOpen(false)}><Settings size={17} /><span>Settings</span></NavLink><button className="nav-item" onClick={() => logout.mutate()}><LogOut size={17} /><span>Switch persona</span></button></div>
    </aside>
    {mobileOpen && <button className="scrim-v2" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
    <div className="workspace"><header className="topbar-v2"><div className="breadcrumbs-v2"><button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={18} /></button><Link to={homeFor(user.role)}>Workspace</Link><span>/</span><strong>{labelForPath(location.pathname)}</strong></div><div className="topbar-tools"><button className="topbar-control" onClick={() => setSearchOpen(true)} aria-label="Search Pathloom"><Search size={15} /><span>Search</span><kbd><Command size={10} /> K</kbd></button><NotificationCenter /><Link className="avatar avatar-sm" to="/settings" aria-label="Open settings">{user.avatar_initials}</Link></div></header><main className="main-canvas">{children}</main></div>
    <SearchCommand open={searchOpen} onClose={() => setSearchOpen(false)} />
  </div>;
}

function labelForPath(path: string) { const value = path.split("/").filter(Boolean).at(-1) ?? "home"; return value.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
