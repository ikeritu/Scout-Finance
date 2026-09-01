"""Accessible visual system for Scout Finance v2.37."""

DISCLAIMER = "Herramienta experimental de investigación. No constituye asesoramiento financiero. El scoring no dispone de evidencia histórica suficiente para considerarse predictivo."


def css() -> str:
    return """<style>
:root{--sf-primary:#0b6670;--sf-ink:#17212b;--sf-muted:#546272;--sf-border:#d5dee8;--sf-soft:#f4f7f8;--sf-warn:#8a4b00;--sf-danger:#9b2922}
[data-testid="stMainBlockContainer"]{max-width:1480px;padding-top:1.6rem;padding-bottom:4rem}
[data-testid="stSidebar"]{border-right:1px solid var(--sf-border)}
h1,h2,h3{letter-spacing:-.018em}.sf-subtitle{color:var(--sf-muted);margin-top:-.5rem}.sf-banner{border:1px solid #b8d8dc;background:#edf7f8;padding:14px 16px;border-radius:12px;margin:.5rem 0 1.2rem}.sf-card{border:1px solid var(--sf-border);background:var(--sf-soft);padding:14px;border-radius:12px}.sf-kicker{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--sf-muted)}
.stButton>button,.stDownloadButton>button{min-height:44px;border-radius:10px;font-weight:650}*:focus-visible{outline:3px solid #005fcc!important;outline-offset:2px!important}[data-testid="stDataFrame"]{border:1px solid var(--sf-border);border-radius:12px;overflow:hidden}
@media(max-width:760px){[data-testid="stMainBlockContainer"]{padding:.8rem .8rem 3rem}[data-testid="column"]{min-width:100%!important;width:100%!important}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>"""


def apply(st) -> None:
    st.markdown(css(), unsafe_allow_html=True)


def banner(st) -> None:
    st.markdown(f'<div class="sf-banner"><strong>Estado cuantitativo:</strong> INSUFFICIENT_EVIDENCE<br><span>{DISCLAIMER}</span></div>', unsafe_allow_html=True)


def heading(st, title: str, description: str) -> None:
    st.title(title)
    st.markdown(f'<p class="sf-subtitle">{description}</p>', unsafe_allow_html=True)
