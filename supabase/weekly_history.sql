-- ==========================================================================
-- THIAN-CORE // WEEKLY HISTORY & XP RESET
-- Ejecutar completo en: Supabase Dashboard > SQL Editor > New query
-- ==========================================================================

create extension if not exists pgcrypto;

-- --------------------------------------------------------------------------
-- 1. TABLA PRINCIPAL
-- --------------------------------------------------------------------------
create table if not exists public.weekly_history (
    id uuid primary key default gen_random_uuid(),
    user_id text not null default 'thian-core',
    week_start_date date not null,
    week_end_date date not null,
    total_tasks integer not null default 0,
    completed_tasks integer not null default 0,
    xp_earned integer not null default 0,
    effectiveness_percentage numeric(5, 2) not null default 0.00,
    status text not null default 'completed',
    -- Metadatos extra usados por el reporte visual de Thian-Core
    breakdown jsonb not null default '{}'::jsonb,
    source text not null default 'manual',
    closed_at timestamptz not null default now(),
    created_at timestamptz not null default now(),

    constraint weekly_history_status_check
        check (status in ('completed', 'reset')),
    constraint weekly_history_dates_check
        check (week_end_date >= week_start_date),
    constraint weekly_history_counts_check
        check (total_tasks >= 0 and completed_tasks >= 0),
    constraint weekly_history_completed_check
        check (completed_tasks <= total_tasks),
    constraint weekly_history_effectiveness_check
        check (
            effectiveness_percentage >= 0
            and effectiveness_percentage <= 100
        ),
    constraint weekly_history_user_week_unique
        unique (user_id, week_start_date)
);

-- --------------------------------------------------------------------------
-- 2. ÍNDICES
-- --------------------------------------------------------------------------
create index if not exists idx_weekly_history_user_week
    on public.weekly_history (user_id, week_start_date desc);

create index if not exists idx_weekly_history_status
    on public.weekly_history (status);

-- --------------------------------------------------------------------------
-- 3. CÁLCULO AUTOMÁTICO DE EFECTIVIDAD
-- --------------------------------------------------------------------------
create or replace function public.calculate_weekly_effectiveness()
returns trigger
language plpgsql
as $$
begin
    -- Si por alguna razón llegan más completadas que el total, corregimos.
    if new.completed_tasks > new.total_tasks then
        new.total_tasks := new.completed_tasks;
    end if;

    if new.total_tasks > 0 then
        new.effectiveness_percentage := round(
            (new.completed_tasks::numeric / new.total_tasks::numeric) * 100,
            2
        );
    else
        new.effectiveness_percentage := 0.00;
    end if;

    return new;
end;
$$;

drop trigger if exists trg_weekly_history_effectiveness
    on public.weekly_history;

create trigger trg_weekly_history_effectiveness
before insert or update on public.weekly_history
for each row
execute function public.calculate_weekly_effectiveness();

-- --------------------------------------------------------------------------
-- 4. CÁLCULO DE XP (MISMA ECONOMÍA QUE EL DASHBOARD)
--    +25 XP por tarea de Estudios / Rygon
--    +50 XP por hábito diario completado
-- --------------------------------------------------------------------------
create or replace function public.calculate_weekly_xp(
    p_completed_tasks integer,
    p_completed_habits integer default 0,
    p_xp_per_task integer default 25,
    p_xp_per_habit integer default 50
)
returns integer
language sql
immutable
as $$
    select
        greatest(coalesce(p_completed_tasks, 0), 0) * greatest(p_xp_per_task, 0)
        + greatest(coalesce(p_completed_habits, 0), 0) * greatest(p_xp_per_habit, 0);
$$;

