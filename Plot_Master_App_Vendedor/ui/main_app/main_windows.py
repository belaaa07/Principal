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
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # 1. Creación del Header
        # ------------------------------------------------------------------
        # Header con color suave inspirado en la referencia
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#3b2b5b", height=50)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self.header_frame,
                text="Ordenes de Trabajo",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="white")
        self.title_label.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        self.user_label = ctk.CTkLabel(self.header_frame,
                   text=f"👤  {self.user_name}",
                   anchor="e",
                   font=ctk.CTkFont(size=13, weight="normal"),
                   text_color="white")
        self.user_label.grid(row=0, column=1, padx=20, sticky="e")

        # ------------------------------------------------------------------
        # 2. Creación del Marco de Navegación (Sidebar)
        # ------------------------------------------------------------------
        
        # Sidebar visual inspirado en la referencia HTML
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#2b2540")
        self.navigation_frame.grid(row=1, column=0, sticky="ns")
        self.navigation_frame.grid_rowconfigure(12, weight=1)

        # ------------------------------------------------------------------
        # 3. Elementos Fijos del Sidebar
        # ------------------------------------------------------------------

        # Helper para crear botones del nav (definida antes de su uso)
        def create_nav_button(row, text, command_name):
            return ctk.CTkButton(self.navigation_frame,
                                 corner_radius=6, height=44,
                                 text=text, fg_color="transparent",
                                 text_color=("#F5F3FB", "#F5F3FB"), hover_color=("#3f2f66", "#3f2f66"),
                                 anchor="w",
                                 command=lambda: self.select_frame_by_name(command_name))

        # Botón Inicio eliminado por cambio de flujo (visual mantenido en ambas apps)

        # SECCIÓN: OTS (solo las dos entradas requeridas)
        ctk.CTkLabel(self.navigation_frame, text="OTS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#DAD7E6").grid(row=2, column=0, padx=16, pady=(12,8), sticky="w")

        self.ordenes_button = create_nav_button(3, "📋  Generar OT", "ordenes")
        self.ordenes_button.grid(row=3, column=0, sticky="ew", padx=10, pady=(6,4))

        self.ordenes_list_button = create_nav_button(4, "📈  Planilla OT", "ordenes_list")
        self.ordenes_list_button.grid(row=4, column=0, sticky="ew", padx=10)

        # ------------------------------------------------------------------
        # 5. Marcos de Contenido (Módulos) - ¡Conexión!
        # ------------------------------------------------------------------
        
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#F7F7F7") 
        self.main_content_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
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
        # Inicia mostrando el módulo de Generar OT
        self.select_frame_by_name("ordenes")

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

    def _show_ordenes(self):
        self._clear_central()
        crear_modulo_ot_embedded(parent=self.central_container, vendedor=self.user_name)

    def _show_ordenes_list(self):
        self._clear_central()
        from ..modules.work_orders_list.ot_registration_list import ModuloOTs
        self.central_container.grid_columnconfigure(0, weight=1)
        ordenes_list_frame = ModuloOTs(self.central_container, vendedor=self.user_name)
        ordenes_list_frame.grid(row=0, column=0, sticky="nsew")

    def select_frame_by_name(self, name):
        # Lógica de navegación principal (sidebar)
        # Limpiar estado de los botones presentes (defensivo si alguno fue removido)
        buttons = [getattr(self, 'inicio_button', None), getattr(self, 'ordenes_button', None), getattr(self, 'ordenes_list_button', None)]
        for button in buttons:
            try:
                if button:
                    button.configure(fg_color="transparent")
            except Exception:
                pass

        active_color = ("#69B5F9", "#0086E2")

        if name == "inicio":
            # Inicio eliminado — mostrar módulo Generar OT por defecto
            self._show_ordenes()
        elif name == "ordenes":
            self.ordenes_button.configure(fg_color=active_color)
            self._show_ordenes()
        elif name == "ordenes_list":
            self.ordenes_list_button.configure(fg_color=active_color)
            self._show_ordenes_list()


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