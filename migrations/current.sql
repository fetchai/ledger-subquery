-- Enter migration here
create table store_contract_messages (id text, sender text, permission text, code_id int, message_id text, transaction_id text, block_id text);

insert into store_contract_messages (id, sender, permission, code_id, message_id, transaction_id, block_id)
select m.id, json ->> 'sender', json ->> 'permission', e.attributes ->> 'code_id', m.id, m.transaction_id, m.block_id
from messages m
    join transactions t on m.transaction_id = t.id
    join events e on t.id = e.transaction_id
where type_url = '/cosmwasm.wasm.v1.MsgStoreCode';

-- select * from messages where type_url = '/cosmwasm.wasm.v1.MsgStoreCode';
-- alter table store_contract_messages (sender, permission, code_id)
--     select (sender, permission, code_id) from messages
--         where messages = '/cosmwasm.wasm.v1.MsgStoreCode'
-- --     select (id, sender, permission, id, transaction_id, block_id) from
--     select (id, 'x', id, transaction_id, block_id) from messages where;
-- select json::jsonb ->> 'amount' from messages where json::jsonb #>> '{amount, 0, denom}' = 'atestfet';
