import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime, date

try:
    from tkcalendar import DateEntry  # Mejora UX si está disponible
except Exception:
    DateEntry = None

from services.supabase_service import get_finalized_work_orders_between


class ReporteMensualOT(ctk.CTkFrame):
    """Módulo para descargar reporte de OTs finalizadas en CSV compatible con Excel."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Reporte mensual de Órdenes Finalizadas",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        subtitle = ctk.CTkLabel(
            self,
            text="Descarga un CSV listo para Excel con las OTs en estado FINALIZADO en un rango de fechas.",
            font=ctk.CTkFont(size=13),
            text_color="#4b5563",
            wraplength=720,
            justify="left",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 12))

        card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        card.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure((0, 1), weight=1)

        # Fecha desde
        self.fecha_desde_widget = self._create_date_input(card, "Fecha desde", 0)
        # Fecha hasta
        self.fecha_hasta_widget = self._create_date_input(card, "Fecha hasta", 1)

        # Orden
        orden_frame = ctk.CTkFrame(card, fg_color="transparent")
        orden_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(orden_frame, text="Orden por fecha", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.orden_var = ctk.StringVar(value="desc")
        self.orden_picker = ctk.CTkSegmentedButton(orden_frame, values=["asc", "desc"], variable=self.orden_var)
        self.orden_picker.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(orden_frame, text="Desc: más recientes primero", font=ctk.CTkFont(size=11), text_color="#6b7280").pack(anchor="w", pady=(4, 0))

        # Botón descarga
        self.btn_descargar = ctk.CTkButton(
            card,
            text="📥 Descargar CSV",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._on_descargar,
            height=42,
            corner_radius=8,
        )
        self.btn_descargar.grid(row=1, column=0, columnspan=3, padx=10, pady=(4, 12), sticky="ew")

        # Estado
        self.status_label = ctk.CTkLabel(card, text="", text_color="#374151")
        self.status_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="w")

    def _create_date_input(self, parent, label, col):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(wrapper, text=label, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        if DateEntry:
            picker = DateEntry(wrapper, width=16, date_pattern='yyyy-mm-dd')
            picker.set_date(date.today())
        else:
            picker = ctk.CTkEntry(wrapper, placeholder_text="yyyy-mm-dd")
            picker.insert(0, date.today().isoformat())
        picker.pack(fill="x", pady=(6, 0))
        return picker

    def _parse_date(self, widget):
        if DateEntry and isinstance(widget, DateEntry):
            return widget.get_date()
        raw = widget.get().strip()
        return datetime.strptime(raw, "%Y-%m-%d").date()

    def _on_descargar(self):
        try:
            f_ini = self._parse_date(self.fecha_desde_widget)
            f_fin = self._parse_date(self.fecha_hasta_widget)
        except Exception:
            messagebox.showerror("Fechas inválidas", "Usa el formato yyyy-mm-dd para ambas fechas.")
            return

        if f_ini > f_fin:
            messagebox.showerror("Rango inválido", "La fecha inicial no puede ser mayor que la fecha final.")
            return

        sort_desc = self.orden_var.get() == "desc"
        self.status_label.configure(text="Consultando datos…")
        self.btn_descargar.configure(state="disabled")
        self.update_idletasks()

        ok, data = get_finalized_work_orders_between(f_ini, f_fin, sort_desc=sort_desc)
        if not ok:
            messagebox.showerror("Error", data)
            self.status_label.configure(text="")
            self.btn_descargar.configure(state="normal")
            return

        if not data:
            messagebox.showinfo("Sin datos", "No hay órdenes finalizadas en el rango indicado.")
            self.status_label.configure(text="")
            self.btn_descargar.configure(state="normal")
            return

        default_name = f"reporte_ot_{f_ini.isoformat()}_{f_fin.isoformat()}.csv"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not path:
            self.status_label.configure(text="Descarga cancelada.")
            self.btn_descargar.configure(state="normal")
            return

        try:
            self._write_csv(path, data)
            self.status_label.configure(text=f"Archivo guardado: {path}", text_color="#059669")
            messagebox.showinfo("Éxito", "Reporte CSV generado correctamente.")
        except Exception as e:
            messagebox.showerror("Error al escribir archivo", str(e))
            self.status_label.configure(text="No se pudo guardar el archivo.", text_color="#b91c1c")
        finally:
            self.btn_descargar.configure(state="normal")

    def _write_csv(self, path, rows):
        headers = [
            "ot_nro",
            "fecha_creacion",
            "cliente",
            "cliente_ci_ruc",
            "vendedor",
            "vendedor_ci_ruc",
            "descripcion",
            "valor_total",
            "abonado_total",
            "forma_pago",
            "solicita_envio",
            "fecha_entrega",
        ]
        with open(path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    'ot_nro': r.get('ot_nro'),
                    'fecha_creacion': r.get('fecha_creacion'),
                    'cliente': r.get('cliente'),
                    'cliente_ci_ruc': r.get('cliente_ci_ruc'),
                    'vendedor': r.get('vendedor'),
                    'vendedor_ci_ruc': r.get('vendedor_ci_ruc'),
                    'descripcion': r.get('descripcion'),
                    'valor_total': r.get('valor_total'),
                    'abonado_total': r.get('abonado_total'),
                    'forma_pago': r.get('forma_pago'),
                    'solicita_envio': 'Con Envío' if r.get('solicita_envio') else 'Sin Envío',
                    'fecha_entrega': r.get('fecha_entrega') or '',
                })
