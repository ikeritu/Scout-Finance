"""Visual, responsive and accessibility helpers for v2.28."""
from __future__ import annotations

TOKENS={
 "primary":"#0E6F78","primary_dark":"#07535A","background":"#F4F6F8","surface":"#FFFFFF",
 "text":"#18222E","muted":"#526173","border":"#D5DEE8","warning":"#8A4B00","danger":"#A4261D","focus":"#005FCC",
}

def css():
 t=TOKENS
 return f"""<style>
:root{{--sf-primary:{t['primary']};--sf-text:{t['text']};--sf-muted:{t['muted']};--sf-border:{t['border']};--sf-surface:{t['surface']};}}
.stApp{{color:var(--sf-text)}}
[data-testid="stMainBlockContainer"]{{max-width:1440px;padding-top:2rem;padding-bottom:4rem}}
[data-testid="stSidebar"]{{border-right:1px solid var(--sf-border)}}
h1,h2,h3{{letter-spacing:-.018em}}h1{{font-size:clamp(1.85rem,3vw,2.55rem)}}
p,li,label,[data-testid="stCaptionContainer"]{{line-height:1.5}}
.stButton>button,.stDownloadButton>button{{min-height:44px;border-radius:10px;font-weight:650}}
.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div{{min-height:44px}}
*:focus-visible{{outline:3px solid {t['focus']}!important;outline-offset:2px!important}}
[data-testid="stDataFrame"]{{border:1px solid var(--sf-border);border-radius:12px;overflow:hidden}}
[data-testid="stAlert"]{{border-radius:12px}}
.sf-context{{color:var(--sf-muted);font-size:.88rem;margin:.2rem 0 1rem}}
.sf-skip{{position:absolute;left:-9999px;top:8px;background:#fff;color:{t['primary_dark']};padding:10px 14px;z-index:9999;border:2px solid {t['focus']}}}
.sf-skip:focus{{left:12px}}
@media(max-width:900px){{[data-testid="stMainBlockContainer"]{{padding-left:1rem;padding-right:1rem}}[data-testid="column"]{{min-width:calc(50% - 1rem)}}}}
@media(max-width:640px){{[data-testid="stMainBlockContainer"]{{padding:.75rem .75rem 3rem}}[data-testid="column"]{{min-width:100%!important;width:100%!important}}.stDataFrame{{font-size:.82rem}}h1{{font-size:1.8rem}}}}
@media(prefers-reduced-motion:reduce){{*,*::before,*::after{{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}}}
@media(prefers-contrast:more){{:root{{--sf-border:#526173}}.stButton>button{{border-width:2px}}}}
</style><a class="sf-skip" href="#contenido-principal">Saltar al contenido principal</a><div id="contenido-principal"></div>"""

def apply(st):st.markdown(css(),unsafe_allow_html=True)

def screen_context(st,title,description):
 st.header(title);st.markdown(f'<p class="sf-context">{description}</p>',unsafe_allow_html=True)

def contrast_ratio(hex_a,hex_b):
 def luminance(value):
  rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]
  rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
  return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
 a,b=sorted((luminance(hex_a),luminance(hex_b)),reverse=True)
 return (a+.05)/(b+.05)
