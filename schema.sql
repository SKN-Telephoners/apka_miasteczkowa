--
-- PostgreSQL database dump
--

\restrict BydDvjq5ybPFJdEQG5sbmUsKW50RfI71JpxL2MaMDiGEbLSb7KC0pFqtfq6TPDP

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

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
-- Name: friendrequeststatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.friendrequeststatus AS ENUM (
    'pending',
    'accepted',
    'rejected'
);


ALTER TYPE public.friendrequeststatus OWNER TO postgres;

--
-- Name: inviterequeststatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.inviterequeststatus AS ENUM (
    'pending',
    'accepted',
    'declined'
);


ALTER TYPE public.inviterequeststatus OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: Block_list; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Block_list" (
    block_id uuid NOT NULL,
    user_id uuid NOT NULL,
    blocked_user_id uuid NOT NULL
);


ALTER TABLE public."Block_list" OWNER TO postgres;

--
-- Name: Comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Comments" (
    comment_id uuid NOT NULL,
    parent_comment_id uuid,
    user_id uuid NOT NULL,
    event_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    content character varying(1000) NOT NULL,
    edited boolean,
    deleted boolean
);


ALTER TABLE public."Comments" OWNER TO postgres;

--
-- Name: Event; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Event" (
    event_id uuid NOT NULL,
    event_name character varying(32) NOT NULL,
    description character varying(1000),
    date_and_time timestamp with time zone NOT NULL,
    location character varying(32) NOT NULL,
    creator_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    is_edited boolean,
    comment_count integer NOT NULL,
    participant_count integer NOT NULL,
    is_private boolean NOT NULL,
    CONSTRAINT check_comment_count_positive CHECK ((comment_count >= 0)),
    CONSTRAINT check_participant_count_positive CHECK ((participant_count >= 0))
);


ALTER TABLE public."Event" OWNER TO postgres;

--
-- Name: Event_Pictures; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Event_Pictures" (
    event_picture_id uuid NOT NULL,
    event_picture_link character varying(64) NOT NULL,
    event_id uuid NOT NULL
);


ALTER TABLE public."Event_Pictures" OWNER TO postgres;

--
-- Name: Event_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Event_participants" (
    event_participants_id uuid NOT NULL,
    event_id uuid NOT NULL,
    user_id uuid NOT NULL
);


ALTER TABLE public."Event_participants" OWNER TO postgres;

--
-- Name: Friend_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Friend_requests" (
    request_id uuid NOT NULL,
    sender_id uuid NOT NULL,
    receiver_id uuid NOT NULL,
    requested_at timestamp without time zone NOT NULL,
    status public.friendrequeststatus NOT NULL,
    CONSTRAINT sender_not_receiver CHECK ((sender_id <> receiver_id))
);


ALTER TABLE public."Friend_requests" OWNER TO postgres;

--
-- Name: Friendships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Friendships" (
    friendship_id uuid NOT NULL,
    user_id uuid NOT NULL,
    friend_id uuid NOT NULL,
    accepted_at timestamp without time zone NOT NULL,
    CONSTRAINT enforce_user_order CHECK ((user_id < friend_id)),
    CONSTRAINT user_cannot_befriend_self CHECK ((user_id <> friend_id))
);


ALTER TABLE public."Friendships" OWNER TO postgres;

--
-- Name: Invites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Invites" (
    invite_id uuid NOT NULL,
    event_id uuid NOT NULL,
    inviter_id uuid NOT NULL,
    invited_id uuid NOT NULL,
    status public.inviterequeststatus NOT NULL,
    created_at timestamp without time zone NOT NULL,
    CONSTRAINT cannot_invite_oneself CHECK ((invited_id <> inviter_id))
);


ALTER TABLE public."Invites" OWNER TO postgres;

--
-- Name: Private_events_shared; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Private_events_shared" (
    private_shared_id uuid NOT NULL,
    event_id uuid NOT NULL,
    sharing uuid NOT NULL,
    shared_with uuid NOT NULL,
    CONSTRAINT cannot_share_with_oneself CHECK ((sharing <> shared_with))
);


ALTER TABLE public."Private_events_shared" OWNER TO postgres;

