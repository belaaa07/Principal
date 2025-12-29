# Plot Master

Plot Master es una aplicación de escritorio pensada para operar de forma local con dos interfaces independientes: la consola del Administrador y la experiencia del Vendedor. Toda la lógica corre desde el código fuente sin depender de actualizaciones automáticas ni servicios externos de publicación.

## Requisitos previos

- Python 3.10 o superior.
- Un entorno virtual (recomendado) y las dependencias instaladas con `pip install -r requirements.txt`.
- PyInstaller solo es necesario si se quiere generar un ejecutable (`generar_exe.py`).

## Estructura clave

- `assets/`: recursos gráficos y archivos estáticos que consumen los módulos de interfaz.
- `plotmaster/`: paquete principal con los módulos de Administrador y Vendedor.
- `ejecutar.py`: lanzador mínimo que muestra un menú y arranca la aplicación elegida.
- `generar_exe.py`: script dedicado para empaquetar cada aplicación con PyInstaller.
- `schema_db.sql`: esqueleto de la base de datos usada por la aplicación.
- `.env.example`: variables de entorno que deben copiarse a `.env` para inyectar llaves de Supabase u otras credenciales.

## Configuración del entorno

1. Copiar `.env.example` a `.env` dentro de la raíz del proyecto.
2. Completar `SUPABASE_URL` y `SUPABASE_KEY` con las credenciales locales si se usan los servicios de Supabase.
3. Activar el entorno virtual y ejecutar `pip install -r requirements.txt`.

## Ejecución local

1. Desde la raíz del proyecto ejecutar:
   ```
   python ejecutar.py
   ```
2. Elegir `1` para el Programa Administrador o `2` para el Programa Vendedor desde el menú interactivo.
3. Cada programa instanciará su ventana en `customtkinter` y seguirá ejecutándose hasta que el usuario la cierre.

## Generar un ejecutable (.exe)

1. Asegurarse de tener PyInstaller instalado (`pip install pyinstaller`).
2. Ejecutar `python generar_exe.py`.
3. Elegir `1` (Administrador) o `2` (Vendedor); el script compilará la aplicación y dejará el binario en `dist/<app>/PlotMaster_<App>.exe`.
4. Cada compilación usa `--onefile` y trabaja en carpetas separadas bajo `dist/` y `build/` para evitar mezclar salidas.

El proyecto ahora es local y autónomo: no hay actualizaciones automáticas, GitHub Releases ni lógica de versión. Solo el launcher, los programas activos y la herramienta de empaquetado.
