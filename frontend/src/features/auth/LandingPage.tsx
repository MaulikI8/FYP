import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowRight, BrainCircuit, FlaskConical, GraduationCap, Lightbulb, Network, RefreshCcw, Users } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { loginDemo, type Role } from "../../lib/api";
import { Button, Eyebrow } from "../../components/ui/Primitives";
import { homeFor } from "../../layouts/AppShell";

const personas: Array<{ id: string; role: string; subtitle: string; detail: string; icon: typeof GraduationCap; accent: string }> = [
  { id: "sahana", role: "Student", subtitle: "Sahana · Grade 10", detail: "Follow evidence to your next useful step.", icon: GraduationCap, accent: "plum" },
  { id: "rina", role: "Teacher", subtitle: "Ms. Rina · Mathematics", detail: "Turn class patterns into targeted support.", icon: Users, accent: "mint" },
  { id: "suman", role: "Coordinator", subtitle: "Mr. Suman · Demo School", detail: "See curriculum coverage without surveillance.", icon: Network, accent: "amber" },
  { id: "guardian_sahana", role: "Guardian", subtitle: "Sahana’s linked guardian", detail: "Support a learner with a limited view.", icon: Lightbulb, accent: "coral" },
];

export function LandingPage() {
  const client = useQueryClient();
  const navigate = useNavigate();
  const reduceMotion = useReducedMotion();
  const [active, setActive] = useState("assess");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const login = async (id: string) => { setPending(id); setError(""); try { const user = await loginDemo(id); await client.invalidateQueries({ queryKey: ["me"] }); navigate(homeFor(user.role as Role)); } catch (caught) { setError(caught instanceof Error ? caught.message : "The demo login could not be completed."); } finally { setPending(null); } };
  return <main className="landing-v2">
    <div className="landing-threads" aria-hidden="true"><span /><span /><span /></div>
    <header className="landing-nav"><a href="/" className="brand"><span className="brand-mark" /><span>pathloom</span></a><span className="demo-label"><span className="live-dot" /> Fictional local demo</span></header>
    <section className="landing-hero-v2"><div className="landing-copy"><Eyebrow><span className="eyebrow-rule" /> Learning intelligence for the next useful step</Eyebrow><h1>Make the next<br /><em>idea click.</em></h1><p>Pathloom connects a learner’s answer evidence to a clearer explanation, a focused practice path, and visible progress — without turning learning into surveillance.</p><div className="loop-control" role="tablist" aria-label="Pathloom learning loop">{["assess", "understand", "try", "improve"].map((step) => <button key={step} className={active === step ? "active" : ""} onClick={() => setActive(step)} role="tab" aria-selected={active === step}>{step}</button>)}</div><div className="loop-caption"><span className="loop-index">0{["assess", "understand", "try", "improve"].indexOf(active) + 1}</span><strong>{copyForLoop(active).title}</strong><span>{copyForLoop(active).copy}</span></div></div><motion.div className="landing-exhibit" initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .55 }}><div className="exhibit-head"><span><span className="live-dot" /> Sahana’s learning path</span><span>Grade 10 · Mathematics</span></div><div className="exhibit-canvas"><div className="exhibit-line line-one" /><div className="exhibit-line line-two" /><div className="exhibit-node node-start"><span>✓</span><small>known</small></div><div className="exhibit-node node-focus"><span><BrainCircuit size={18} /></span><strong>Factorisation</strong><small>needs a closer look</small></div><div className="exhibit-node node-next"><span><ArrowRight size={17} /></span><small>next step</small></div><div className="exhibit-note"><Eyebrow tone="amber">Suggested because</Eyebrow><strong>2 answer signals</strong><span>point to the factor-pair step</span></div></div><div className="exhibit-footer"><span>Explore → Understand → Try → See growth</span><span><FlaskConical size={13} /> No camera required</span></div></motion.div></section>
    <section className="persona-section-v2"><div className="section-heading-v2"><div><Eyebrow>Enter the workspace</Eyebrow><h2>Choose a perspective</h2></div><p>Each choice signs into a real Django session with its own permissions and fictional records.</p></div><div className="persona-grid-v2">{personas.map(({ id, role, subtitle, detail, icon: Icon, accent }) => <button className={`persona-card-v2 persona-${accent}`} key={id} onClick={() => void login(id)} disabled={!!pending}><span className="persona-icon-v2"><Icon size={20} /></span><span className="persona-copy-v2"><small>{role}</small><strong>{subtitle}</strong><span>{detail}</span></span>{pending === id ? <RefreshCcw size={17} className="spin" /> : <ArrowRight size={17} />}</button>)}</div>{error && <p className="landing-error" role="alert">{error}</p>}</section>
    <footer className="landing-footer-v2"><span>PATHLOOM · Islington College FYP prototype</span><span>Assess · Understand · Try · Improve</span></footer>
  </main>;
}

function copyForLoop(step: string) { const values: Record<string, { title: string; copy: string }> = { assess: { title: "Start with evidence.", copy: "A response gives the path a signal." }, understand: { title: "Find the missing step.", copy: "See the concept and its prerequisites." }, try: { title: "Work with the idea.", copy: "Manipulate, explain, and test a fresh example." }, improve: { title: "See what changed.", copy: "Return to evidence, not a promise." } }; return values[step]; }
