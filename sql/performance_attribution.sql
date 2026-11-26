-- Run once in Supabase SQL Editor before running the private workflow.
-- Existing portfolio_db RLS governs reads, as with the ledger itself.
begin;
alter table public.portfolio_db add column if not exists performance_attribution jsonb;

create or replace function public.invalidate_performance_attribution()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  if new.ledger_data::jsonb is distinct from old.ledger_data::jsonb
     or new.history_data::jsonb is distinct from old.history_data::jsonb then
    new.performance_attribution := null;
  end if;
  return new;
end;
$$;
drop trigger if exists invalidate_performance_attribution on public.portfolio_db;
create trigger invalidate_performance_attribution
before update on public.portfolio_db
for each row execute function public.invalidate_performance_attribution();

create or replace function public.publish_performance_attribution(
  p_row_id bigint, p_ledger jsonb, p_history jsonb, p_report jsonb
) returns boolean
language plpgsql security invoker set search_path = ''
as $$
declare changed integer;
begin
  update public.portfolio_db
  set performance_attribution = p_report
  where id = p_row_id
    and ledger_data::jsonb is not distinct from p_ledger
    and history_data::jsonb is not distinct from p_history;
  get diagnostics changed = row_count;
  return changed = 1;
end;
$$;
revoke all on function public.publish_performance_attribution(bigint,jsonb,jsonb,jsonb) from public, anon, authenticated;
grant execute on function public.publish_performance_attribution(bigint,jsonb,jsonb,jsonb) to service_role;
commit;
notify pgrst, 'reload schema';
