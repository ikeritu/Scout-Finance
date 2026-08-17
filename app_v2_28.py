"""Scout Finance UI, completed through v2.28E. Local Analyst UI · v2.28 · estable; validated in v2.29."""
from pathlib import Path
import pandas as pd
import streamlit as st
from src.ui_v2_28 import ConsumerState,SCREENS,build_app_state
from src.ui_v2_28.catalog import DISPLAY_FIELDS,asset_by_identity,distinct_values,load_catalog,query_catalog
from src.ui_v2_28.watchlists import add,atomic_write,create,export_csv_bytes,list_watchlists,read,remove,scan_watchlists,update_item,update_metadata
from src.ui_v2_28.scoring import diagnostic_contract,distribution_rows,load_diagnostic
from src.ui_v2_28.reports import diagnostic_markdown,package_report,universe_markdown,watchlist_markdown
from src.ui_v2_28.ui import apply as apply_ui,screen_context

st.set_page_config(page_title="Scout Finance — Local Analyst UI",page_icon="📊",layout="wide")
ROOT=Path(__file__).resolve().parent
apply_ui(st)

@st.cache_data(ttl=60,show_spinner=False)
def state_snapshot():return build_app_state(ROOT)
@st.cache_data(show_spinner="Cargando catálogo operativo…")
def catalog_snapshot(path,sha):return load_catalog(Path(path))
def go(screen,identity=None):
 if identity:st.session_state.asset_identity=identity
 st.session_state.screen=screen;st.rerun()
def table(rows):
 fields=["name","ticker","exchange","isin","country","currency","asset_type","provider","identity_key"]
 st.dataframe(pd.DataFrame(rows,columns=fields),use_container_width=True,hide_index=True)
def chip(label,value,tone="neutral"):
 colors={"ok":"#0E7C86","warn":"#B76E00","bad":"#B42318","neutral":"#526173"};color=colors[tone]
 st.markdown(f'<div style="border:1px solid #E1E7EE;border-radius:12px;padding:12px;background:white"><small>{label}</small><div style="font-size:18px;font-weight:750;color:{color}">{value}</div></div>',unsafe_allow_html=True)
def render_status(s):
 st.title("Scout Finance");st.caption("Interfaz local de análisis · Estado operativo verificado por pointers")
 values=(("Universo",f"{s.universe.rows:,} activos" if s.universe.available else "No disponible","ok" if s.universe.available else "bad"),("Scoring","No disponible" if not s.scoring.allow_ranking else "Productivo","warn"),("Refresh",s.maintenance.refresh_status or "UNKNOWN","warn"),("Proveedores",f"{s.maintenance.providers_complete}/{s.maintenance.providers_expected}","warn"))
 for col,args in zip(st.columns(4),values):
  with col:chip(*args)
 if not s.scoring.allow_ranking:st.warning("Scoring productivo no autorizado. Rankings, recomendaciones y señales permanecen ocultos.")
 st.info("El catálogo, las watchlists y los informes siguen disponibles. Esta herramienta no ofrece asesoramiento financiero.")
def render_catalog(rows):
 screen_context(st,"Universo operativo","Exploración de metadatos. No contiene scores, rankings ni recomendaciones.")
 search=st.text_input("Buscar",placeholder="Nombre, ticker, ISIN o identidad estable");filters={};fields=("country","exchange","currency","asset_type","provider")
 for col,field in zip(st.columns(5),fields):
  with col:filters[field]=st.multiselect(field.replace("_"," ").title(),distinct_values(rows,field))
 a,b=st.columns([1,3]);page_size=a.selectbox("Filas",[25,50,100,250],index=1);initial=query_catalog(rows,search,filters,1,page_size)
 page=b.number_input("Página",1,initial.pages,1);result=query_catalog(rows,search,filters,page,page_size)
 st.caption(f"{result.total:,} resultados · página {result.page} de {result.pages}");table(result.rows)
 options={f'{x["ticker"]} · {x["exchange"]} · {x["name"]}':x["identity_key"] for x in result.rows}
 if options:
  label=st.selectbox("Activo seleccionado",options)
  if st.button("Abrir detalle",type="primary"):go("asset",options[label])
def choose_watchlist():
 available,errors=scan_watchlists(ROOT)
 for path,error in errors:st.warning(f"Watchlist omitida por estar dañada: {path.name} · {error}")
 if not available:return None,None
 labels={f'{data["name"]} ({len(data["items"])})':path for path,data in available};path=labels[st.selectbox("Watchlist",labels)];return path,read(path)
