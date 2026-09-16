"""Accessible visual system for Scout Finance v2.37."""

DISCLAIMER = "Herramienta experimental de investigación. No constituye asesoramiento financiero. El scoring no dispone de evidencia histórica suficiente para considerarse predictivo."


def css() -> str:
    return """<style>
:root{--sf-primary:#0b6670;--sf-ink:#17212b;--sf-muted:#546272;--sf-border:#d5dee8;--sf-soft:#f4f7f8;--sf-warn:#8a4b00;--sf-danger:#9b2922}
[data-testid="stMainBlockContainer"]{max-width:1480px;padding-top:1.6rem;padding-bottom:4rem}
[data-testid="stSidebar"]{border-right:1px solid var(--sf-border)}
h1,h2,h3{letter-spacing:-.018em}.sf-subtitle{color:var(--sf-muted);margin-top:-.5rem}.sf-banner{border:1px solid #b8d8dc;background:#edf7f8;padding:14px 16px;border-radius:12px;margin:.5rem 0 1.2rem}.sf-card{border:1px solid var(--sf-border);background:var(--sf-soft);padding:14px;border-radius:12px}.sf-kicker{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--sf-muted)}
.stButton>button,.stDownloadButton>button{min-height:44px;border-radius:10px;font-weight:650}*:focus-visible{outline:3px solid #005fcc!important;outline-offset:2px!important}[data-testid="stDataFrame"]{border:1px solid var(--sf-border);border-radius:12px;overflow:hidden}
@keyframes sfFadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes sfPulseGlow{0%,100%{box-shadow:0 0 0 rgba(15,118,110,0)}50%{box-shadow:0 0 20px rgba(15,118,110,.22)}}
@keyframes sfScan{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
@keyframes sfFill{from{width:8%}to{width:var(--sf-fill)}}
@keyframes sfTicker{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes sfOrbit{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes sfSweep{0%{left:-35%;opacity:.2}45%{opacity:1}100%{left:100%;opacity:.2}}
@keyframes sfNodeFloat{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-8px) scale(1.06)}}
@keyframes sfProgressLoop{0%{transform:translateX(-100%)}100%{transform:translateX(240%)}}
@keyframes sfGaugePop{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
@keyframes sfCheckIn{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
.sf-company-motion{display:grid;grid-template-columns:190px 1fr;gap:18px;align-items:stretch;margin:12px 0 16px;animation:sfFadeUp .45s ease both}
.sf-gauge{--p:75;display:grid;place-items:center;width:168px;height:168px;border-radius:50%;background:conic-gradient(#0f766e calc(var(--p)*1%),#dbeafe 0);animation:sfGaugePop .55s ease both,sfPulseGlow 2.8s ease-in-out infinite}
.sf-gauge-inner{display:grid;place-items:center;width:122px;height:122px;border-radius:50%;background:#fff;border:1px solid #d8e2ef}.sf-gauge-value{font-size:34px;font-weight:900;color:#0f766e}.sf-gauge-label{font-size:12px;color:#64748b}
.sf-checklist{border:1px solid #d8e2ef;border-radius:10px;background:#fff;padding:12px}.sf-check{display:flex;align-items:center;gap:9px;padding:7px 0;border-bottom:1px solid #edf2f7;animation:sfCheckIn .45s ease both}.sf-check:nth-child(2){animation-delay:.12s}.sf-check:nth-child(3){animation-delay:.24s}.sf-check:nth-child(4){animation-delay:.36s}.sf-check:last-child{border-bottom:0}.sf-check-dot{display:grid;place-items:center;width:22px;height:22px;border-radius:999px;background:#dcfce7;color:#0f766e;font-weight:900}
.sf-verify-flow{display:flex;align-items:center;gap:8px;margin:12px 0;overflow:auto}.sf-verify-step{white-space:nowrap;border:1px solid #d8e2ef;border-radius:999px;padding:6px 10px;background:#fff;animation:sfFadeUp .45s ease both}.sf-verify-step.active{border-color:#0f766e;background:#ecfeff;animation:sfPulseGlow 2.2s ease-in-out infinite}.sf-verify-arrow{color:#94a3b8}
.sf-signal-bars{display:grid;gap:8px;margin-top:10px}.sf-signal-row{display:grid;grid-template-columns:120px 1fr 42px;gap:10px;align-items:center;font-size:13px}.sf-signal-bar{height:9px;border-radius:999px;background:#e2e8f0;overflow:hidden}.sf-signal-bar>span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#0f766e);width:var(--sf-fill);animation:sfFill .9s ease both}
.sf-motion-card{position:relative;overflow:hidden;animation:sfFadeUp .42s ease both;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.sf-motion-card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(15,23,42,.08)}
.sf-motion-card.is-selected{animation:sfFadeUp .42s ease both,sfPulseGlow 2.4s ease-in-out infinite}
.sf-motion-card::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(15,118,110,.08),transparent);transform:translateX(-100%);animation:sfScan 2.8s ease-in-out infinite;pointer-events:none}
.sf-confidence-track{height:7px;border-radius:999px;background:#e2e8f0;margin-top:10px;overflow:hidden}
.sf-confidence-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#7dd3fc,#0f766e);width:var(--sf-fill);animation:sfFill .9s ease both}
.sf-live-ticker{border:1px solid #d8e2ef;border-radius:8px;background:#fff;overflow:hidden;margin:10px 0 14px}
.sf-live-ticker-track{display:flex;gap:28px;width:max-content;padding:8px 12px;color:#475569;font-size:13px;animation:sfTicker 18s linear infinite}
.sf-live-dot{display:inline-block;width:8px;height:8px;border-radius:999px;background:#0f766e;margin-right:6px;animation:sfPulseGlow 1.6s ease-in-out infinite}
.sf-analysis-engine{position:relative;border:1px solid #b8d8dc;border-radius:10px;background:linear-gradient(135deg,#f8fdff,#eefafa);padding:14px 16px;margin:10px 0 16px;overflow:hidden}
.sf-analysis-engine::before{content:"";position:absolute;top:0;bottom:0;width:30%;background:linear-gradient(90deg,transparent,rgba(14,116,144,.16),transparent);animation:sfSweep 2.2s ease-in-out infinite}
.sf-engine-grid{display:grid;grid-template-columns:1.2fr 1fr;gap:14px;position:relative;z-index:1}
.sf-engine-title{font-weight:850;color:#0f172a;font-size:18px}.sf-engine-sub{color:#475569;font-size:13px;margin-top:2px}
.sf-engine-progress{height:9px;background:#dbeafe;border-radius:999px;overflow:hidden;margin-top:10px}.sf-engine-progress>span{display:block;height:100%;width:38%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#0f766e);animation:sfProgressLoop 1.7s linear infinite}
.sf-node-map{position:relative;height:76px}.sf-node{position:absolute;width:16px;height:16px;border-radius:50%;background:#0f766e;animation:sfNodeFloat 2.4s ease-in-out infinite}.sf-node:nth-child(2){left:34%;top:14px;background:#38bdf8;animation-delay:.2s}.sf-node:nth-child(3){left:62%;top:42px;background:#334155;animation-delay:.4s}.sf-node:nth-child(4){left:86%;top:20px;background:#0f766e;animation-delay:.6s}
.sf-node-line{position:absolute;left:8%;right:8%;top:40px;border-top:2px dashed rgba(15,118,110,.35);animation:sfPulseGlow 2.2s ease-in-out infinite}
@media(max-width:760px){[data-testid="stMainBlockContainer"]{padding:.8rem .8rem 3rem}[data-testid="column"]{min-width:100%!important;width:100%!important}}
@media(max-width:760px){.sf-company-motion{grid-template-columns:1fr}.sf-gauge{margin:auto}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>"""


def apply(st) -> None:
    st.markdown(css(), unsafe_allow_html=True)


def banner(st) -> None:
    st.markdown(f'<div class="sf-banner"><strong>Estado cuantitativo:</strong> INSUFFICIENT_EVIDENCE<br><span>{DISCLAIMER}</span></div>', unsafe_allow_html=True)


def heading(st, title: str, description: str) -> None:
    st.title(title)
    st.markdown(f'<p class="sf-subtitle">{description}</p>', unsafe_allow_html=True)
