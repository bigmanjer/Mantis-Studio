-- Free accounts without their own AI key get one automatic "organize" of an imported book.
alter table public.profiles add column if not exists organize_used boolean not null default false;
