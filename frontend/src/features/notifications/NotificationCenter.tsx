import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getNotifications, markNotificationRead } from "../../lib/api";

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["notifications"], queryFn: getNotifications, staleTime: 15_000 });
  const read = useMutation({ mutationFn: markNotificationRead, onSuccess: () => void client.invalidateQueries({ queryKey: ["notifications"] }) });
  const go = (id: string, destination: string) => { if (!read.isPending) read.mutate(id); setOpen(false); navigate(destination); };
  return <div className="notification-wrap"><button className="icon-control" aria-label="Open notifications" aria-expanded={open} onClick={() => setOpen((value) => !value)}><Bell size={16} />{query.data?.unread_count ? <span className="unread-dot" /> : null}</button>{open && <div className="popover"><div className="popover-header"><div><span className="eyebrow">Workspace signals</span><h3>Notifications</h3></div><button className="icon-control" onClick={() => setOpen(false)} aria-label="Close notifications"><X size={15} /></button></div>{query.data?.results.length ? query.data.results.slice(0, 6).map((item) => <button className={`notification-item ${item.read ? "" : "unread"}`} key={item.id} onClick={() => go(item.id, item.destination)}><strong>{item.title}</strong><span>{item.body}</span></button>) : <div className="command-empty">You’re caught up.</div>}</div>}</div>;
}
