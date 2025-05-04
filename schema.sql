--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Ubuntu 14.17-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.17 (Ubuntu 14.17-0ubuntu0.22.04.1)

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

CREATE TABLE public.app_user (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    username character varying(32) NOT NULL,
    password_hash character varying(128) NOT NULL,
    email character varying(320) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT email_format CHECK (((email)::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text))
);


ALTER TABLE public.app_user OWNER TO postgres;

--
-- Name: app_user app_user_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_email_key UNIQUE (email);


--
-- Name: app_user app_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_pkey PRIMARY KEY (user_id);


--
-- Name: app_user app_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_username_key UNIQUE (username);


--
-- Name: friends; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE friends (
    friend_id SERIAL NOT NULL PRIMARY KEY,
    user_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'unraleted',  
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    CONSTRAINT unique_friendship UNIQUE (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
);

--
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE events ( 
    event_id UUID PRIMARY KEY, 
    event_title VARCHAR(255), 
    desciption TEXT, 
    location_name VARCHAR(255), 
    width DECIMAL(9,6), 
    height DECIMAL (9,6), 
    start_time TIMESTAMP, 
    end_time TIMESTAMP, 
    created_by UUID visiblity VARCHAR(30), 
    category VARCHAR(100) DEFAULT 'uncategorized', 
    created_at TIMESTAMP DEFAULT now(), 
    updated_at TIMESTAMP DEFAULT now() 
);

--
-- Name: events_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE events_participants ( 
    event_id UUID REFERENCES, 
    events(event_id) ON DELETE CASCADE, 
    user_id UUID REFERENCES, 
    app_user(user_id) ON DELETE CASCADE status VARCHAR(30) DEFAULT 'no_starting', 
    PRIMARY KEY (event_id, user_id) 
);

--
-- Name: events_comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE events_comments ( 
    events_comments_id SERIAL PRIMARY KEY, 
    event_id UUID REFERENCES, 
    events(event_id) ON DELETE CASCADE, 
    user_id UUID REFERENCES app_user(user_id) ON DELETE SET NULL, 
    content TEXT NOT NULL, 
    created_at TIMESTAMP DEFAULT now() 
);
--
-- PostgreSQL database dump complete
--