def render_watchlists(rows):
 screen_context(st,"Watchlists","Listas locales basadas únicamente en identidad y metadatos.")
 with st.expander("Crear watchlist"):
  name=st.text_input("Nombre",key="new_wl_name");description=st.text_input("Descripción",key="new_wl_description")
  if st.button("Crear"):
   try:create(ROOT,name,description);st.success("Watchlist creada");st.rerun()
   except ValueError as exc:st.error(str(exc))
 path,data=choose_watchlist()
 if not data:st.info("Todavía no hay watchlists locales.");return
 with st.expander("Editar datos de la lista"):
  name=st.text_input("Nombre",data["name"],key="edit_wl_name");description=st.text_input("Descripción",data.get("description",""),key="edit_wl_desc")
  if st.button("Guardar datos"):
   try:update_metadata(path,data,name,description);st.rerun()
   except ValueError as exc:st.error(str(exc))
 st.subheader("Añadir activo");query=st.text_input("Buscar activo para añadir",key="wl_search");matches=query_catalog(rows,query,page_size=25).rows if query else ()
 if matches:
  labels={f'{x["ticker"]} · {x["exchange"]} · {x["name"]}':x for x in matches};label=st.selectbox("Resultado",labels);tags=st.text_input("Etiquetas separadas por comas");note=st.text_area("Nota")
  if st.button("Añadir a watchlist",type="primary"):
   try:add(data,labels[label],tags,note);atomic_write(path,data);st.rerun()
   except ValueError as exc:st.error(str(exc))
 st.subheader(f'Activos ({len(data["items"])})');table(data["items"])
 if data["items"]:
  choices={f'{x["ticker"]} · {x["exchange"]}':x for x in data["items"]};item=choices[st.selectbox("Editar activo",choices)]
  tags=st.text_input("Etiquetas",",".join(item.get("tags",[])),key="item_tags");note=st.text_area("Nota",item.get("note",""),key="item_note");a,b,c=st.columns(3)
  if a.button("Guardar nota y etiquetas"):update_item(data,item["identity_key"],tags,note);atomic_write(path,data);st.rerun()
  if b.button("Abrir detalle"):go("asset",item["identity_key"])
  if c.button("Eliminar de la lista"):remove(data,item["identity_key"]);atomic_write(path,data);st.rerun()
 st.download_button("Descargar CSV",export_csv_bytes(data),file_name=f'{path.stem}.csv',mime="text/csv")
def render_asset(rows):
 screen_context(st,"Detalle de activo","Identidad, metadatos, linaje y pertenencia a watchlists.");identity=st.session_state.get("asset_identity","")
 if not identity:st.info("Selecciona un activo desde Universo o una watchlist.");return
 try:asset=asset_by_identity(rows,identity)
 except ValueError as exc:st.error(str(exc));return
 st.subheader(f'{asset["name"]} · {asset["ticker"]}');st.caption(asset["identity_key"])
 for col,field in zip(st.columns(4),("exchange","country","currency","asset_type")):
  with col:chip(field.replace("_"," ").title(),asset[field])
 st.markdown("#### Identidad y linaje");st.json({key:asset[key] for key in DISPLAY_FIELDS},expanded=True)
 memberships=[data["name"] for _,data in list_watchlists(ROOT) if any(x["identity_key"]==identity for x in data["items"])]
 st.write("Watchlists:",", ".join(memberships) if memberships else "Ninguna");unknown=[key for key,value in asset.items() if value=="Unknown"]
 if unknown:st.warning("Metadatos desconocidos: "+", ".join(unknown))
 st.info("Vista descriptiva. Sin recomendación, señal, score ni ranking.")
def render_scores(s):
 screen_context(st,"Score Explorer","Estado de scoring y diagnóstico opcional de preparación de datos.")
 if s.scoring.allow_ranking:
  st.success("Scoring productivo autorizado por el pointer operativo.");return
 contract=diagnostic_contract(ROOT);st.warning("SCORING UNAVAILABLE · FAIL-CLOSED")
 st.write("No existe un scoring productivo autorizado. No se muestran rankings, recomendaciones ni señales.")
 with st.expander("Diagnóstico opcional de preparación de datos"):
  st.caption(f'Rol: {contract["role"] or "UNAVAILABLE"} · {contract["rows"]:,} filas · no apto para producción')
  acknowledged=st.checkbox("Entiendo que mide cobertura y calidad de datos, no atractivo de inversión ni ranking.",key="diagnostic_ack")
  if acknowledged and st.button("Abrir diagnóstico",type="primary"):
   try:
    st.session_state.diagnostic_summary=load_diagnostic(ROOT,True)
    st.session_state.diagnostic_consent_granted=True
   except (OSError,ValueError,PermissionError) as exc:st.error(str(exc))
 summary=st.session_state.get("diagnostic_summary") if acknowledged else None
 if not summary:return
 st.error("DIAGNÓSTICO · DATA_READINESS_ONLY · NO PRODUCTIVO")
 cols=st.columns(4)
 for col,(field,value) in zip(cols,summary["component_means"].items()):
  col.metric(field.replace("_"," ").title(),"N/A" if value is None else f"{value:.2f}",help="Componente de calidad/cobertura; no mide rentabilidad esperada.")
 a,b=st.columns(2)
 with a:st.subheader("Buckets diagnósticos");st.dataframe(pd.DataFrame(distribution_rows(summary["buckets"],summary["rows"])),hide_index=True,use_container_width=True)
 with b:st.subheader("Cobertura por proveedor");st.dataframe(pd.DataFrame(distribution_rows(summary["providers"],summary["rows"])),hide_index=True,use_container_width=True)
 st.caption("El campo dry_run_rank se ignora. No se ordenan activos por score.")
