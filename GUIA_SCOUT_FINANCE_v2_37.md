# Guía de Scout Finance v2.37

## Inicio en Windows 11

Desde PowerShell:

```powershell
Set-Location 'D:\Proyectos\💰 Scout Finance'
git switch phase8-product-ui-v2-37
git pull --ff-only
python tests/qa_phase8_full_suite_v2_37.py
.\run_local_ui_v2_37.bat
```

La aplicación debe abrir `http://localhost:8501`. No expone el servidor a la red local.

Si faltan dependencias:

```powershell
python -m pip install -r requirements-ui-v2_28.txt
```

## Cómo leer el producto

- **Inicio:** resume disponibilidad y límites.
- **Universo:** busca y filtra los 50 activos.
- **Ranking experimental:** muestra JPX; TWSE y revisión requerida quedan separados.
- **Ficha:** reúne precio, scoring y fundamentales cuando los datos detallados existen localmente.
- **Comparador:** contrasta entre dos y cuatro activos y avisa al mezclar mercados.
- **Watchlist:** guarda decisiones de investigación privadas, nunca órdenes.
- **Informes:** exporta HTML y un manifiesto de trazabilidad.
- **Ayuda:** explica metodología y límites en lenguaje sencillo.

## Interpretación correcta

`HIGH` describe cobertura/comparabilidad, no probabilidad de rentabilidad. `INSUFFICIENT_EVIDENCE` significa que no se ha demostrado capacidad predictiva fuera de muestra. La ausencia de evidencia tampoco demuestra que el enfoque sea inútil.

## Checklist visual de aceptación

- [ ] La portada muestra `INSUFFICIENT_EVIDENCE` sin necesidad de desplegar nada.
- [ ] Se ven 50 activos: 41 JPX, 7 TWSE parciales y 2 en revisión.
- [ ] TWSE no aparece en el ranking principal.
- [ ] P020 y P178 no tienen posición automática.
- [ ] La ficha de P155 muestra datos reales locales y fecha de corte.
- [ ] La ficha de P020 muestra el bloqueo por anomalía.
- [ ] La ficha de P178 muestra el requisito de contrato financiero.
- [ ] El comparador advierte cuando mezcla JPX y TWSE.
- [ ] Crear, editar, exportar y eliminar una watchlist funciona.
- [ ] Los informes incluyen el aviso obligatorio y la decisión de fase 7.
- [ ] No aparece ningún dato demo ni se produce ninguna llamada de red.
- [ ] La interfaz es utilizable con teclado y a un ancho aproximado de 375 px.

## Recuperación

Las watchlists se guardan en `data/watchlists/*.v2_37.json`. Cada sobrescritura conserva un `.bak`. Si un archivo es inválido, Scout Finance lo omite y muestra el error; no intenta repararlo silenciosamente.

## Límite

Scout Finance es una herramienta experimental de investigación. No constituye recomendación de comprar, vender o mantener ningún activo. El scoring no dispone de evidencia histórica suficiente para considerarse predictivo.
