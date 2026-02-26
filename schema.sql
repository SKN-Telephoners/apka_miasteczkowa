--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Ubuntu 14.17-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.17 (Ubuntu 14.17-0ubuntu0.22.04.1)
// SQL script to create the database schema for the application, including tables for users and token blocklist, with constraints and indexes
// Po polsku: Skrypt SQL do tworzenia schematu bazy danych dla aplikacji, w tym tabel dla użytkowników i bloklisty tokenów, z ograniczeniami i indeksami
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_user; Type: TABLE; Schema: public; Owner: postgres
--
// Create the app_user table to store user information, including user ID, username, password hash, email, and creation timestamp
// Po polsku: Utworzenie tabeli app_user do przechowywania informacji o użytkownikach, w tym ID użytkownika, nazwy użytkownika, hasha hasła, emaila i znacznika czasu utworzenia
CREATE TABLE public.app_user (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    username character varying(32) NOT NULL,
    password_hash character varying(128) NOT NULL,
    email character varying(320) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT email_format CHECK (((email)::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text))
);

// Set the owner of the app_user table to postgres
// Ustawienie właściciela tabeli app_user na postgres
ALTER TABLE public.app_user OWNER TO postgres;

--
-- Name: app_user app_user_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--
// Add a unique constraint on the email column of the app_user table to ensure that each email address is unique
// Po polsku: Dodanie unikalnego ograniczenia na kolumnie email tabeli app_user, aby zapewnić, że każdy adres email jest unikalny
ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_email_key UNIQUE (email);


--
-- Name: app_user app_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--
// Add a primary key constraint on the user_id column of the app_user table to uniquely identify each user
// Po polsku: Dodanie ograniczenia klucza głównego na kolumnie user_id tabeli app_user, aby jednoznacznie identyfikować każdego użytkownika
ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_pkey PRIMARY KEY (user_id);


--
-- Name: app_user app_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--
// Add a unique constraint on the username column of the app_user table to ensure that each username is unique
// Po polsku: Dodanie unikalnego ograniczenia na kolumnie username tabeli app_user, aby zapewnić, że każda nazwa użytkownika jest unikalna
ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_username_key UNIQUE (username);


--
-- Name: token_blocklist; Type: TABLE; Schema: public; Owner: postgres
--
// Create the token_blocklist table to store information about revoked JWT tokens, including token ID, token type, user ID, revocation time, and expiration time
// Po polsku: Utworzenie tabeli token_blocklist do przechowywania informacji o unieważnionych tokenach JWT, w tym ID tokena, typu tokena, ID użytkownika, czasu unieważnienia i czasu wygaśnięcia
CREATE TABLE public.token_blocklist (
    token_id uuid DEFAULT gen_random_uuid() NOT NULL,
    jti character varying(36) NOT NULL,
    token_type character varying(18) NOT NULL,
    user_id uuid NOT NULL,
    revoked_at timestamp without time zone,
    expires timestamp without time zone NOT NULL
);

// Set the owner of the token_blocklist table to postgres
// Ustawienie właściciela tabeli token_blocklist na postgres
ALTER TABLE public.token_blocklist OWNER TO postgres;

--
-- Name: token_blocklist token_blocklist_jti_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--
// Add a unique constraint on the jti column of the token_blocklist table to ensure that each token ID is unique
// Po polsku: Dodanie unikalnego ograniczenia na kolumnie jti tabeli token_blocklist, aby zapewnić, że każdy ID tokena jest unikalny
ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT token_blocklist_jti_key UNIQUE (jti);


--
-- Name: token_blocklist token_blocklist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--
// Add a primary key constraint on the token_id column of the token_blocklist table to uniquely identify each revoked token
// Po polsku: Dodanie ograniczenia klucza głównego na kolumnie token_id tabeli token_blocklist, aby jednoznacznie identyfikować każdy unieważniony token
ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT token_blocklist_pkey PRIMARY KEY (token_id);


--
-- Name: token_blocklist fk_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--
// Add a foreign key constraint on the user_id column of the token_blocklist table to reference the user_id column of the app_user table, with cascading delete
// Po polsku: Dodanie ograniczenia klucza obcego na kolumnie user_id tabeli token_blocklist, aby odwoływać się do kolumny user_id tabeli app_user, z kaskadowym usuwaniem
ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

