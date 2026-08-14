"""Scout Finance v2.28 local UI foundation. Safe parallel entrypoint."""
from pathlib import Path
import streamlit as st
from src.ui_v2_28 import ConsumerState,SCREENS,build_app_state

st.set_page_config(page_title="Scout Finance — Local Analyst UI",page_icon="📊",layout="wide")
ROOT=Path(__file__).resolve().parent

@st.cache_data(ttl=60,show_spinner=False)
def state_snapshot():
 return build_app_state(ROOT)

def status_chip(label,value,tone="neutral"):
 colors={"ok":"#0E7C86","warn":"#B76E00","bad":"#B42318","neutral":"#526173"}
 color=colors[tone]
 st.markdown(f'<div style="border:1px solid #E1E7EE;border-radius:12px;padding:12px;background:white"><small>{label}</small><div style="font-size:18px;font-weight:750;color:{color}">{value}</div></div>',unsafe_allow_html=True)

def render_status(s):
 st.title("Scout Finance")
 st.caption("Interfaz local de análisis · Estado operativo verificado por pointers")
 a,b,c,d=st.columns(4)
 with a:status_chip("Universo",f"{s.universe.rows:,} activos" if s.universe.available else "No disponible","ok" if s.universe.available else "bad")
 with b:status_chip("Scoring","No disponible" if not s.scoring.allow_ranking else "Productivo","warn" if not s.scoring.allow_ranking else "ok")
 with c:status_chip("Refresh",s.maintenance.refresh_status or "UNKNOWN","warn")
 with d:status_chip("Proveedores",f"{s.maintenance.providers_complete}/{s.maintenance.providers_expected}","warn")
 if not s.scoring.allow_ranking:st.warning("Scoring productivo no autorizado. Rankings, recomendaciones y señales permanecen ocultos.")
 st.info("El catálogo, las watchlists y los informes siguen disponibles. Esta herramienta no ofrece asesoramiento financiero.")

def placeholder(title,message):
 st.header(title);st.info(message);st.caption("Esta pantalla se implementará en las siguientes fases v2.28.")

def main():
 s=state_snapshot()
 with st.sidebar:
  st.markdown("### Scout Finance")
  st.caption("Local Analyst UI · v2.28B")
  selected=st.radio("Navegación",options=[x.id for x in SCREENS],format_func=lambda i:next(f"{x.icon} {x.label}" for x in SCREENS if x.id==i),label_visibility="collapsed")
  st.divider();st.caption(f"Estado: {s.scoring.consumer_state.value}");st.caption("No es asesoramiento financiero")
 if selected=="status":render_status(s)
 elif selected=="universe":placeholder("Universo","Explorador de 43.089 instrumentos con filtros y paginación.")
 elif selected=="watchlists":placeholder("Watchlists","Gestión visual basada en el contrato v2.27C.")
 elif selected=="scores":
  st.header("Score Explorer")
  if s.scoring.consumer_state==ConsumerState.PRODUCTION_RANKING:st.success("Scoring productivo autorizado por pointer.")
  else:st.warning("SCORING UNAVAILABLE · FAIL-CLOSED");st.write("El diagnóstico solo podrá abrirse mediante confirmación explícita.")
 elif selected=="reports":placeholder("Informes y exports","Generación de informes y paquetes con manifiesto.")
 elif selected=="asset":placeholder("Detalle de activo","Metadatos, identidad, linaje y pertenencia a watchlists.")
 elif selected=="maintenance":
  st.header("Mantenimiento");st.warning("Vista avanzada · solo lectura")
  st.write({"refresh":s.maintenance.refresh_status,"providers":f"{s.maintenance.providers_complete}/{s.maintenance.providers_expected}","missing_rows":s.maintenance.missing_rows})
 else:
  st.header("Ayuda y límites");st.markdown("- Catálogo y watchlists: disponibles\n- Ranking productivo: bloqueado\n- Broker y señales: no disponibles")
if __name__=="__main__":main()
