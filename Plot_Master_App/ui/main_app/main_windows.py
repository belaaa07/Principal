import customtkinter as ctk

# ==========================================================================
# CLASE 1: Módulo de Órdenes de Trabajo (Contiene las Subpestañas)
# ==========================================================================

class OrdenesFrame(ctk.CTkFrame):
    """
    Este módulo implementa las subpestañas: + Generar OT, Pendientes, Aprobados.
    """
    def __init__(self, parent):
        # El parent es self.main_content_frame de la clase App
        super().__init__(parent, fg_color="transparent") 
        
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

        self.select_view_by_name("generar") # Inicia en Generar OT

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
        label = ctk.CTkLabel(frame, 
                             text=text, 
                             font=ctk.CTkFont(size=24, weight="bold"), 
                             text_color="#343638")
        label.pack(padx=20, pady=20)
        return frame

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

        # Make this frame expand to fill parent
        self.grid(row=0, column=0, sticky="nsew")
        try:
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(0, weight=1)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # 2. Creación del Marco de Navegación (Sidebar)
        # ------------------------------------------------------------------
        
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#343638") 
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(8, weight=1)

        # ------------------------------------------------------------------
        # 3. Elementos Fijos del Sidebar
        # ------------------------------------------------------------------
        
        self.title_label = ctk.CTkLabel(self.navigation_frame, 
                                        text="Plot Master", 
                                        font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.user_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        self.user_frame.grid(row=1, column=0, padx=10, pady=(10, 20), sticky="ew")
        self.user_label = ctk.CTkLabel(self.user_frame, 
                           text=f"👤  {self.user_name}", 
                           anchor="w",
                           font=ctk.CTkFont(size=14, weight="normal"))
        self.user_label.pack(fill="x")
        
        self.menu_separator = ctk.CTkLabel(self.navigation_frame, 
                                           text="MENÚ", 
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           text_color="gray50")
        self.menu_separator.grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")

        # ------------------------------------------------------------------
        # 4. Botones de Navegación (Pestañas)
        # ------------------------------------------------------------------

        def create_nav_button(row, text, command_name):
            return ctk.CTkButton(self.navigation_frame, 
                                 corner_radius=0, height=40, border_spacing=10, 
                                 text=text, fg_color="transparent", 
                                 text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                 anchor="w",
                                 command=lambda: self.select_frame_by_name(command_name))
                                 
        self.inicio_button = create_nav_button(3, "🏠  Inicio", "inicio")
        self.inicio_button.grid(row=3, column=0, sticky="ew")

        self.ordenes_button = create_nav_button(4, "📋  Órdenes de trabajo", "ordenes")
        self.ordenes_button.grid(row=4, column=0, sticky="ew")

        self.clientes_button = create_nav_button(5, "👤  Clientes", "clientes")
        self.clientes_button.grid(row=5, column=0, sticky="ew")

        self.reportes_button = create_nav_button(6, "📊  Reportes", "reportes")
        self.reportes_button.grid(row=6, column=0, sticky="ew")

        self.acceso_button = create_nav_button(7, "⚙️  Administrar Accesos", "acceso")
        self.acceso_button.grid(row=7, column=0, sticky="ew")
        
        # ------------------------------------------------------------------
        # 5. Marcos de Contenido (Módulos) - ¡Conexión!
        # ------------------------------------------------------------------
        
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#F7F7F7") 
        self.main_content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # Instanciamos los marcos, utilizando la clase OrdenesFrame que tiene las subpestañas
        self.inicio_frame = self._create_module_frame("Módulo de Inicio")
        self.clientes_frame = self._create_module_frame("Módulo: Clientes")
        self.reportes_frame = self._create_module_frame("Módulo: Reportes")
        self.acceso_frame = self._create_module_frame("Módulo: Administrar Accesos")
        
        # INSTANCIAMOS EL MÓDULO CON SUBPESTAÑAS
        self.ordenes_frame = OrdenesFrame(self.main_content_frame) # <-- ¡Conexión Directa!

        # ------------------------------------------------------------------
        # 6. Inicialización y Lógica de Pestañas
        # ------------------------------------------------------------------
        
        self.select_frame_by_name("ordenes") # Inicia en "Órdenes de trabajo"

    def _create_module_frame(self, text):
        # Función para crear módulos genéricos
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        label = ctk.CTkLabel(frame, 
                             text=text, 
                             font=ctk.CTkFont(size=30, weight="bold"), 
                             text_color="#343638")
        label.pack(padx=50, pady=50)
        return frame

    def select_frame_by_name(self, name):
        # Lógica de navegación principal (sidebar)
        
        buttons = [self.inicio_button, self.ordenes_button, self.clientes_button, self.reportes_button, self.acceso_button]
        for button in buttons:
            button.configure(fg_color="transparent")

        frames = [self.inicio_frame, self.ordenes_frame, self.clientes_frame, self.reportes_frame, self.acceso_frame]
        for frame in frames:
            frame.grid_forget()

        active_color = ("#69B5F9", "#0086E2") 
        
        if name == "inicio":
            self.inicio_button.configure(fg_color=active_color)
            self.inicio_frame.grid(row=0, column=0, sticky="nsew")
        
        elif name == "ordenes":
            self.ordenes_button.configure(fg_color=active_color)
            self.ordenes_frame.grid(row=0, column=0, sticky="nsew")
            
        elif name == "clientes":
            self.clientes_button.configure(fg_color=active_color)
            self.clientes_frame.grid(row=0, column=0, sticky="nsew")
        
        elif name == "reportes":
            self.reportes_button.configure(fg_color=active_color)
            self.reportes_frame.grid(row=0, column=0, sticky="nsew")

        elif name == "acceso":
            self.acceso_button.configure(fg_color=active_color)
            self.acceso_frame.grid(row=0, column=0, sticky="nsew")


# --------------------------------------------------------------------------
# 7. Ejecución
# --------------------------------------------------------------------------

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark") 
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()