import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BookOpen, BrainCircuit, Search, Users, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { search } from "../../lib/api";

export function SearchCommand({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const results = useQuery({ queryKey: ["search", query], queryFn: () => search(query), enabled: open && query.trim().length > 1, staleTime: 20_000 });

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  useEffect(() => { if (!open) setQuery(""); }, [open]);
  if (!open) return null;
  const go = (path: string) => { onClose(); navigate(path); };
  return <div className="command-overlay" role="dialog" aria-modal="true" aria-label="Search Pathloom" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <div className="command-dialog">
      <div className="command-input"><Search size={19} color="var(--plum)" /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search lessons, concepts, or learners…" /><button className="icon-control" onClick={onClose} aria-label="Close search"><X size={16} /></button></div>
      <div className="command-results">
        {!query.trim() && <div className="command-empty">Search the curriculum you are allowed to see. Try “factor”, “voltage”, or “science”.</div>}
        {results.isLoading && <div className="command-empty">Looking through the local curriculum…</div>}
        {results.data?.courses.length ? <ResultGroup label="Courses">{results.data.courses.map((item) => <ResultButton key={item.id} icon={<BookOpen size={16} />} label={item.title} onClick={() => go(`/student/learn/${item.id}`)} />)}</ResultGroup> : null}
        {results.data?.concepts.length ? <ResultGroup label="Concepts">{results.data.concepts.map((item) => <ResultButton key={item.id} icon={<BrainCircuit size={16} />} label={item.title} onClick={() => go(`/student/concepts/${item.id}`)} />)}</ResultGroup> : null}
        {results.data?.learners.length ? <ResultGroup label="Learners">{results.data.learners.map((item) => <ResultButton key={item.id} icon={<Users size={16} />} label={item.name} onClick={() => go(`/teacher/students/${item.id}`)} />)}</ResultGroup> : null}
        {query.trim() && !results.isLoading && results.data && !results.data.courses.length && !results.data.concepts.length && !results.data.learners.length && <div className="command-empty">No authorized results for “{query}”.</div>}
      </div>
    </div>
  </div>;
}

function ResultGroup({ label, children }: { label: string; children: React.ReactNode }) { return <div><div className="result-group-label">{label}</div>{children}</div>; }
function ResultButton({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick: () => void }) { return <button className="command-result" onClick={onClick}>{icon}<span>{label}</span><ArrowUpRight size={14} /></button>; }
