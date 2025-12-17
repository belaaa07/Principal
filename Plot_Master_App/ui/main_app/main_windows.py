import customtkinter as ctk
from ui.modules.work_orders.ot_registration_view import crear_modulo_ot_embedded, crear_modulo_ot

# ==========================================================================
# CLASE 1: Módulo de Órdenes de Trabajo (Contiene las Subpestañas)
# ==========================================================================

class OrdenesFrame(ctk.CTkFrame):
    """
    Este módulo implementa las subpestañas: + Generar OT, Pendientes, Aprobados.
    """
    def __init__(self, parent, open_generar_callback=None):
        # El parent es self.main_content_frame de la clase App
        super().__init__(parent, fg_color="transparent") 
        self.open_generar_callback = open_generar_callback
        
        # Configurar el grid interno para el sub-sidebar (columna 0) y el contenido (columna 1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -----------------------------------------------------------
        # A. Sub-Sidebar de Navegación Interna (Subpestañas)
        # -----------------------------------------------------------
        
        self.internal_sidebar = ctk.CTkFrame(self, 
                                             width=180, 
                                             corner_radius=8, 
                                             fg_color="#E0E0E0") # Color más claro para diferenciar
        self.internal_sidebar.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.internal_sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self.internal_sidebar, text="VISTAS OT", 
                     font=ctk.CTkFont(size=12, weight="bold"), 
                     text_color="gray40").grid(row=0, column=0, padx=15, pady=(20, 5), sticky="w")

        # Botones de Sub-pestañas
        self.generar_ot_button = self._create_sub_button(1, "➕ Generar OT", "generar")
        self.pendientes_button = self._create_sub_button(2, "🕔 Pendientes", "pendientes")
        self.aprobados_button = self._create_sub_button(3, "✅ Aprobados", "aprobados")

        # -----------------------------------------------------------
        # B. Marcos de Contenido de las Subpestañas (Vistas)
        # -----------------------------------------------------------
        
        self.internal_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.internal_content_frame.grid(row=0, column=1, sticky="nsew")
        self.internal_content_frame.grid_rowconfigure(0, weight=1)
        self.internal_content_frame.grid_columnconfigure(0, weight=1)

        # Frames internos para el contenido real
        self.generar_frame = self._create_view_frame("FORMULARIO: GENERAR NUEVA OT")
        self.pendientes_frame = self._create_view_frame("TABLA: ÓRDENES PENDIENTES")
        self.aprobados_frame = self._create_view_frame("TABLA: ÓRDENES APROBADAS")

        # Inicia en la vista "generar" sin abrir ventanas externas
        self.select_view_by_name("generar")

    def _create_sub_button(self, row, text, command_name):
        # Función auxiliar para crear botones de subpestaña
        button = ctk.CTkButton(self.internal_sidebar, 
                               corner_radius=6, 
                               height=35, 
                               text=text,
                               fg_color="transparent", 
                               text_color=("gray10", "gray90"), 
                               hover_color="#CCCCCC", 
                               anchor="w",
                               command=lambda: self.select_view_by_name(command_name))
        button.grid(row=row, column=0, padx=10, pady=(0, 5), sticky="ew")
        return button

    def _create_view_frame(self, text):
        # Función auxiliar para crear los frames de contenido de la vista
            frame = ctk.CTkFrame(self.internal_content_frame, fg_color="transparent")
            frame.grid_rowconfigure(0, weight=0)
            frame.grid_rowconfigure(1, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(frame,
                                 text=text,
                                 font=ctk.CTkFont(size=24, weight="bold"),
                                 text_color="#343638")
            label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

            # Si es la vista de 'generar', añadimos botón que abre el módulo OT cuando el usuario lo solicita
            if "GENERAR" in text.upper():
                generar_btn = ctk.CTkButton(frame, text="Generar OT", fg_color="#5E835E", hover_color="#4B6B4B",
                                            width=180, height=40, command=self._on_generar_pressed)
                generar_btn.grid(row=1, column=0, sticky="w", padx=20, pady=(10, 20))
            return frame

    def _on_generar_pressed(self):
        # Limpiar contenido previo del frame de 'generar' y ejecutar callback embebido
        for child in self.generar_frame.winfo_children():
            child.destroy()

        if callable(self.open_generar_callback):
            # Pasamos el frame donde debe montarse el formulario
            self.open_generar_callback(parent=self.generar_frame)
        else:
            # No hacemos nada si no hay callback embebido
            return

    def select_view_by_name(self, name):
        # Lógica de cambio de Subpestaña
        buttons = [self.generar_ot_button, self.pendientes_button, self.aprobados_button]
        for button in buttons:
            button.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        frames = [self.generar_frame, self.pendientes_frame, self.aprobados_frame]
        for frame in frames:
            frame.grid_forget()

        active_color = "#AAAAAA" 
        
        if name == "generar":
            self.generar_ot_button.configure(fg_color=active_color, text_color="black")
            self.generar_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "pendientes":
            self.pendientes_button.configure(fg_color=active_color, text_color="black")
            self.pendientes_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "aprobados":
            self.aprobados_button.configure(fg_color=active_color, text_color="black")
            self.aprobados_frame.grid(row=0, column=0, sticky="nsew")


# ==========================================================================
# CLASE 2: Aplicación Principal (App)
# ==========================================================================

class MainAppFrame(ctk.CTkFrame):
    def __init__(self, parent, user_name: str = None):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.user_name = user_name or "Usuario"

        # Make this frame expand to fill parent and set column weights
        self.grid(row=0, column=0, sticky="nsew")
        try:
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(0, weight=1)
        except Exception:
            pass
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # 2. Creación del Marco de Navegación (Sidebar)
        # ------------------------------------------------------------------
        
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#263238")
        self.navigation_frame.grid(row=0, column=0, sticky="ns")
        self.navigation_frame.grid_rowconfigure(12, weight=1)

        # ------------------------------------------------------------------
        # 3. Elementos Fijos del Sidebar
        # ------------------------------------------------------------------
        
        self.title_label = ctk.CTkLabel(self.navigation_frame,
                        text="Plot Master",
                        font=ctk.CTkFont(size=18, weight="bold"),
                        text_color="white")
        self.title_label.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        self.user_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        self.user_frame.grid(row=1, column=0, padx=10, pady=(6, 12), sticky="ew")
        self.user_label = ctk.CTkLabel(self.user_frame,
                   text=f"👤  {self.user_name}",
                   anchor="w",
                   font=ctk.CTkFont(size=13, weight="normal"),
                   text_color="white")
        self.user_label.pack(fill="x")

        # MENÚ
        self.menu_separator = ctk.CTkLabel(self.navigation_frame,
                           text="MENÚ",
                           font=ctk.CTkFont(size=12, weight="bold"),
                           text_color="#B0BEC5")
        self.menu_separator.grid(row=2, column=0, padx=16, pady=(12, 6), sticky="w")

        # ------------------------------------------------------------------
        # 4. Botones de Navegación (Pestañas)
        # ------------------------------------------------------------------

        def create_nav_button(row, text, command_name):
            return ctk.CTkButton(self.navigation_frame,
                                 corner_radius=0, height=40, border_spacing=10,
                                 text=text, fg_color="transparent",
                                 text_color=("#ECEFF1", "#ECEFF1"), hover_color=("#344A4E", "#344A4E"),
                                 anchor="w",
                                 command=lambda: self.select_frame_by_name(command_name))

        self.inicio_button = create_nav_button(3, "🏠  Inicio", "inicio")
        self.inicio_button.grid(row=3, column=0, sticky="ew", padx=6)

        self.ordenes_button = create_nav_button(4, "📋  Órdenes de trabajo", "ordenes")
        self.ordenes_button.grid(row=4, column=0, sticky="ew", padx=6)

        # CATÁLOGO
        self.catalogo_separator = ctk.CTkLabel(self.navigation_frame,
                                               text="CATÁLOGO",
                                               font=ctk.CTkFont(size=12, weight="bold"),
                                               text_color="#B0BEC5")
        self.catalogo_separator.grid(row=5, column=0, padx=16, pady=(12, 6), sticky="w")

        self.clientes_button = create_nav_button(6, "👥  Clientes", "clientes")
        self.clientes_button.grid(row=6, column=0, sticky="ew", padx=6)

        self.reportes_button = create_nav_button(7, "📊  Reportes", "reportes")
        self.reportes_button.grid(row=7, column=0, sticky="ew", padx=6)

        # CONFIGURACIÓN
        self.config_separator = ctk.CTkLabel(self.navigation_frame,
                                             text="CONFIGURACIÓN",
                                             font=ctk.CTkFont(size=12, weight="bold"),
                                             text_color="#B0BEC5")
        self.config_separator.grid(row=8, column=0, padx=16, pady=(12, 6), sticky="w")

        self.acceso_button = create_nav_button(9, "⚙️  Administrar accesos", "acceso")
        self.acceso_button.grid(row=9, column=0, sticky="ew", padx=6)
        
        # ------------------------------------------------------------------
        # 5. Marcos de Contenido (Módulos) - ¡Conexión!
        # ------------------------------------------------------------------
        
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#F7F7F7") 
        self.main_content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # Contenedor central persistente donde se montan todos los módulos
        self.central_container = ctk.CTkFrame(self.main_content_frame, fg_color="#F1F5F9")
        self.central_container.grid(row=0, column=0, sticky="nsew")
        self.central_container.grid_rowconfigure(0, weight=1)
        self.central_container.grid_columnconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # 6. Inicialización y Lógica de Pestañas
        # ------------------------------------------------------------------
        # Inicia mostrando el módulo de Inicio
        self.select_frame_by_name("inicio")

    def _create_module_frame(self, text):
        # Función para crear módulos genéricos
        frame = ctk.CTkFrame(self.central_container, fg_color="transparent")
        label = ctk.CTkLabel(frame, 
                             text=text, 
                             font=ctk.CTkFont(size=30, weight="bold"), 
                             text_color="#343638")
        label.pack(padx=50, pady=50)
        return frame

    def _clear_central(self):
        for child in self.central_container.winfo_children():
            child.destroy()

    def _show_inicio(self):
        self._clear_central()
        frame = self._create_module_frame("Módulo de Inicio")
        frame.grid(row=0, column=0, sticky="nsew")

    def _show_clientes(self):
        self._clear_central()
        frame = self._create_module_frame("Módulo: Clientes")
        frame.grid(row=0, column=0, sticky="nsew")

    def _show_reportes(self):
        self._clear_central()
        frame = self._create_module_frame("Módulo: Reportes")
        frame.grid(row=0, column=0, sticky="nsew")

    def _show_acceso(self):
        self._clear_central()
        frame = self._create_module_frame("Módulo: Administrar Accesos")
        frame.grid(row=0, column=0, sticky="nsew")

    def _show_ordenes(self):
        self._clear_central()
        crear_modulo_ot_embedded(parent=self.central_container, vendedor=self.user_name)

    def select_frame_by_name(self, name):
        # Lógica de navegación principal (sidebar)
        buttons = [self.inicio_button, self.ordenes_button, self.clientes_button, self.reportes_button, self.acceso_button]
        for button in buttons:
            button.configure(fg_color="transparent")

        active_color = ("#69B5F9", "#0086E2")

        if name == "inicio":
            self.inicio_button.configure(fg_color=active_color)
            self._show_inicio()
        elif name == "ordenes":
            self.ordenes_button.configure(fg_color=active_color)
            self._show_ordenes()
        elif name == "clientes":
            self.clientes_button.configure(fg_color=active_color)
            self._show_clientes()
        elif name == "reportes":
            self.reportes_button.configure(fg_color=active_color)
            self._show_reportes()
        elif name == "acceso":
            self.acceso_button.configure(fg_color=active_color)
            self._show_acceso()


# --------------------------------------------------------------------------
# 7. Ejecución
# --------------------------------------------------------------------------

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Plot Master - Demo")
    root.geometry("1000x700")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Instanciar la aplicación principal dentro del root
    main_app = MainAppFrame(root, user_name="Demo")
    root.mainloop()