--
-- Name: Profile_pictures; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Profile_pictures" (
    profile_picture_id uuid NOT NULL,
    user_id uuid NOT NULL,
    picture_link character varying(1000)
);


ALTER TABLE public."Profile_pictures" OWNER TO postgres;

--
-- Name: Token_blocklist; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Token_blocklist" (
    token_id uuid NOT NULL,
    jti character varying(36) NOT NULL,
    token_type character varying(18) NOT NULL,
    user_id uuid NOT NULL,
    revoked_at timestamp with time zone,
    expires timestamp with time zone NOT NULL
);


ALTER TABLE public."Token_blocklist" OWNER TO postgres;

--
-- Name: User; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."User" (
    user_id uuid NOT NULL,
    username character varying(32) NOT NULL,
    password_hash character varying(128) NOT NULL,
    email character varying(320) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    is_confirmed boolean,
    password_changed_at timestamp with time zone,
    confirmed_at timestamp with time zone,
    description character varying(320),
    academy character varying(10),
    course character varying(100),
    year smallint,
    academic_circles character varying(100)[],
    deleted boolean,
    pending_email character varying(320),
    CONSTRAINT email_format CHECK (((email)::text ~* '^[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text))
);


ALTER TABLE public."User" OWNER TO postgres;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: Block_list Block_list_block_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Block_list"
    ADD CONSTRAINT "Block_list_block_id_key" UNIQUE (block_id);


--
-- Name: Block_list Block_list_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Block_list"
    ADD CONSTRAINT "Block_list_pkey" PRIMARY KEY (block_id);


--
-- Name: Comments Comments_comment_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Comments"
    ADD CONSTRAINT "Comments_comment_id_key" UNIQUE (comment_id);


--
-- Name: Comments Comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Comments"
    ADD CONSTRAINT "Comments_pkey" PRIMARY KEY (comment_id);


--
-- Name: Event_Pictures Event_Pictures_event_picture_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_Pictures"
    ADD CONSTRAINT "Event_Pictures_event_picture_id_key" UNIQUE (event_picture_id);


--
-- Name: Event_Pictures Event_Pictures_event_picture_link_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_Pictures"
    ADD CONSTRAINT "Event_Pictures_event_picture_link_key" UNIQUE (event_picture_link);


--
-- Name: Event_Pictures Event_Pictures_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_Pictures"
    ADD CONSTRAINT "Event_Pictures_pkey" PRIMARY KEY (event_picture_id);


--
-- Name: Event Event_event_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event"
    ADD CONSTRAINT "Event_event_id_key" UNIQUE (event_id);


--
-- Name: Event_participants Event_participants_event_participants_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_participants"
    ADD CONSTRAINT "Event_participants_event_participants_id_key" UNIQUE (event_participants_id);


--
-- Name: Event_participants Event_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_participants"
    ADD CONSTRAINT "Event_participants_pkey" PRIMARY KEY (event_participants_id);


--
-- Name: Event Event_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event"
    ADD CONSTRAINT "Event_pkey" PRIMARY KEY (event_id);


--
-- Name: Friend_requests Friend_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friend_requests"
    ADD CONSTRAINT "Friend_requests_pkey" PRIMARY KEY (request_id);


--
-- Name: Friend_requests Friend_requests_request_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friend_requests"
    ADD CONSTRAINT "Friend_requests_request_id_key" UNIQUE (request_id);


--
-- Name: Friendships Friendships_friendship_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friendships"
    ADD CONSTRAINT "Friendships_friendship_id_key" UNIQUE (friendship_id);


--
-- Name: Friendships Friendships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friendships"
    ADD CONSTRAINT "Friendships_pkey" PRIMARY KEY (friendship_id);


--
-- Name: Invites Invites_invite_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Invites"
    ADD CONSTRAINT "Invites_invite_id_key" UNIQUE (invite_id);


--
-- Name: Invites Invites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Invites"
    ADD CONSTRAINT "Invites_pkey" PRIMARY KEY (invite_id);


--
-- Name: Private_events_shared Private_events_shared_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Private_events_shared"
    ADD CONSTRAINT "Private_events_shared_pkey" PRIMARY KEY (private_shared_id);


--
-- Name: Private_events_shared Private_events_shared_private_shared_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Private_events_shared"
    ADD CONSTRAINT "Private_events_shared_private_shared_id_key" UNIQUE (private_shared_id);


--
-- Name: Profile_pictures Profile_pictures_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Profile_pictures"
    ADD CONSTRAINT "Profile_pictures_pkey" PRIMARY KEY (profile_picture_id);


--
-- Name: Profile_pictures Profile_pictures_profile_picture_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Profile_pictures"
    ADD CONSTRAINT "Profile_pictures_profile_picture_id_key" UNIQUE (profile_picture_id);


--
-- Name: Token_blocklist Token_blocklist_jti_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Token_blocklist"
    ADD CONSTRAINT "Token_blocklist_jti_key" UNIQUE (jti);


--
-- Name: Token_blocklist Token_blocklist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Token_blocklist"
    ADD CONSTRAINT "Token_blocklist_pkey" PRIMARY KEY (token_id);


--
-- Name: Token_blocklist Token_blocklist_token_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Token_blocklist"
    ADD CONSTRAINT "Token_blocklist_token_id_key" UNIQUE (token_id);


--
-- Name: User User_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."User"
    ADD CONSTRAINT "User_email_key" UNIQUE (email);


--
-- Name: User User_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."User"
    ADD CONSTRAINT "User_pkey" PRIMARY KEY (user_id);


--
-- Name: User User_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."User"
    ADD CONSTRAINT "User_user_id_key" UNIQUE (user_id);


--
-- Name: User User_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."User"
    ADD CONSTRAINT "User_username_key" UNIQUE (username);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: Invites unique_event_invite; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Invites"
    ADD CONSTRAINT unique_event_invite UNIQUE (inviter_id, invited_id, event_id);


--
-- Name: Event_participants unique_event_participants; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_participants"
    ADD CONSTRAINT unique_event_participants UNIQUE (user_id, event_id);


--
-- Name: Friendships unique_friendship_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friendships"
    ADD CONSTRAINT unique_friendship_pair UNIQUE (user_id, friend_id);


--
-- Name: Private_events_shared unique_private_events_shared; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Private_events_shared"
    ADD CONSTRAINT unique_private_events_shared UNIQUE (sharing, shared_with, event_id);


--
-- Name: Friend_requests unique_request_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friend_requests"
    ADD CONSTRAINT unique_request_pair UNIQUE (sender_id, receiver_id);


--
-- Name: ix_Block_list_blocked_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Block_list_blocked_user_id" ON public."Block_list" USING btree (blocked_user_id);


--
-- Name: ix_Block_list_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Block_list_user_id" ON public."Block_list" USING btree (user_id);


--
-- Name: ix_Event_Pictures_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Event_Pictures_event_id" ON public."Event_Pictures" USING btree (event_id);


--
-- Name: ix_Event_creator_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Event_creator_id" ON public."Event" USING btree (creator_id);


--
-- Name: ix_Event_participants_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Event_participants_event_id" ON public."Event_participants" USING btree (event_id);


--
-- Name: ix_Event_participants_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Event_participants_user_id" ON public."Event_participants" USING btree (user_id);


--
-- Name: ix_Friend_requests_receiver_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Friend_requests_receiver_id" ON public."Friend_requests" USING btree (receiver_id);


--
-- Name: ix_Friend_requests_sender_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Friend_requests_sender_id" ON public."Friend_requests" USING btree (sender_id);


--
-- Name: ix_Friendships_friend_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Friendships_friend_id" ON public."Friendships" USING btree (friend_id);


--
-- Name: ix_Friendships_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Friendships_user_id" ON public."Friendships" USING btree (user_id);


--
-- Name: ix_Invites_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Invites_event_id" ON public."Invites" USING btree (event_id);


--
-- Name: ix_Invites_invited_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Invites_invited_id" ON public."Invites" USING btree (invited_id);


--
-- Name: ix_Invites_inviter_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Invites_inviter_id" ON public."Invites" USING btree (inviter_id);


--
-- Name: ix_Private_events_shared_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Private_events_shared_event_id" ON public."Private_events_shared" USING btree (event_id);


--
-- Name: ix_Private_events_shared_shared_with; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Private_events_shared_shared_with" ON public."Private_events_shared" USING btree (shared_with);


--
-- Name: ix_Private_events_shared_sharing; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Private_events_shared_sharing" ON public."Private_events_shared" USING btree (sharing);


--
-- Name: ix_Profile_pictures_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Profile_pictures_user_id" ON public."Profile_pictures" USING btree (user_id);


--
-- Name: ix_Token_blocklist_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_Token_blocklist_user_id" ON public."Token_blocklist" USING btree (user_id);


--
-- Name: Block_list Block_list_blocked_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Block_list"
    ADD CONSTRAINT "Block_list_blocked_user_id_fkey" FOREIGN KEY (blocked_user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Block_list Block_list_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Block_list"
    ADD CONSTRAINT "Block_list_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Comments Comments_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Comments"
    ADD CONSTRAINT "Comments_event_id_fkey" FOREIGN KEY (event_id) REFERENCES public."Event"(event_id) ON DELETE CASCADE;


--
-- Name: Comments Comments_parent_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Comments"
    ADD CONSTRAINT "Comments_parent_comment_id_fkey" FOREIGN KEY (parent_comment_id) REFERENCES public."Comments"(comment_id) ON DELETE SET NULL;


--
-- Name: Comments Comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Comments"
    ADD CONSTRAINT "Comments_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Event_Pictures Event_Pictures_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_Pictures"
    ADD CONSTRAINT "Event_Pictures_event_id_fkey" FOREIGN KEY (event_id) REFERENCES public."Event"(event_id) ON DELETE CASCADE;


--
-- Name: Event Event_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event"
    ADD CONSTRAINT "Event_creator_id_fkey" FOREIGN KEY (creator_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Event_participants Event_participants_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_participants"
    ADD CONSTRAINT "Event_participants_event_id_fkey" FOREIGN KEY (event_id) REFERENCES public."Event"(event_id) ON DELETE CASCADE;


--
-- Name: Event_participants Event_participants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Event_participants"
    ADD CONSTRAINT "Event_participants_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Friend_requests Friend_requests_receiver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friend_requests"
    ADD CONSTRAINT "Friend_requests_receiver_id_fkey" FOREIGN KEY (receiver_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Friend_requests Friend_requests_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friend_requests"
    ADD CONSTRAINT "Friend_requests_sender_id_fkey" FOREIGN KEY (sender_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Friendships Friendships_friend_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friendships"
    ADD CONSTRAINT "Friendships_friend_id_fkey" FOREIGN KEY (friend_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Friendships Friendships_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Friendships"
    ADD CONSTRAINT "Friendships_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Invites Invites_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Invites"
    ADD CONSTRAINT "Invites_event_id_fkey" FOREIGN KEY (event_id) REFERENCES public."Event"(event_id) ON DELETE CASCADE;


--
-- Name: Invites Invites_invited_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Invites"
    ADD CONSTRAINT "Invites_invited_id_fkey" FOREIGN KEY (invited_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Invites Invites_inviter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Invites"
    ADD CONSTRAINT "Invites_inviter_id_fkey" FOREIGN KEY (inviter_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Private_events_shared Private_events_shared_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Private_events_shared"
    ADD CONSTRAINT "Private_events_shared_event_id_fkey" FOREIGN KEY (event_id) REFERENCES public."Event"(event_id) ON DELETE CASCADE;


--
-- Name: Private_events_shared Private_events_shared_shared_with_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Private_events_shared"
    ADD CONSTRAINT "Private_events_shared_shared_with_fkey" FOREIGN KEY (shared_with) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Private_events_shared Private_events_shared_sharing_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Private_events_shared"
    ADD CONSTRAINT "Private_events_shared_sharing_fkey" FOREIGN KEY (sharing) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Profile_pictures Profile_pictures_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Profile_pictures"
    ADD CONSTRAINT "Profile_pictures_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- Name: Token_blocklist Token_blocklist_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Token_blocklist"
    ADD CONSTRAINT "Token_blocklist_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public."User"(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict BydDvjq5ybPFJdEQG5sbmUsKW50RfI71JpxL2MaMDiGEbLSb7KC0pFqtfq6TPDP

