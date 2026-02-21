--
-- PostgreSQL database dump
--

\restrict UNI903pW0XC68tzQCXCzGmUfFl5Or7blLoHMqOKiaRk21Ymdv9JvhQdu1x0vasH

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

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

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


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
-- Name: comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.comments (
    comment_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    parent_comment_id uuid,
    user_id uuid NOT NULL,
    event_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    content character varying(1000) NOT NULL,
    edited boolean DEFAULT false NOT NULL,
    deleted boolean DEFAULT false
);


ALTER TABLE public.comments OWNER TO postgres;

--
-- Name: event; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event (
    event_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(32) NOT NULL,
    description character varying(1000),
    date_and_time timestamp with time zone DEFAULT (now() AT TIME ZONE 'UTC'::text) NOT NULL,
    location character varying(32) NOT NULL,
    creator_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT (now() AT TIME ZONE 'UTC'::text) NOT NULL,
    edited boolean DEFAULT false NOT NULL,
    CONSTRAINT check_event_date_future CHECK ((date_and_time > CURRENT_TIMESTAMP))
);


ALTER TABLE public.event OWNER TO postgres;

--
-- Name: friend_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.friend_requests (
    request_id uuid DEFAULT gen_random_uuid() NOT NULL,
    sender_id uuid NOT NULL,
    receiver_id uuid NOT NULL,
    requested_at timestamp without time zone DEFAULT now(),
    CONSTRAINT sender_not_receiver CHECK ((sender_id <> receiver_id))
);


ALTER TABLE public.friend_requests OWNER TO postgres;

--
-- Name: friendships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.friendships (
    friendship_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    friend_id uuid NOT NULL,
    accepted_at timestamp without time zone DEFAULT now(),
    CONSTRAINT enforce_user_order CHECK ((user_id < friend_id)),
    CONSTRAINT user_cannot_befriend_self CHECK ((user_id <> friend_id))
);


ALTER TABLE public.friendships OWNER TO postgres;

--
-- Name: token_blocklist; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.token_blocklist (
    token_id uuid DEFAULT gen_random_uuid() NOT NULL,
    jti character varying(36) NOT NULL,
    token_type character varying(18) NOT NULL,
    user_id uuid NOT NULL,
    revoked_at timestamp without time zone,
    expires timestamp without time zone NOT NULL
);


ALTER TABLE public.token_blocklist OWNER TO postgres;

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
-- Name: comments comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_pkey PRIMARY KEY (comment_id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (event_id);


--
-- Name: friend_requests friend_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friend_requests
    ADD CONSTRAINT friend_requests_pkey PRIMARY KEY (request_id);


--
-- Name: friendships friendships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friendships
    ADD CONSTRAINT friendships_pkey PRIMARY KEY (friendship_id);


--
-- Name: token_blocklist token_blocklist_jti_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT token_blocklist_jti_key UNIQUE (jti);


--
-- Name: token_blocklist token_blocklist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT token_blocklist_pkey PRIMARY KEY (token_id);


--
-- Name: friendships unique_friendship_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friendships
    ADD CONSTRAINT unique_friendship_pair UNIQUE (user_id, friend_id);


--
-- Name: friend_requests unique_request_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friend_requests
    ADD CONSTRAINT unique_request_pair UNIQUE (sender_id, receiver_id);


--
-- Name: idx_event_creator_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_event_creator_id ON public.event USING btree (creator_id);


--
-- Name: comments comments_parent_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES public.comments(comment_id) ON DELETE SET NULL;


--
-- Name: comments comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: event fk_event_creator; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT fk_event_creator FOREIGN KEY (creator_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: friendships fk_friend; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friendships
    ADD CONSTRAINT fk_friend FOREIGN KEY (friend_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: friend_requests fk_receiver; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friend_requests
    ADD CONSTRAINT fk_receiver FOREIGN KEY (receiver_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: friend_requests fk_sender; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friend_requests
    ADD CONSTRAINT fk_sender FOREIGN KEY (sender_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: friendships fk_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.friendships
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: token_blocklist fk_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict UNI903pW0XC68tzQCXCzGmUfFl5Or7blLoHMqOKiaRk21Ymdv9JvhQdu1x0vasH

