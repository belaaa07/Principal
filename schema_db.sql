create table public.abonos (
  id bigserial not null,
  ot_id bigint not null,
  monto numeric(12, 2) not null,
  fecha_abono timestamp with time zone not null default now(),
  observacion text null,
  creado_por bigint null,
  constraint abonos_pkey primary key (id),
  constraint abonos_creado_por_fkey foreign KEY (creado_por) references administradores (id),
  constraint abonos_ot_id_fkey foreign KEY (ot_id) references ordenes_trabajo (id) on delete CASCADE,
  constraint abonos_monto_check check ((monto > (0)::numeric))
) TABLESPACE pg_default;

create table public.administradores (
  id bigserial not null,
  ci_ruc text not null,
  nombre text not null,
  email text null,
  password_hash text not null,
  salt text not null,
  estado public.estado_usuarios not null default 'activo'::estado_usuarios,
  fecha_registro timestamp with time zone not null default now(),
  constraint administradores_pkey primary key (id),
  constraint administradores_ci_ruc_key unique (ci_ruc)
) TABLESPACE pg_default;

create table public.clientes (
  id bigserial not null,
  nombre text not null,
  ci_ruc text not null,
  telefono text not null,
  zona public.ciudades_central null,
  email text null,
  created_at timestamp with time zone not null default now(),
  constraint clientes_pkey primary key (id),
  constraint clientes_ci_ruc_key unique (ci_ruc)
) TABLESPACE pg_default;

create table public.ordenes_trabajo (
  id bigserial not null,
  ot_nro integer not null,
  cliente_id bigint not null,
  vendedor_id bigint not null,
  descripcion text null,
  valor_total numeric(12, 2) not null,
  sena numeric(12, 2) not null default 0,
  abonado_total numeric(12, 2) not null default 0,
  forma_pago public.forma_pagos not null,
  solicita_envio boolean not null default false,
  status public.ordenes_estados not null default 'Pendiente'::ordenes_estados,
  fecha_creacion date not null,
  fecha_entrega date null,
  aprobado_por bigint null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint ordenes_trabajo_pkey primary key (id),
  constraint ordenes_trabajo_ot_nro_key unique (ot_nro),
  constraint ordenes_trabajo_aprobado_por_fkey foreign KEY (aprobado_por) references administradores (id),
  constraint ordenes_trabajo_cliente_id_fkey foreign KEY (cliente_id) references clientes (id) on delete CASCADE,
  constraint ordenes_trabajo_vendedor_id_fkey foreign KEY (vendedor_id) references usuarios (id)
) TABLESPACE pg_default;

create table public.usuarios (
  id bigserial not null,
  ci_ruc text not null,
  nombre text not null,
  email text null,
  password_hash text not null,
  salt text not null,
  estado public.estado_usuarios not null default 'activo'::estado_usuarios,
  fecha_registro timestamp with time zone not null default now(),
  constraint usuarios_pkey primary key (id),
  constraint usuarios_ci_ruc_key unique (ci_ruc)
) TABLESPACE pg_default;