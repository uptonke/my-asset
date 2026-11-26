-- Run after sql/performance_attribution.sql; no history backfill or replacement.
begin;
create or replace function public.protect_automated_nav()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  -- Preserve exact automated rows even when a stale browser upserts a
  -- previously loaded history array. Fail the whole write, never silently merge.
  if exists (
    select 1 from jsonb_array_elements(coalesce(old.history_data::jsonb,'[]'::jsonb)) h
    where h->'valuation'->>'capture_mode'='automated_completed_daily_marks'
      and (select count(*) from jsonb_array_elements(coalesce(new.history_data::jsonb,'[]'::jsonb)) n
           where n->>'date'=h->>'date')<>1
  ) or exists (
    select 1 from jsonb_array_elements(coalesce(old.history_data::jsonb,'[]'::jsonb)) h
    where h->'valuation'->>'capture_mode'='automated_completed_daily_marks'
      and not exists (select 1 from jsonb_array_elements(coalesce(new.history_data::jsonb,'[]'::jsonb)) n where n=h)
  ) then
    raise exception 'Automated NAV is immutable; reload latest history before saving';
  end if;
  if current_user not in ('service_role','postgres','supabase_admin') and exists (
    select 1 from jsonb_array_elements(coalesce(new.history_data::jsonb,'[]'::jsonb)) n
    where n->'valuation'->>'capture_mode'='automated_completed_daily_marks'
      and not exists (select 1 from jsonb_array_elements(coalesce(old.history_data::jsonb,'[]'::jsonb)) h where h=n)
  ) then
    raise exception 'Automated NAV may only be appended by server';
  end if;
  return new;
end;
$$;
drop trigger if exists protect_automated_nav on public.portfolio_db;
create trigger protect_automated_nav before update on public.portfolio_db
for each row execute function public.protect_automated_nav();

create or replace function public.append_automated_nav(
  p_row_id bigint,p_ledger jsonb,p_history jsonb,p_record jsonb
) returns boolean language plpgsql security invoker set search_path = ''
as $$
declare changed integer;
begin
  if jsonb_typeof(p_record) is distinct from 'object'
    or p_record->>'date' is distinct from (timezone('Asia/Taipei',now())::date)::text
    or p_record->'valuation'->>'version' is distinct from 'v2'
    or p_record->'valuation'->>'capture_mode' is distinct from 'automated_completed_daily_marks'
    or p_record->'valuation'->>'date' is distinct from p_record->>'date'
    or jsonb_typeof(p_ledger) is distinct from 'array'
    or jsonb_typeof(p_history) is distinct from 'array'
    or exists (select 1 from jsonb_array_elements(p_history) h where h->>'date'=p_record->>'date') then
    return false;
  end if;
  update public.portfolio_db set history_data=p_history||jsonb_build_array(p_record)
    where id=p_row_id and ledger_data::jsonb is not distinct from p_ledger
      and history_data::jsonb is not distinct from p_history;
  get diagnostics changed=row_count;
  return changed=1;
end;
$$;
revoke all on function public.append_automated_nav(bigint,jsonb,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.append_automated_nav(bigint,jsonb,jsonb,jsonb) to service_role;
commit;
notify pgrst, 'reload schema';
