-- ============================================
-- DUMP DDL del esquema "public"
-- Incluye: tipos ENUM, secuencias, tablas, constraints, índices, defaults, RLS enabled flags y comentarios cuando aplica.
-- Generado para uso como contexto en Copilot.
-- Revise antes de ejecutar en un entorno de producción.
-- ============================================

-- =========================
-- ENUMS / TIPOS USER-DEFINED
-- =========================

-- Tipo: ciudades_central (usado en clientes.zona)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ciudades_central') THEN
    CREATE TYPE public.ciudades_central AS ENUM (
      'Areguá','Asunción','Capiatá','Fernando de la Mora','Guarambaré','Itá','Itauguá',
      'J. Augusto Saldívar','Lambaré','Limpio','Luque','Mariano Roque Alonso','Nueva Italia',
      'Ñemby','San Antonio','San Lorenzo','Villa Elisa','Villeta','Ypané','Ypacaraí','Otro'
    );
  END IF;
END$$;

-- Tipo: estado_usuarios (usado en usuarios.estado y administradores.estado)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_usuarios') THEN
    CREATE TYPE public.estado_usuarios AS ENUM ('activo','inactivo');
  END IF;
END$$;

-- Tipo: forma_pagos (usado en ordenes_trabajo.forma_pago)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'forma_pagos') THEN
    CREATE TYPE public.forma_pagos AS ENUM ('Crédito','Contado');
  END IF;
END$$;

-- Tipo: ordenes_estados (usado en ordenes_trabajo.status y cancelaciones.estado_anterior)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ordenes_estados') THEN
    CREATE TYPE public.ordenes_estados AS ENUM ('Rechazado','Pendiente','Aprobado','Entregado','Finalizado','Cancelado');
  END IF;
END$$;

-- =========================
-- SECUENCIAS (si aplica)
-- =========================
-- NOTA: Las secuencias se crean implícitamente cuando se usa nextval en default_value. Creamos explícitamente para compatibilidad.

CREATE SEQUENCE IF NOT EXISTS public.usuarios_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.administradores_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.clientes_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.ordenes_trabajo_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.abonos_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.historial_cancelaciones_ot_id_seq;

-- =========================
-- TABLAS
-- =========================

-- Tabla: usuarios
CREATE TABLE IF NOT EXISTS public.usuarios (
  id bigint DEFAULT nextval('public.usuarios_id_seq'::regclass) PRIMARY KEY,
  ci_ruc text UNIQUE NOT NULL,
  nombre text NOT NULL,
  email text,
  password_hash text NOT NULL,
  salt text NOT NULL,
  estado public.estado_usuarios NOT NULL DEFAULT 'activo',
  fecha_registro timestamptz NOT NULL DEFAULT now()
);

-- Tabla: administradores
CREATE TABLE IF NOT EXISTS public.administradores (
  id bigint DEFAULT nextval('public.administradores_id_seq'::regclass) PRIMARY KEY,
  ci_ruc text UNIQUE NOT NULL,
  nombre text NOT NULL,
  email text,
  password_hash text NOT NULL,
  salt text NOT NULL,
  estado public.estado_usuarios NOT NULL DEFAULT 'activo',
  fecha_registro timestamptz NOT NULL DEFAULT now()
);

