--! Previous: sha1:9744879ec421a1edd39b9bc53b717a35b00e31cc
--! Hash: sha1:a3f4085c1ee2e3bc5438c28f13e9f09ac6d6d358

CREATE SCHEMA IF NOT EXISTS app;
SET SCHEMA 'app';

DROP TABLE IF EXISTS release_version;
create table release_version (
    id text primary key not null,
    git_hash text not null,
    git_tag text not null
);

insert into release_version (id, git_hash, git_tag) VALUES ('0', '3ac0d0143547f9a0cc3462a916933e10ea5e747d', 'v0.3.0');
