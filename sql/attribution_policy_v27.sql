-- Run once in SQL Editor after the v2.4 migration.
begin;
alter table public.portfolio_db add column if not exists attribution_benchmark_policy jsonb;
create or replace function public.invalidate_performance_attribution()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  if new.ledger_data::jsonb is distinct from old.ledger_data::jsonb
    or new.history_data::jsonb is distinct from old.history_data::jsonb
    or new.attribution_benchmark_policy is distinct from old.attribution_benchmark_policy then
    new.performance_attribution := null;
  end if;
  return new;
end;
$$;
-- CAS includes the policy so concurrent approvals cannot publish a stale report.
create or replace function public.publish_performance_attribution_v27(
  p_row_id bigint,p_ledger jsonb,p_history jsonb,p_policy jsonb,p_report jsonb
) returns boolean language plpgsql security invoker set search_path = ''
as $$
declare changed integer;
begin
  update public.portfolio_db set performance_attribution=p_report
  where id=p_row_id and ledger_data::jsonb is not distinct from p_ledger
    and history_data::jsonb is not distinct from p_history
    and attribution_benchmark_policy is not distinct from p_policy;
  get diagnostics changed=row_count;
  return changed=1;
end;
$$;
revoke all on function public.publish_performance_attribution_v27(bigint,jsonb,jsonb,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.publish_performance_attribution_v27(bigint,jsonb,jsonb,jsonb,jsonb) to service_role;
commit;
notify pgrst,'reload schema';
