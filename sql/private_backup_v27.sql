-- Run after sql/attribution_policy_v27.sql. Private bucket; never make public.
begin;
insert into storage.buckets(id,name,public)
values ('portfolio-private-backups','portfolio-private-backups',false)
on conflict(id) do nothing;
do $$
begin
  if not exists(select 1 from storage.buckets where id='portfolio-private-backups' and public is false)
  then raise exception 'Backup bucket must be private'; end if;
end;
$$;

-- Recovery is restricted to an existing EMPTY target row. No destructive
-- restore of live portfolio, no rewriting immutable snapshots.
create or replace function public.restore_empty_portfolio_v27(p_row_id bigint,p_data jsonb)
returns boolean language plpgsql security invoker set search_path=''
as $$
declare changed integer;
begin
  if jsonb_typeof(p_data) is distinct from 'object'
     or p_data->>'id' is distinct from p_row_id::text
     or jsonb_typeof(p_data->'ledger_data') is distinct from 'array'
     or jsonb_typeof(p_data->'history_data') is distinct from 'array'
     or jsonb_typeof(p_data->'stock_meta') is distinct from 'object'
     or jsonb_typeof(p_data->'settings') is distinct from 'object'
     or not (p_data ? 'attribution_benchmark_policy')
     or jsonb_typeof(p_data->'attribution_benchmark_policy') not in ('object','null')
  then return false; end if;
  if jsonb_array_length(p_data->'ledger_data')=0 or jsonb_array_length(p_data->'history_data')=0 then return false; end if;
  update public.portfolio_db set
    ledger_data=p_data->'ledger_data',
    history_data=p_data->'history_data',
    stock_meta=p_data->'stock_meta',
    settings=p_data->'settings',
    attribution_benchmark_policy=nullif(p_data->'attribution_benchmark_policy','null'::jsonb),
    performance_attribution=null
  where id=p_row_id
    and (ledger_data is null or ledger_data::jsonb in ('[]'::jsonb,'null'::jsonb))
    and (history_data is null or history_data::jsonb in ('[]'::jsonb,'null'::jsonb))
    and (stock_meta is null or stock_meta::jsonb in ('{}'::jsonb,'null'::jsonb))
    and (settings is null or settings::jsonb in ('{}'::jsonb,'null'::jsonb))
    and attribution_benchmark_policy is null;
  get diagnostics changed=row_count;
  return changed=1;
end;
$$;
revoke all on function public.restore_empty_portfolio_v27(bigint,jsonb) from public,anon,authenticated;
grant execute on function public.restore_empty_portfolio_v27(bigint,jsonb) to service_role;
commit;
notify pgrst,'reload schema';
