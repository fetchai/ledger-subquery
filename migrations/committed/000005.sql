--! Previous: sha1:da26eb35d28f84418481866c2f08a576617e9bc6
--! Hash: sha1:c74f3c0c8cc6e06f7e680fa0e7d2c7d491b282e1

-- Enter migration here
CREATE SCHEMA IF NOT EXISTS app;
SET SCHEMA 'app';

alter table app.execute_contract_messages
    RENAME column contract to contract_id;
CREATE INDEX execute_contract_messages_contract_id ON app.execute_contract_messages USING hash (contract_id);
ALTER TABLE ONLY app.execute_contract_messages
    ADD CONSTRAINT execute_contract_messages_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES app.contracts(id) ON UPDATE CASCADE;
