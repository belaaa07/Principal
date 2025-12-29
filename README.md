# Plot Master (Administrador y Vendedor)

Proyecto existente dividido en dos aplicaciones de escritorio (Administrador y Vendedor) con UI en CustomTkinter y backend en Supabase. No se agregan nuevas features: el foco es ordenar, unificar y dejar listo para versionado, build a .exe y futuro auto-update.

## Estructura actual
```
.
├─ plotmaster/
│  ├─ apps/
│  │  ├─ admin/           # Entrypoint y UI admin (main.py, vistas admin)
│  │  └─ vendor/          # Entrypoint y UI vendedor (main.py, vistas vendedor)
│  └─ core/               # Lógica compartida
│     ├─ services/        # supabase_service.py unificado
│     ├─ ui/              # (placeholder) widgets/temas reutilizables
│     ├─ config/          # (placeholder) settings/env
│     └─ utils/           # (placeholder)
├─ updater/               # Cliente de actualización: check version.json remoto, descarga y swap de .exe
├─ assets/                # Íconos, fuentes, imágenes
├─ config/                # Archivos de config deploy (env.example, pyinstaller specs, version.json plantilla)
├─ docs/                  # Documentación mínima
├─ scripts/               # Scripts de build/packaging (pyinstaller, checksum)
├─ build/                 # Salida temporal (git ignored)
├─ dist/                  # Salida de ejecutables (git ignored)
└─ README.md
```

## Qué queda igual (funcionalidad)

## Configuración rápida (estado actual)
## Configuración rápida (estado actual)
- Python 3.10+.
- Instalar dependencias: `pip install -r requirements.txt`.
- Variables Supabase en `.env` (o en `plotmaster/apps/admin/.env` y `plotmaster/apps/vendor/.env`): `SUPABASE_URL`, `SUPABASE_KEY`. Ejemplo en `config/env.example`.
- Ejecutar hoy (desde la raíz):
	- Admin: `python -m plotmaster.apps.admin.main`
	- Vendedor: `python -m plotmaster.apps.vendor.main`

## Scripts de trabajo
- Desarrollo rápido: `python ejecutar.py` abre un menú y lanza Admin o Vendedor en modo módulo (sin generar .exe).
- Publicación automatizada: `python publicar.py` pregunta la app y la versión (v1.4.0), actualiza `config/*_version.json` y `config/remote_versions/*.json`, elimina builds previos, corre PyInstaller (spec con `onefile`) y copia el ejecutable versionado sin carpeta `internal` a `releases/access/`.
- Los .exe generados quedan nombrados como `PlotMaster_Admin_vX.Y.Z.exe` o `PlotMaster_Vendedor_vX.Y.Z.exe`, listos para subir a GitHub Releases y compatibles con el actualizador existente.

## Unificación de código (estado)
## Build a .exe (PyInstaller)
- Specs listos: `scripts/pyinstaller_admin.spec` y `scripts/pyinstaller_vendor.spec`.
- Ejecutar desde la raíz:
	- `pyinstaller scripts/pyinstaller_admin.spec`
	- `pyinstaller scripts/pyinstaller_vendor.spec`
- Ambos specs ahora definen `onefile=True`, por lo que `dist/PlotMaster_* .exe` se genera como único binario sin carpeta `internal`.
- Salidas: `dist/` (git-ignored). Ajusta `datas` si agregas assets.

## Build a .exe (PyInstaller)
## Auto-update (listo para GitHub)
- Cada `main.py` arranca llamando `updater.check_for_updates("admin")` o `updater.check_for_updates("vendor")` antes de crear la UI, de modo que la app siempre chequea si hay una versión más reciente en GitHub.
- La configuración de `config/update_config.json` define el repo de GitHub (`github.repo`), el prefijo de tag (normalmente `v`) y el nombre del asset que se debe descargar (`asset_name_template`). También mantiene las rutas de versión local (`config/*.json`) y los archivos de versión remotos de ejemplo bajo `config/remote_versions/` para pruebas offline. Por defecto `github.repo` está vacío para que los chequeos funcionen localmente; reemplazalo con tu `<usuario>/<repo>` real cuando publiques releases.
- Cuando se detecta una versión nueva, el gestor descarga el `.exe` correspondiente a `build/updates/{app}/{app}_{version}.exe`, guarda un `pending_<app>.json` y registra la URL del asset. Ese archivo impide que se vuelva a descargar varias veces y sirve de base para un swapper futuro.
- `python -m updater --app admin` (o `vendor`) ejecuta el mismo chequeo manualmente; usa `PLOTMASTER_SKIP_UPDATES=1` si trabajas sin red o en un entorno cerrado.
- El flujo se completa al reemplazar el `.exe` actual con el descargado; la carpeta `build/updates/` está en `.gitignore` y prepara el terreno para integrar `updater/downloader.py` + `updater/swapper.py` y el reemplazo automático en el siguiente arranque.

## Auto-update (diseño futuro)
## Unificación de código (estado)
- Cliente Supabase unificado en `plotmaster/core/services/supabase_service.py` (carga `.env` raíz y de cada app, cache referencial, helpers admin/vendedor).
- Imports actualizados a paquete `plotmaster.*` (ejecución con `-m`).
- Pendiente: centralizar temas/widgets en `plotmaster/core/ui` y settings en `plotmaster/core/config`.

## Próximos pasos sugeridos
- Migrar archivos actuales a la estructura objetivo manteniendo imports relativos (usar un paquete raíz, ej. `plotmaster`).
- Extraer duplicados de servicios (`supabase_service`), login y layouts a `core/`.
- Añadir tests mínimos de servicios críticos (supabase mocks) antes de tocar lógica sensible.
- Completar `requirements.txt` y scripts de build.