-- Tabla: clientes
CREATE TABLE IF NOT EXISTS public.clientes (
  id bigint DEFAULT nextval('public.clientes_id_seq'::regclass) PRIMARY KEY,
  nombre text NOT NULL,
  ci_ruc text UNIQUE NOT NULL,
  telefono text NOT NULL,
  zona public.ciudades_central,
  email text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Tabla: ordenes_trabajo
CREATE TABLE IF NOT EXISTS public.ordenes_trabajo (
  id bigint DEFAULT nextval('public.ordenes_trabajo_id_seq'::regclass) PRIMARY KEY,
  ot_nro integer UNIQUE NOT NULL,
  cliente_id bigint NOT NULL,
  vendedor_id bigint NOT NULL,
  descripcion text,
  valor_total numeric NOT NULL,
  sena numeric NOT NULL DEFAULT 0,
  abonado_total numeric NOT NULL DEFAULT 0,
  forma_pago public.forma_pagos,
  solicita_envio boolean NOT NULL DEFAULT false,
  status public.ordenes_estados NOT NULL DEFAULT 'Pendiente',
  fecha_creacion date NOT NULL,
  fecha_entrega date,
  aprobado_por bigint,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Tabla: abonos
CREATE TABLE IF NOT EXISTS public.abonos (
  id bigint DEFAULT nextval('public.abonos_id_seq'::regclass) PRIMARY KEY,
  ot_id bigint NOT NULL,
  monto numeric NOT NULL CHECK (monto > 0),
  fecha_abono timestamptz NOT NULL DEFAULT now(),
  observacion text,
  creado_por bigint
);

-- Tabla: cancelaciones (historial_cancelaciones_ot)
CREATE TABLE IF NOT EXISTS public.cancelaciones (
  id bigint DEFAULT nextval('public.historial_cancelaciones_ot_id_seq'::regclass) PRIMARY KEY,
  ot_id bigint NOT NULL,
  cliente_id bigint NOT NULL,
  vendedor_id bigint NOT NULL,
  descripcion text,
  estado_anterior public.ordenes_estados,
  cancelado_por bigint,
  fecha_creacion_ot timestamptz,
  fecha_cancelacion timestamptz NOT NULL DEFAULT now(),
  motivo text,
  reembolso numeric NOT NULL DEFAULT 0
);

-- Tabla: pending_work_orders (nueva)
CREATE TABLE IF NOT EXISTS public.pending_work_orders (
  id BIGSERIAL PRIMARY KEY,
  ot_id INTEGER NOT NULL,
  fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
  vendedor TEXT,
  monto_total NUMERIC(12,2) NOT NULL CHECK (monto_total >= 0),
  monto_abonado NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (monto_abonado >= 0),
  estado TEXT NOT NULL DEFAULT 'pendiente',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================
-- CONSTRAINTS / FOREIGN KEYS
-- =========================

-- Foreign keys: ordenes_trabajo -> clientes, usuarios, administradores
ALTER TABLE IF EXISTS public.ordenes_trabajo
  ADD CONSTRAINT IF NOT EXISTS ordenes_trabajo_cliente_id_fkey
    FOREIGN KEY (cliente_id) REFERENCES public.clientes (id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE IF EXISTS public.ordenes_trabajo
  ADD CONSTRAINT IF NOT EXISTS ordenes_trabajo_vendedor_id_fkey
    FOREIGN KEY (vendedor_id) REFERENCES public.usuarios (id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE IF EXISTS public.ordenes_trabajo
  ADD CONSTRAINT IF NOT EXISTS ordenes_trabajo_aprobado_por_fkey
    FOREIGN KEY (aprobado_por) REFERENCES public.administradores (id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Foreign keys: abonos -> ordenes_trabajo, administradores
ALTER TABLE IF EXISTS public.abonos
  ADD CONSTRAINT IF NOT EXISTS abonos_ot_id_fkey
    FOREIGN KEY (ot_id) REFERENCES public.ordenes_trabajo (id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE IF EXISTS public.abonos
  ADD CONSTRAINT IF NOT EXISTS abonos_creado_por_fkey
    FOREIGN KEY (creado_por) REFERENCES public.administradores (id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Foreign keys: cancelaciones -> ordenes_trabajo, clientes, usuarios, administradores
ALTER TABLE IF EXISTS public.cancelaciones
  ADD CONSTRAINT IF NOT EXISTS historial_cancelaciones_ot_ot_fkey
    FOREIGN KEY (ot_id) REFERENCES public.ordenes_trabajo (id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE IF EXISTS public.cancelaciones
  ADD CONSTRAINT IF NOT EXISTS historial_cancelaciones_ot_cliente_fkey
    FOREIGN KEY (cliente_id) REFERENCES public.clientes (id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE IF EXISTS public.cancelaciones
  ADD CONSTRAINT IF NOT EXISTS historial_cancelaciones_ot_vendedor_fkey
    FOREIGN KEY (vendedor_id) REFERENCES public.usuarios (id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE IF EXISTS public.cancelaciones
  ADD CONSTRAINT IF NOT EXISTS historial_cancelaciones_ot_admin_fkey
    FOREIGN KEY (cancelado_por) REFERENCES public.administradores (id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Foreign keys: usuarios/administradores referenced by other tables already above (added where relevant)

-- Foreign key: pending_work_orders -> ordenes_trabajo (por ot_nro)
-- Nota: ordenes_trabajo.ot_nro es UNIQUE integer; acá referenciamos esa columna.
ALTER TABLE IF EXISTS public.pending_work_orders
  ADD CONSTRAINT IF NOT EXISTS fk_pending_ot
    FOREIGN KEY (ot_id) REFERENCES public.ordenes_trabajo (ot_nro) ON UPDATE CASCADE ON DELETE RESTRICT;

-- =========================
-- ÍNDICES
-- =========================

-- Usuarios
CREATE INDEX IF NOT EXISTS idx_usuarios_ci_ruc ON public.usuarios (ci_ruc);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON public.usuarios (email);

-- Administradores
CREATE INDEX IF NOT EXISTS idx_administradores_ci_ruc ON public.administradores (ci_ruc);

-- Clientes
CREATE INDEX IF NOT EXISTS idx_clientes_ci_ruc ON public.clientes (ci_ruc);
CREATE INDEX IF NOT EXISTS idx_clientes_zona ON public.clientes (zona);

-- Ordenes de trabajo
CREATE INDEX IF NOT EXISTS idx_ordenes_trabajo_ot_nro ON public.ordenes_trabajo (ot_nro);
CREATE INDEX IF NOT EXISTS idx_ordenes_trabajo_cliente_id ON public.ordenes_trabajo (cliente_id);
CREATE INDEX IF NOT EXISTS idx_ordenes_trabajo_vendedor_id ON public.ordenes_trabajo (vendedor_id);
CREATE INDEX IF NOT EXISTS idx_ordenes_trabajo_status ON public.ordenes_trabajo (status);
CREATE INDEX IF NOT EXISTS idx_ordenes_trabajo_fecha_creacion ON public.ordenes_trabajo (fecha_creacion);

-- Abonos
CREATE INDEX IF NOT EXISTS idx_abonos_ot_id ON public.abonos (ot_id);
CREATE INDEX IF NOT EXISTS idx_abonos_creado_por ON public.abonos (creado_por);
CREATE INDEX IF NOT EXISTS idx_abonos_fecha_abono ON public.abonos (fecha_abono);

-- Cancelaciones
CREATE INDEX IF NOT EXISTS idx_cancelaciones_ot_id ON public.cancelaciones (ot_id);
CREATE INDEX IF NOT EXISTS idx_cancelaciones_fecha_cancelacion ON public.cancelaciones (fecha_cancelacion);

-- Pending Work Orders (nueva)
CREATE INDEX IF NOT EXISTS idx_pending_work_orders_ot_id ON public.pending_work_orders (ot_id);
CREATE INDEX IF NOT EXISTS idx_pending_work_orders_vendedor_estado ON public.pending_work_orders (vendedor, estado);
CREATE INDEX IF NOT EXISTS idx_pending_work_orders_estado ON public.pending_work_orders (estado);
CREATE INDEX IF NOT EXISTS idx_pending_work_orders_created_at ON public.pending_work_orders (created_at);
CREATE INDEX IF NOT EXISTS idx_pending_work_orders_monto_abonado ON public.pending_work_orders (monto_abonado);

-- =========================
-- RLS (Row Level Security) FLAGS
-- =========================

-- Marcar tablas con RLS habilitado según estado detectado
-- (No se habilita RLS automáticamente aquí; esto deja constancia que deben activarse/ya están activas.)
-- Habilite RLS según su política de seguridad:
-- ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.administradores ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.clientes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.ordenes_trabajo ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.abonos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.cancelaciones ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.pending_work_orders ENABLE ROW LEVEL SECURITY;

-- =========================
-- EJEMPLOS/EXTRAS: POLÍTICAS RLS DETECTADAS (esqueleto)
-- =========================

-- Nota: Se incluyeron las tablas que tienen RLS habilitado en su entorno. A continuación se dan ejemplos de políticas
-- que podrían existir o que puede querer añadir; **ajústelas según sus reglas de negocio**.

-- Ejemplo: permitir SELECT a usuarios autenticados sobre ordenes_trabajo si son vendedor o admin
-- CREATE POLICY "ordenes_vendedor_o_admin_select" ON public.ordenes_trabajo
--   FOR SELECT TO authenticated
--   USING (
--     vendedor_id = (SELECT (auth.uid())::bigint) OR (auth.jwt() ->> 'role') = 'admin'
--   );

-- Ejemplo: permitir INSERT de abonos solo si el usuario es admin o lo crea un administrador
-- CREATE POLICY "abonos_crear_admin" ON public.abonos
--   FOR INSERT TO authenticated
--   WITH CHECK (
--     (auth.jwt() ->> 'role') = 'admin' OR creado_por = (SELECT (auth.uid())::bigint)
--   );

-- Ejemplo: políticas para pending_work_orders (personalizar)
-- CREATE POLICY "pending_select_vendedor" ON public.pending_work_orders
--   FOR SELECT TO authenticated
--   USING (
--     vendedor IS NOT DISTINCT FROM (auth.uid())::text OR (auth.jwt() ->> 'role') = 'admin'
--   );

-- CREATE POLICY "pending_modify_vendedor" ON public.pending_work_orders
--   FOR UPDATE, DELETE TO authenticated
--   USING (
--     vendedor IS NOT DISTINCT FROM (auth.uid())::text OR (auth.jwt() ->> 'role') = 'admin'
--   )
--   WITH CHECK (
--     vendedor IS NOT DISTINCT FROM (auth.uid())::text OR (auth.jwt() ->> 'role') = 'admin'
--   );

-- =========================
-- TRIGGERS (si los hubiera)
-- =========================

-- Nota: No se detectaron triggers en el resumen proporcionado. Si tiene triggers (ej. para actualizar updated_at),
-- agréguelos aquí. Ejemplo de trigger para actualizar updated_at en ordenes_trabajo:

-- CREATE OR REPLACE FUNCTION public.update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--   NEW.updated_at = now();
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- CREATE TRIGGER trg_ordenes_update_updated_at
--   BEFORE UPDATE ON public.ordenes_trabajo
--   FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();