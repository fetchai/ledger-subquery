--! Previous: sha1:1ac102c5a5b3baf595ce66aac2912ad9f1090b49
--! Hash: sha1:7e732658a28ad168924c1ff4eb82172ba66166a7

CREATE SCHEMA IF NOT EXISTS app;
SET SCHEMA 'app';

DROP TABLE IF EXISTS release_version;
create table release_version (
    id int primary key not null,
    git_hash text not null,
    git_tag text not null
);

insert into release_version (id, git_hash, git_tag) VALUES (0, '3ac0d0143547f9a0cc3462a916933e10ea5e747d', 'v0.3.0');
