--! Previous: sha1:da26eb35d28f84418481866c2f08a576617e9bc6
--! Hash: sha1:85d9a089f412eb4b9593109b614ecd0da5305682

-- Enter migration here
CREATE SCHEMA IF NOT EXISTS app;
SET SCHEMA 'app';

alter table app.cw20_transfers
    RENAME column contract to contract_id;
CREATE INDEX cw20_transfers_contract_id ON app.cw20_transfers USING hash (contract_id);
ALTER TABLE ONLY app.cw20_transfers
    ADD CONSTRAINT cw20_transfers_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES app.contracts(id) ON UPDATE CASCADE;
