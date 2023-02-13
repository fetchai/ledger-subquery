--! Previous: sha1:914d20d8e81f79b1e98e114302e6e48534463c27
--! Hash: sha1:4cd160088f2f5f2ea996294f7076068a9c4d6649

-- Enter migration here
CREATE SCHEMA IF NOT EXISTS app;
SET SCHEMA 'app';

ALTER TABLE app.contracts
    ALTER COLUMN store_message_id DROP NOT NULL;
ALTER TABLE app.contracts
    ALTER COLUMN instantiate_message_id DROP NOT NULL;
