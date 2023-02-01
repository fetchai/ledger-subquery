--! Previous: sha1:914d20d8e81f79b1e98e114302e6e48534463c27
--! Hash: sha1:12fcbbff828973e1619ec9fee35008f99e747cf2

CREATE SCHEMA IF NOT EXISTS app;
SET SCHEMA 'app';

ALTER TABLE IF EXISTS ONLY app.almanac_resolutions DROP CONSTRAINT IF EXISTS almanac_resolutions_record_id_fkey;
ALTER TABLE IF EXISTS ONLY app.almanac_resolutions DROP CONSTRAINT IF EXISTS almanac_resolutions_contract_id_fkey;
ALTER TABLE IF EXISTS ONLY app.almanac_resolutions DROP CONSTRAINT IF EXISTS almanac_resolutions_agent_id_fkey;
DROP INDEX IF EXISTS app.almanac_resolutions_record_id;
DROP INDEX IF EXISTS app.almanac_resolutions_contract_id;
DROP INDEX IF EXISTS app.almanac_resolutions_agent_id;
ALTER TABLE IF EXISTS ONLY app.almanac_resolutions DROP CONSTRAINT IF EXISTS almanac_resolutions_pkey;
DROP TABLE IF EXISTS app.almanac_resolutions;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: almanac_resolutions; Type: TABLE; Schema: app; Owner: subquery
--

CREATE TABLE app.almanac_resolutions (
                                         id text NOT NULL,
                                         agent_id text NOT NULL,
                                         contract_id text NOT NULL,
                                         record_id text NOT NULL
);


ALTER TABLE app.almanac_resolutions OWNER TO subquery;

--
-- Name: almanac_resolutions almanac_resolutions_pkey; Type: CONSTRAINT; Schema: app; Owner: subquery
--

ALTER TABLE ONLY app.almanac_resolutions
    ADD CONSTRAINT almanac_resolutions_pkey PRIMARY KEY (id);


--
-- Name: almanac_resolutions_agent_id; Type: INDEX; Schema: app; Owner: subquery
--

CREATE INDEX almanac_resolutions_agent_id ON app.almanac_resolutions USING hash (agent_id);


--
-- Name: almanac_resolutions_contract_id; Type: INDEX; Schema: app; Owner: subquery
--

CREATE INDEX almanac_resolutions_contract_id ON app.almanac_resolutions USING hash (contract_id);


--
-- Name: almanac_resolutions_record_id; Type: INDEX; Schema: app; Owner: subquery
--

CREATE INDEX almanac_resolutions_record_id ON app.almanac_resolutions USING hash (record_id);


--
-- Name: almanac_resolutions almanac_resolutions_agent_id_fkey; Type: FK CONSTRAINT; Schema: app; Owner: subquery
--

ALTER TABLE ONLY app.almanac_resolutions
    ADD CONSTRAINT almanac_resolutions_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES app.agents(id) ON UPDATE CASCADE;


--
-- Name: almanac_resolutions almanac_resolutions_contract_id_fkey; Type: FK CONSTRAINT; Schema: app; Owner: subquery
--

ALTER TABLE ONLY app.almanac_resolutions
    ADD CONSTRAINT almanac_resolutions_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES app.contracts(id) ON UPDATE CASCADE;


--
-- Name: almanac_resolutions almanac_resolutions_record_id_fkey; Type: FK CONSTRAINT; Schema: app; Owner: subquery
--

ALTER TABLE ONLY app.almanac_resolutions
    ADD CONSTRAINT almanac_resolutions_record_id_fkey FOREIGN KEY (record_id) REFERENCES app.almanac_records(id) ON UPDATE CASCADE;


--
-- PostgreSQL database dump complete
--


INSERT INTO app.almanac_resolutions (id, agent_id, contract_id, record_id)
SELECT reg.id, reg.agent_id, reg.contract_id, reg.record_id
FROM app.almanac_registrations reg
WHERE reg.expiry_height > (
    SELECT b.height FROM app.blocks b
                    ORDER BY b.height
                    LIMIT 1
    );
