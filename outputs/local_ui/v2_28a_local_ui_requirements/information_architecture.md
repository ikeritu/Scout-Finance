# Local UI information architecture

```mermaid
flowchart TD
    A["Inicio / Estado"] --> B["Universo"]
    B --> C["Detalle de activo"]
    B --> D["Watchlists"]
    D --> E["Informes y exports"]
    A --> F["Score Explorer"]
    A --> G["Mantenimiento"]
    A --> H["Ayuda y límites"]
```

The sidebar keeps the five main destinations visible. Asset detail opens from the catalog without discarding filter state. Maintenance remains advanced and read-only by default.

## Global status bar

Every screen shows:

- universe pointer health;
- scoring state;
- refresh state;
- generated artifact provenance;
- “No es asesoramiento financiero”.

Status may not rely on color alone.