def report_downloads(markdown,kind,stem,sources):
 fmt=st.radio("Formato",["md","html"],horizontal=True,key=f"fmt_{kind}");payload,manifest=package_report(markdown,kind,fmt,sources)
 st.download_button("Descargar informe",payload,file_name=f"{stem}.{fmt}",mime="text/markdown" if fmt=="md" else "text/html")
 st.download_button("Descargar manifiesto",manifest,file_name=f"{stem}.{fmt}.manifest.json",mime="application/json")
def render_reports(s):
 screen_context(st,"Informes y exports","Descargas descriptivas con manifiesto de procedencia y sin acciones de broker.")
 kind=st.selectbox("Tipo de informe",["Universo","Watchlist","Diagnóstico de datos"])
 if kind=="Universo":
  md=universe_markdown(s.universe,s.scoring);st.markdown(md);report_downloads(md,"universe","scout_finance_universe",[{"dataset_sha256":s.universe.dataset_sha256}])
 elif kind=="Watchlist":
  path,data=choose_watchlist()
  if not data:st.info("Crea una watchlist antes de generar este informe.");return
  md=watchlist_markdown(data,s.scoring);st.markdown(md);report_downloads(md,"watchlist",f"watchlist_{path.stem}",[{"watchlist_id":data["watchlist_id"],"updated_at_utc":data["updated_at_utc"]}])
 else:
  summary=st.session_state.get("diagnostic_summary")
  if not st.session_state.get("diagnostic_consent_granted") or not summary:st.warning("Abre y confirma primero el diagnóstico desde Score Explorer.");return
  md=diagnostic_markdown(summary);st.markdown(md);report_downloads(md,"diagnostic","data_readiness_diagnostic",[{"role":"DATA_READINESS_ONLY","rows":summary["rows"]}])
def placeholder(title,message):st.header(title);st.info(message);st.caption("Esta pantalla se implementará en las siguientes fases v2.28.")
def main():
 s=state_snapshot();rows=catalog_snapshot(str(s.universe.dataset),s.universe.dataset_sha256) if s.universe.available else []
 if "screen" not in st.session_state:st.session_state.screen="status"
 with st.sidebar:
  st.markdown("### Scout Finance");st.caption("Local Analyst UI · v2.29 · validada");ids=[x.id for x in SCREENS]
  selected=st.radio("Navegación",ids,index=ids.index(st.session_state.screen),format_func=lambda i:next(f"{x.icon} {x.label}" for x in SCREENS if x.id==i),label_visibility="collapsed")
  st.session_state.screen=selected;st.divider();st.caption(f"Estado: {s.scoring.consumer_state.value}");st.caption("No es asesoramiento financiero")
 if selected=="status":render_status(s)
 elif selected=="universe":render_catalog(rows) if rows else st.error("Catálogo no disponible")
 elif selected=="watchlists":render_watchlists(rows) if rows else st.error("Catálogo no disponible")
 elif selected=="asset":render_asset(rows)
 elif selected=="scores":render_scores(s)
 elif selected=="reports":render_reports(s)
 elif selected=="maintenance":screen_context(st,"Mantenimiento","Estado operativo avanzado y estrictamente de solo lectura.");st.warning("Vista avanzada · solo lectura");st.write({"refresh":s.maintenance.refresh_status,"providers":f"{s.maintenance.providers_complete}/{s.maintenance.providers_expected}","missing_rows":s.maintenance.missing_rows})
 else:screen_context(st,"Ayuda y límites","Qué puedes hacer, qué permanece bloqueado y cómo interpretar la herramienta.");st.markdown("- Catálogo y watchlists: disponibles\n- Informes descriptivos: disponibles\n- Diagnóstico: requiere confirmación explícita\n- Ranking productivo: bloqueado\n- Broker, recomendaciones y señales: no disponibles\n\n**Navegación:** usa el menú lateral. Todos los controles conservan etiqueta y foco de teclado visible.")
if __name__=="__main__":main()