-- --------------------------------------------------------------------------
-- 5. RPC DE CIERRE SEMANAL (UPSERT IDEMPOTENTE)
--    El backend de Thian-Core calcula las métricas desde Obsidian y llama
--    a esta función para guardar el registro definitivo en Supabase.
-- --------------------------------------------------------------------------
create or replace function public.close_weekly_cycle(
    p_user_id text,
    p_week_start date,
    p_week_end date,
    p_total_tasks integer,
    p_completed_tasks integer,
    p_xp_earned integer,
    p_status text default 'completed',
    p_breakdown jsonb default '{}'::jsonb,
    p_source text default 'manual'
)
returns public.weekly_history
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_row public.weekly_history;
begin
    if p_status not in ('completed', 'reset') then
        raise exception 'status inválido: %. Usa completed o reset.', p_status;
    end if;

    if p_week_end < p_week_start then
        raise exception 'week_end_date no puede ser menor que week_start_date.';
    end if;

    insert into public.weekly_history (
        user_id,
        week_start_date,
        week_end_date,
        total_tasks,
        completed_tasks,
        xp_earned,
        status,
        breakdown,
        source,
        closed_at
    )
    values (
        coalesce(nullif(p_user_id, ''), 'thian-core'),
        p_week_start,
        p_week_end,
        greatest(coalesce(p_total_tasks, 0), 0),
        greatest(coalesce(p_completed_tasks, 0), 0),
        greatest(coalesce(p_xp_earned, 0), 0),
        p_status,
        coalesce(p_breakdown, '{}'::jsonb),
        coalesce(nullif(p_source, ''), 'manual'),
        now()
    )
    on conflict (user_id, week_start_date)
    do update set
        week_end_date = excluded.week_end_date,
        total_tasks = excluded.total_tasks,
        completed_tasks = excluded.completed_tasks,
        xp_earned = excluded.xp_earned,
        status = excluded.status,
        breakdown = excluded.breakdown,
        source = excluded.source,
        closed_at = now()
    returning * into v_row;

    return v_row;
end;
$$;

-- --------------------------------------------------------------------------
-- 6. VISTA DE AGREGADOS PARA EL DASHBOARD
-- --------------------------------------------------------------------------
create or replace view public.weekly_history_summary
with (security_invoker = true) as
select
    user_id,
    count(*)::integer as total_weeks,
    coalesce(sum(xp_earned), 0)::integer as total_xp,
    round(avg(effectiveness_percentage), 2) as avg_effectiveness,
    max(effectiveness_percentage) as best_effectiveness,
    coalesce(sum(completed_tasks), 0)::integer as total_completed,
    coalesce(sum(total_tasks), 0)::integer as total_tasks
from public.weekly_history
group by user_id;

-- --------------------------------------------------------------------------
-- 7. SEGURIDAD (RLS)
--    Thian-Core es un dashboard personal single-user. Estas políticas
--    permiten leer/escribir con la publishable/anon key desde el backend.
--
--    ⚠️ PRODUCCIÓN MULTI-USUARIO:
--    Reemplaza `using (true)` por `using (auth.uid()::text = user_id)`
--    y usa SUPABASE_SERVICE_ROLE_KEY solo en el servidor.
-- --------------------------------------------------------------------------
alter table public.weekly_history enable row level security;

drop policy if exists "weekly_history_read" on public.weekly_history;
create policy "weekly_history_read"
    on public.weekly_history
    for select
    using (true);

drop policy if exists "weekly_history_insert" on public.weekly_history;
create policy "weekly_history_insert"
    on public.weekly_history
    for insert
    with check (true);

drop policy if exists "weekly_history_update" on public.weekly_history;
create policy "weekly_history_update"
    on public.weekly_history
    for update
    using (true)
    with check (true);

drop policy if exists "weekly_history_delete" on public.weekly_history;
create policy "weekly_history_delete"
    on public.weekly_history
    for delete
    using (true);

grant select, insert, update, delete
    on public.weekly_history
    to anon, authenticated;

grant select on public.weekly_history_summary
    to anon, authenticated;

grant execute on function public.calculate_weekly_xp(integer, integer, integer, integer)
    to anon, authenticated;

grant execute on function public.close_weekly_cycle(
    text, date, date, integer, integer, integer, text, jsonb, text
) to anon, authenticated;

-- --------------------------------------------------------------------------
-- 8. EJEMPLO DE USO MANUAL (opcional)
-- --------------------------------------------------------------------------
-- select public.close_weekly_cycle(
--     'thian-core',
--     '2026-11-02',
--     '2026-11-08',
--     40,
--     34,
--     public.calculate_weekly_xp(30, 4),
--     'completed',
--     '{"estudios":{"total":20,"completed":18,"xp":450},
--       "rygon":{"total":10,"completed":8,"xp":200},
--       "rutinas":{"total":10,"completed":8,"xp":400}}'::jsonb,
--     'manual'
-- );
