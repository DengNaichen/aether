--
-- PostgreSQL database dump
--

\restrict MFKxrne8z3qoPvwfLaro1CsdPNXverztssByckeHXk65SZ8QdX4vebOPYWiNkN6

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

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

ALTER TABLE IF EXISTS ONLY public.user_mastery DROP CONSTRAINT IF EXISTS user_mastery_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_mastery DROP CONSTRAINT IF EXISTS user_mastery_graph_id_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_mastery DROP CONSTRAINT IF EXISTS user_mastery_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.subtopics DROP CONSTRAINT IF EXISTS subtopics_graph_id_parent_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.subtopics DROP CONSTRAINT IF EXISTS subtopics_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.subtopics DROP CONSTRAINT IF EXISTS subtopics_graph_id_child_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.submission_answers DROP CONSTRAINT IF EXISTS submission_answers_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.submission_answers DROP CONSTRAINT IF EXISTS submission_answers_question_id_fkey;
ALTER TABLE IF EXISTS ONLY public.submission_answers DROP CONSTRAINT IF EXISTS submission_answers_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.quiz_attempts DROP CONSTRAINT IF EXISTS quiz_attempts_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.quiz_attempts DROP CONSTRAINT IF EXISTS quiz_attempts_course_id_fkey;
ALTER TABLE IF EXISTS ONLY public.questions DROP CONSTRAINT IF EXISTS questions_graph_id_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.questions DROP CONSTRAINT IF EXISTS questions_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.questions DROP CONSTRAINT IF EXISTS questions_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.prerequisites DROP CONSTRAINT IF EXISTS prerequisites_graph_id_to_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.prerequisites DROP CONSTRAINT IF EXISTS prerequisites_graph_id_from_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.prerequisites DROP CONSTRAINT IF EXISTS prerequisites_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_nodes DROP CONSTRAINT IF EXISTS knowledge_nodes_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_graphs DROP CONSTRAINT IF EXISTS knowledge_graphs_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_graphs DROP CONSTRAINT IF EXISTS knowledge_graphs_forked_from_id_fkey;
ALTER TABLE IF EXISTS ONLY public.graph_enrollments DROP CONSTRAINT IF EXISTS graph_enrollments_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.graph_enrollments DROP CONSTRAINT IF EXISTS graph_enrollments_graph_id_fkey;
ALTER TABLE IF EXISTS ONLY public.enrollments DROP CONSTRAINT IF EXISTS enrollments_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.enrollments DROP CONSTRAINT IF EXISTS enrollments_course_id_fkey;
DROP TRIGGER IF EXISTS trg_prerequisites_update ON public.prerequisites;
DROP TRIGGER IF EXISTS trg_prerequisites_insert ON public.prerequisites;
DROP TRIGGER IF EXISTS trg_prerequisites_delete ON public.prerequisites;
DROP INDEX IF EXISTS public.ix_users_refresh_token;
DROP INDEX IF EXISTS public.ix_user_mastery_due_date;
DROP INDEX IF EXISTS public.ix_knowledge_nodes_node_id_str;
DROP INDEX IF EXISTS public.ix_knowledge_nodes_level;
DROP INDEX IF EXISTS public.ix_knowledge_nodes_dependents_count;
DROP INDEX IF EXISTS public.ix_knowledge_graphs_slug;
DROP INDEX IF EXISTS public.ix_knowledge_graphs_is_template;
DROP INDEX IF EXISTS public.ix_knowledge_graphs_is_public;
DROP INDEX IF EXISTS public.ix_courses_name;
DROP INDEX IF EXISTS public.idx_users_reset_token;
DROP INDEX IF EXISTS public.idx_subtopic_graph_parent;
DROP INDEX IF EXISTS public.idx_subtopic_graph_child;
DROP INDEX IF EXISTS public.idx_questions_graph_node;
DROP INDEX IF EXISTS public.idx_questions_graph;
DROP INDEX IF EXISTS public.idx_prereq_graph_to;
DROP INDEX IF EXISTS public.idx_prereq_graph_from;
DROP INDEX IF EXISTS public.idx_nodes_level;
DROP INDEX IF EXISTS public.idx_nodes_graph_str;
DROP INDEX IF EXISTS public.idx_nodes_graph_id;
DROP INDEX IF EXISTS public.idx_nodes_graph;
DROP INDEX IF EXISTS public.idx_mastery_user_graph;
DROP INDEX IF EXISTS public.idx_mastery_graph_node;
DROP INDEX IF EXISTS public.idx_mastery_due;
DROP INDEX IF EXISTS public.idx_graphs_tags;
DROP INDEX IF EXISTS public.idx_graphs_public_template;
DROP INDEX IF EXISTS public.idx_graphs_owner;
DROP INDEX IF EXISTS public.idx_enrollment_user;
DROP INDEX IF EXISTS public.idx_enrollment_graph;
DROP INDEX IF EXISTS public.idx_enrollment_active;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.user_mastery DROP CONSTRAINT IF EXISTS user_mastery_pkey;
ALTER TABLE IF EXISTS ONLY public.graph_enrollments DROP CONSTRAINT IF EXISTS uq_user_graph_enrollment;
ALTER TABLE IF EXISTS ONLY public.knowledge_graphs DROP CONSTRAINT IF EXISTS uq_owner_graph_slug;
ALTER TABLE IF EXISTS ONLY public.knowledge_nodes DROP CONSTRAINT IF EXISTS uq_graph_node_uuid;
ALTER TABLE IF EXISTS ONLY public.knowledge_nodes DROP CONSTRAINT IF EXISTS uq_graph_node_str;
ALTER TABLE IF EXISTS ONLY public.subtopics DROP CONSTRAINT IF EXISTS subtopics_pkey;
ALTER TABLE IF EXISTS ONLY public.submission_answers DROP CONSTRAINT IF EXISTS submission_answers_pkey;
ALTER TABLE IF EXISTS ONLY public.quiz_attempts DROP CONSTRAINT IF EXISTS quiz_attempts_pkey;
ALTER TABLE IF EXISTS ONLY public.questions DROP CONSTRAINT IF EXISTS questions_pkey;
ALTER TABLE IF EXISTS ONLY public.prerequisites DROP CONSTRAINT IF EXISTS prerequisites_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_nodes DROP CONSTRAINT IF EXISTS knowledge_nodes_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_graphs DROP CONSTRAINT IF EXISTS knowledge_graphs_pkey;
ALTER TABLE IF EXISTS ONLY public.graph_enrollments DROP CONSTRAINT IF EXISTS graph_enrollments_pkey;
ALTER TABLE IF EXISTS ONLY public.enrollments DROP CONSTRAINT IF EXISTS enrollments_pkey;
ALTER TABLE IF EXISTS ONLY public.courses DROP CONSTRAINT IF EXISTS courses_pkey;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.user_mastery;
DROP TABLE IF EXISTS public.subtopics;
DROP TABLE IF EXISTS public.submission_answers;
DROP TABLE IF EXISTS public.quiz_attempts;
DROP TABLE IF EXISTS public.questions;
DROP TABLE IF EXISTS public.prerequisites;
DROP TABLE IF EXISTS public.knowledge_nodes;
DROP TABLE IF EXISTS public.knowledge_graphs;
DROP TABLE IF EXISTS public.graph_enrollments;
DROP TABLE IF EXISTS public.enrollments;
DROP TABLE IF EXISTS public.courses;
DROP FUNCTION IF EXISTS public.trigger_topology_on_update();
DROP FUNCTION IF EXISTS public.trigger_topology_on_insert();
DROP FUNCTION IF EXISTS public.trigger_topology_on_delete();
DROP FUNCTION IF EXISTS public.recalculate_graph_topology(target_graph_id uuid);
DROP TYPE IF EXISTS public.quiz_status_enum;
--
-- Name: quiz_status_enum; Type: TYPE; Schema: public; Owner: aether_user
--

CREATE TYPE public.quiz_status_enum AS ENUM (
    'IN_PROGRESS',
    'COMPLETED',
    'ABORTED'
);


ALTER TYPE public.quiz_status_enum OWNER TO aether_user;

--
-- Name: recalculate_graph_topology(uuid); Type: FUNCTION; Schema: public; Owner: aether_user
--

CREATE FUNCTION public.recalculate_graph_topology(target_graph_id uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Step 1: Reset all nodes to default values first
    UPDATE knowledge_nodes
    SET level = 0, dependents_count = 0
    WHERE graph_id = target_graph_id;

    -- Step 2: Calculate level (topological depth in DAG)
    -- level = 0: nodes with no prerequisites
    -- level = N: max(prerequisite levels) + 1
    WITH RECURSIVE topo_levels AS (
        -- Base case: nodes with no incoming prerequisite edges -> level = 0
        SELECT
            n.id AS node_id,
            0 AS level
        FROM knowledge_nodes n
        WHERE n.graph_id = target_graph_id
          AND NOT EXISTS (
              SELECT 1 FROM prerequisites p
              WHERE p.graph_id = target_graph_id
                AND p.to_node_id = n.id
          )

        UNION ALL

        -- Recursive case: nodes whose prerequisites have been processed
        SELECT
            p.to_node_id AS node_id,
            tl.level + 1 AS level
        FROM prerequisites p
        INNER JOIN topo_levels tl ON p.from_node_id = tl.node_id
        WHERE p.graph_id = target_graph_id
    ),
    -- Take max level for each node (handles multiple prerequisite paths)
    max_levels AS (
        SELECT node_id, MAX(level) AS level
        FROM topo_levels
        GROUP BY node_id
    )
    UPDATE knowledge_nodes n
    SET level = ml.level
    FROM max_levels ml
    WHERE n.id = ml.node_id
      AND n.graph_id = target_graph_id;

    -- Step 3: Calculate dependents_count (how many nodes depend on this node)
    -- This counts all direct and indirect dependents
    WITH RECURSIVE downstream AS (
        -- Base case: direct dependents
        SELECT
            p.from_node_id AS root_node,
            p.to_node_id AS dependent_node
        FROM prerequisites p
        WHERE p.graph_id = target_graph_id

        UNION

        -- Recursive case: dependents of dependents
        SELECT
            d.root_node,
            p.to_node_id AS dependent_node
        FROM downstream d
        INNER JOIN prerequisites p
            ON d.dependent_node = p.from_node_id
           AND p.graph_id = target_graph_id
    ),
    dep_counts AS (
        SELECT root_node, COUNT(DISTINCT dependent_node) AS cnt
        FROM downstream
        GROUP BY root_node
    )
    UPDATE knowledge_nodes n
    SET dependents_count = dc.cnt
    FROM dep_counts dc
    WHERE n.id = dc.root_node
      AND n.graph_id = target_graph_id;

END;
$$;


ALTER FUNCTION public.recalculate_graph_topology(target_graph_id uuid) OWNER TO aether_user;

--
-- Name: trigger_topology_on_delete(); Type: FUNCTION; Schema: public; Owner: aether_user
--

CREATE FUNCTION public.trigger_topology_on_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    affected_graph_id UUID;
BEGIN
    SELECT DISTINCT graph_id INTO affected_graph_id FROM old_table LIMIT 1;

    IF affected_graph_id IS NOT NULL THEN
        PERFORM recalculate_graph_topology(affected_graph_id);
    END IF;

    RETURN NULL;
END;
$$;


ALTER FUNCTION public.trigger_topology_on_delete() OWNER TO aether_user;

--
-- Name: trigger_topology_on_insert(); Type: FUNCTION; Schema: public; Owner: aether_user
--

CREATE FUNCTION public.trigger_topology_on_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    affected_graph_id UUID;
BEGIN
    SELECT DISTINCT graph_id INTO affected_graph_id FROM new_table LIMIT 1;

    IF affected_graph_id IS NOT NULL THEN
        PERFORM recalculate_graph_topology(affected_graph_id);
    END IF;

    RETURN NULL;
END;
$$;


ALTER FUNCTION public.trigger_topology_on_insert() OWNER TO aether_user;

--
-- Name: trigger_topology_on_update(); Type: FUNCTION; Schema: public; Owner: aether_user
--

CREATE FUNCTION public.trigger_topology_on_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    affected_graph_id UUID;
BEGIN
    SELECT DISTINCT graph_id INTO affected_graph_id FROM new_table LIMIT 1;

    IF affected_graph_id IS NOT NULL THEN
        PERFORM recalculate_graph_topology(affected_graph_id);
    END IF;

    RETURN NULL;
END;
$$;


ALTER FUNCTION public.trigger_topology_on_update() OWNER TO aether_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: courses; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.courses (
    id character varying NOT NULL,
    name character varying,
    description character varying
);


ALTER TABLE public.courses OWNER TO aether_user;

--
-- Name: enrollments; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.enrollments (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    course_id character varying NOT NULL,
    enrollment_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.enrollments OWNER TO aether_user;

--
-- Name: graph_enrollments; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.graph_enrollments (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    graph_id uuid NOT NULL,
    enrolled_at timestamp with time zone DEFAULT now() NOT NULL,
    last_activity timestamp with time zone,
    completed_at timestamp with time zone,
    is_active boolean NOT NULL
);


ALTER TABLE public.graph_enrollments OWNER TO aether_user;

--
-- Name: knowledge_graphs; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.knowledge_graphs (
    id uuid NOT NULL,
    owner_id uuid NOT NULL,
    name character varying NOT NULL,
    slug character varying NOT NULL,
    description text,
    tags character varying[],
    is_public boolean NOT NULL,
    is_template boolean NOT NULL,
    enrollment_count integer NOT NULL,
    forked_from_id uuid,
    allow_fork boolean NOT NULL,
    allow_pr boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.knowledge_graphs OWNER TO aether_user;

--
-- Name: knowledge_nodes; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.knowledge_nodes (
    id uuid NOT NULL,
    graph_id uuid NOT NULL,
    node_id_str character varying,
    node_name character varying NOT NULL,
    description text,
    level integer,
    dependents_count integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.knowledge_nodes OWNER TO aether_user;

--
-- Name: prerequisites; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.prerequisites (
    graph_id uuid NOT NULL,
    from_node_id uuid NOT NULL,
    to_node_id uuid NOT NULL,
    weight double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_no_self_prerequisite CHECK ((from_node_id <> to_node_id)),
    CONSTRAINT ck_prerequisite_weight CHECK (((weight >= (0.0)::double precision) AND (weight <= (1.0)::double precision)))
);


ALTER TABLE public.prerequisites OWNER TO aether_user;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.questions (
    id uuid NOT NULL,
    graph_id uuid NOT NULL,
    node_id uuid NOT NULL,
    question_type character varying NOT NULL,
    text text NOT NULL,
    details jsonb NOT NULL,
    difficulty character varying NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_question_difficulty CHECK (((difficulty)::text = ANY ((ARRAY['easy'::character varying, 'medium'::character varying, 'hard'::character varying])::text[]))),
    CONSTRAINT ck_question_type CHECK (((question_type)::text = ANY ((ARRAY['multiple_choice'::character varying, 'fill_blank'::character varying, 'calculation'::character varying])::text[])))
);


ALTER TABLE public.questions OWNER TO aether_user;

--
-- Name: quiz_attempts; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.quiz_attempts (
    attempt_id uuid NOT NULL,
    user_id uuid NOT NULL,
    course_id character varying NOT NULL,
    question_num integer NOT NULL,
    status public.quiz_status_enum NOT NULL,
    score integer,
    created_at timestamp with time zone DEFAULT now(),
    submitted_at timestamp with time zone
);


ALTER TABLE public.quiz_attempts OWNER TO aether_user;

--
-- Name: submission_answers; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.submission_answers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    graph_id uuid NOT NULL,
    question_id uuid NOT NULL,
    user_answer json NOT NULL,
    is_correct boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.submission_answers OWNER TO aether_user;

--
-- Name: subtopics; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.subtopics (
    graph_id uuid NOT NULL,
    parent_node_id uuid NOT NULL,
    child_node_id uuid NOT NULL,
    weight double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_no_self_subtopic CHECK ((parent_node_id <> child_node_id)),
    CONSTRAINT ck_subtopic_weight CHECK (((weight >= (0.0)::double precision) AND (weight <= (1.0)::double precision)))
);


ALTER TABLE public.subtopics OWNER TO aether_user;

--
-- Name: user_mastery; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.user_mastery (
    user_id uuid NOT NULL,
    graph_id uuid NOT NULL,
    node_id uuid NOT NULL,
    score double precision NOT NULL,
    p_l0 double precision NOT NULL,
    p_t double precision NOT NULL,
    fsrs_state character varying NOT NULL,
    fsrs_stability double precision,
    fsrs_difficulty double precision,
    due_date timestamp with time zone,
    last_review timestamp with time zone,
    review_log jsonb NOT NULL,
    last_updated timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_mastery_fsrs_difficulty CHECK (((fsrs_difficulty IS NULL) OR ((fsrs_difficulty >= (1.0)::double precision) AND (fsrs_difficulty <= (10.0)::double precision)))),
    CONSTRAINT ck_mastery_fsrs_state CHECK (((fsrs_state)::text = ANY ((ARRAY['learning'::character varying, 'review'::character varying, 'relearning'::character varying])::text[]))),
    CONSTRAINT ck_mastery_p_l0 CHECK (((p_l0 >= (0.0)::double precision) AND (p_l0 <= (1.0)::double precision))),
    CONSTRAINT ck_mastery_p_t CHECK (((p_t >= (0.0)::double precision) AND (p_t <= (1.0)::double precision))),
    CONSTRAINT ck_mastery_score CHECK (((score >= (0.0)::double precision) AND (score <= (1.0)::double precision)))
);


ALTER TABLE public.user_mastery OWNER TO aether_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: aether_user
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    name character varying NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    is_active boolean,
    is_admin boolean NOT NULL,
    oauth_provider character varying,
    oauth_id character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    refresh_token character varying,
    reset_token character varying,
    reset_token_expires_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO aether_user;

--
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.courses (id, name, description) FROM stdin;
g10_phys	Grade 11 Physics - Chapter 1: Kinematics	Introduction to kinematics: displacement, velocity, and acceleration
\.


--
-- Data for Name: enrollments; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.enrollments (id, user_id, course_id, enrollment_date) FROM stdin;
e64104a6-8966-4682-a5cb-0f8677ed16bd	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	2025-11-07 02:51:23.612449+00
\.


--
-- Data for Name: graph_enrollments; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.graph_enrollments (id, user_id, graph_id, enrolled_at, last_activity, completed_at, is_active) FROM stdin;
fb1480de-2c9d-4917-a74b-cc2f6485b4b2	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	2025-11-18 19:31:35.23965+00	\N	\N	t
c25c4fd7-ff40-401e-adf3-d478a41b84e3	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2025-11-24 07:51:47.478518+00	\N	\N	t
\.


--
-- Data for Name: knowledge_graphs; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.knowledge_graphs (id, owner_id, name, slug, description, tags, is_public, is_template, enrollment_count, forked_from_id, allow_fork, allow_pr, created_at, updated_at) FROM stdin;
a5ceec13-66ee-4285-acc8-ef13fdec244d	39dbb758-eb18-4909-8144-ab819d687a73	My Python Course	my-python-course	Learn Python from scratch	{python,programming,beginner}	f	f	0	\N	t	t	2025-11-12 06:26:32.161112+00	\N
18b9bd75-aed7-4631-83f1-bb4c9e9ea209	39dbb758-eb18-4909-8144-ab819d687a73	Advanced Data Structures	advanced-data-structures	Master advanced data structures and algorithms	{algorithms,data-structures,advanced}	t	f	0	\N	t	t	2025-11-12 06:26:40.730844+00	\N
5815da27-0b63-4e75-9d0b-2eef53fb9972	39dbb758-eb18-4909-8144-ab819d687a73	Quick Notes	quick-notes	\N	{}	f	f	0	\N	t	t	2025-11-12 06:26:46.075734+00	\N
2a66e246-d73c-4dbb-bcb6-a61d76dc964a	39dbb758-eb18-4909-8144-ab819d687a73	C++ Programming & Design Patterns!	c-programming-design-patterns	Test slug generation with special characters	{c++,design-patterns}	f	f	0	\N	t	t	2025-11-12 06:27:04.285615+00	\N
79f6869b-a9d1-4965-b864-dafd6a3faa6d	bc7dd8cd-ec52-4082-bc39-825a7e72b294	Grade 11 Physics - Chapter 1: Kinematics	grade-11-physics-chapter-1-kinematics	Introduction to kinematics: displacement, velocity, and acceleration	{physics,grade11,kinematics,development}	t	t	1	\N	t	t	2025-11-13 20:05:45.986179+00	2025-11-18 19:31:35.23965+00
c463695b-1187-4f8a-b139-a225bde8545b	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	my python course	my-python-course	learn python from screach 	{}	f	f	0	\N	t	t	2025-11-22 19:14:25.470088+00	\N
28d691a0-5df4-49d3-b728-ecddaf866644	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	python course	python-course	test 	{}	t	f	0	\N	t	t	2025-11-22 19:15:16.11903+00	\N
84714860-4e96-4852-b8a9-7b991eef48bd	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	test	test	test	{}	f	f	0	\N	t	t	2025-11-22 19:18:29.649342+00	\N
defa757b-8ac2-4452-a2ed-3b0acdc07bb5	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	test lala	test-lala	test lala	{}	f	f	0	\N	t	t	2025-11-22 19:22:44.656601+00	\N
c18d6d95-77ed-4b41-a833-dc5cddec74f4	bc7dd8cd-ec52-4082-bc39-825a7e72b294	Grade 11 Chemistry	grade-11-chemistry	Complete Grade 11 Chemistry curriculum covering matter, elements, compounds, and chemical reactions.	{}	t	t	1	\N	t	t	2025-11-24 07:34:14.217104+00	2025-11-24 07:51:47.478518+00
\.


--
-- Data for Name: knowledge_nodes; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.knowledge_nodes (id, graph_id, node_id_str, node_name, description, level, dependents_count, created_at, updated_at) FROM stdin;
a7fa63f8-cff2-4dcd-8748-d456b669b014	79f6869b-a9d1-4965-b864-dafd6a3faa6d	s1_1	1.1 Motion in Our Lives		0	0	2025-11-13 20:06:22.298129+00	\N
d0fb6dbc-6b0b-4391-aa92-98b587aca876	79f6869b-a9d1-4965-b864-dafd6a3faa6d	s1_3	1.3 Two-Dimensional Motion		0	0	2025-11-13 20:06:22.300302+00	\N
40a0cce9-df72-4721-b303-aa264a89d0e7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	s1_6	1.6 Solving Uniform Acceleration Problems		0	0	2025-11-13 20:06:22.302742+00	\N
bed1e3d1-1c3e-4260-860b-6984b797eafb	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kinematics	Kinematics	The study of motion.	0	0	2025-11-13 20:06:22.303485+00	\N
b7dcf5b7-fd95-4dcc-b0e2-213826327a64	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_base_unit	Base Unit	Fundamental units in SI (e.g., metre (m), second (s)).	9	0	2025-11-13 20:06:22.305058+00	\N
292ffe16-e4f2-49ac-acd9-f1aa726bd35b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	s1_4	1.4 Uniform Acceleration		0	0	2025-11-13 20:06:22.30113+00	\N
3ceb2e87-78aa-4edc-9f62-013c205c682e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ch1	Chapter 1: Motion		0	0	2025-11-13 20:06:22.288115+00	\N
20994d2d-564a-48b6-b508-1bc4ca91ba20	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_nonuniform_motion	Nonuniform Motion	Movement involving change in speed or direction.	6	0	2025-11-13 20:06:22.309305+00	\N
ebdea86b-4b32-4edb-9b93-f13e64300bff	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_scalar	Scalar Quantity	A quantity with magnitude but no direction (e.g., distance, time, speed).	10	0	2025-11-13 20:06:22.304317+00	\N
43bd532e-c53d-4669-9d44-365ff564c308	79f6869b-a9d1-4965-b864-dafd6a3faa6d	s1_2	1.2 Uniform Motion		0	0	2025-11-13 20:06:22.299363+00	\N
6675f374-dd03-41c2-8796-7e81999cc075	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_uniform_motion	Uniform Motion	Movement at a constant speed in a straight line.	2	0	2025-11-13 20:06:22.308546+00	\N
cd52a236-4934-4574-8150-1b5c008d3b9c	79f6869b-a9d1-4965-b864-dafd6a3faa6d	s1_5	1.5 Acceleration Near Earth's Surface		0	0	2025-11-13 20:06:22.301929+00	\N
1109f07f-9d32-408c-999c-73dbfb2d88cc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_vector_add_graphic	Vector Addition (Graphical)	Adding vectors using head-to-tail scale diagrams.	1	6	2025-11-13 20:06:22.3184+00	\N
1255712f-8dd1-4ab8-85b4-1faf7610c1b5	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kin_eq_4	Kinematic Equation (no $\\Delta t$)	$v_{f}^{2}=v_{i}^{2}+2a_{av}\\Delta d$	1	16	2025-11-13 20:06:22.334686+00	\N
182ddcaa-29bf-4484-8c6c-b18496d59832	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_graph_vel_time	Velocity-Time Graph	Plotting velocity vs. time.	4	8	2025-11-13 20:06:22.314586+00	\N
1a161ca5-68e2-4c97-8850-85f7c80aac24	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_vector	Vector Quantity	A quantity with both magnitude and direction.	9	1	2025-11-13 20:06:22.310025+00	\N
20865509-851f-4525-bc9a-fa7111c3c194	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kin_eq_3	Kinematic Equation (no $\\vec{v}_{f}$)	$\\Delta\\vec{d}=\\vec{v}_{i}\\Delta t+\\frac{1}{2}\\vec{a}_{av}(\\Delta t)^{2}$	1	16	2025-11-13 20:06:22.333957+00	\N
273ec2d4-2aa9-47a5-accc-02f852edf5e4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_resultant_disp	Resultant Displacement ($\\Delta\\vec{d}_{R}$)	The vector sum of individual displacements.	3	4	2025-11-13 20:06:22.317227+00	\N
324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kin_prob_solve	Problem-Solving Strategy (Kinematics)	Applying the 5 kinematic equations to solve for unknown variables.	0	20	2025-11-13 20:06:22.336258+00	\N
3fe283af-0a1a-4190-95b2-4322066bb104	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_graph_pos_time	Position-Time Graph	Plotting position vs. time.	1	9	2025-11-13 20:06:22.312955+00	\N
448fef63-5446-41a9-b188-83a57b2d586f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_displacement	Displacement ($\\Delta\\vec{d}$)	Change in position.	7	3	2025-11-13 20:06:22.311483+00	\N
4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_uniform_accel	Uniformly Accelerated Motion	Motion with a constant rate of change in velocity (constant acceleration).	4	10	2025-11-13 20:06:22.323466+00	\N
4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_slope_pos_time	Slope of Position-Time Graph	Represents average velocity.	0	10	2025-11-13 20:06:22.313658+00	\N
538a4f93-25b2-4b30-8d1e-ece54261d891	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_tangent	Tangent Technique	Using the slope of a line tangent to a curve to find instantaneous rate of change.	1	12	2025-11-13 20:06:22.327591+00	\N
5649bae7-fb7f-436c-a34e-5c085a6a014d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_area_vel_time	Area under Velocity-Time Graph	Represents displacement.	3	9	2025-11-13 20:06:22.315477+00	\N
5779685d-faf6-4d00-a974-9d74c994b0e7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_vector_add_algebra	Vector Addition (Algebraic)	Using Pythagorean theorem and trigonometry for right-angle vectors.	0	7	2025-11-13 20:06:22.319109+00	\N
5ef58b93-a72e-49ba-bf69-4dd5315f56d7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_inst_velocity	Instantaneous Velocity	The slope of the tangent on a position-time graph.	0	14	2025-11-13 20:06:22.328398+00	\N
60d09626-84eb-4770-8ec2-5ae442c65ade	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_directions	Communicating Directions	Using compass points and angles (e.g., [N 30° E]).	2	2	2025-11-13 20:06:22.316413+00	\N
6cb12ce7-228f-40f4-87c4-185b110e32b7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_avg_velocity	Average Velocity	Displacement divided by time interval ($\\vec{v}_{av} = \\Delta\\vec{d} / \\Delta t$).	6	7	2025-11-13 20:06:22.312244+00	\N
77b28549-ef65-4a72-9f54-8ce4f6cd7439	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_area_accel_time	Area under Acceleration-Time Graph	Represents the change in velocity.	0	12	2025-11-13 20:06:22.329122+00	\N
7c217eaf-391d-42b3-983c-2f2ef0b9013c	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kin_eq_5	Kinematic Equation (no $\\vec{v}_{i}$)	$\\Delta\\vec{d}=\\vec{v}_{f}\\Delta t-\\frac{1}{2}\\vec{a}_{av}(\\Delta t)^{2}$	1	16	2025-11-13 20:06:22.335438+00	\N
80495392-972a-42ec-a6ec-10e777152993	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_g	Acceleration Due to Gravity ($\\vec{g}$)	Constant acceleration ($9.8~m/s^2$ [down]) near Earth's surface, independent of mass.	2	11	2025-11-13 20:06:22.329814+00	\N
8a4f2710-f341-4455-9680-9665e0a584d6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kin_eq_1	Kinematic Equation (Definition of $\\vec{a}_{av}$)	$\\vec{a}_{av}=\\frac{\\vec{v}_{f}-\\vec{v}_{i}}{\\Delta t}$	2	12	2025-11-13 20:06:22.332444+00	\N
9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_free_fall	Free Fall	Motion of an object where gravity is the only force acting (air resistance is negligible).	1	12	2025-11-13 20:06:22.330803+00	\N
a593ae32-e04e-4e0d-be2b-6a440f7f6f64	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_accel_motion	Accelerated Motion	Nonuniform motion involving a change in velocity.	5	9	2025-11-13 20:06:22.322394+00	\N
b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_avg_velocity_2d	Average Velocity (2D)	Resultant displacement divided by time ($\\vec{v}_{av} = \\Delta\\vec{d}_{R} / \\Delta t$).	2	9	2025-11-13 20:06:22.319911+00	\N
b341ac8a-5a51-44ea-acaa-d25047d77a5d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_avg_speed	Average Speed	Total distance divided by total time ($v_{av} = d/t$).	7	3	2025-11-13 20:06:22.306898+00	\N
b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_slope_vel_time	Slope of Velocity-Time Graph	Represents average acceleration.	0	13	2025-11-13 20:06:22.325999+00	\N
bff0139a-f332-433b-b234-d722e796e2a6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_avg_accel	Average Acceleration	The rate of change of velocity ($\\vec{a}_{av} = \\Delta\\vec{v} / \\Delta t$).	3	11	2025-11-13 20:06:22.32438+00	\N
c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_frame_of_ref	Frame of Reference	A coordinate system relative to which motion is observed.	1	10	2025-11-13 20:06:22.320737+00	\N
cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_inst_accel	Instantaneous Acceleration	Acceleration at a particular instant.	0	12	2025-11-13 20:06:22.325195+00	\N
d2d79951-5ba9-48e5-a52e-a4e3180a3b62	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_terminal_speed	Terminal Speed	Maximum constant speed reached by a falling object when air resistance balances gravity.	0	13	2025-11-13 20:06:22.331648+00	\N
d5972321-2d2b-433e-b43b-760522bfd99b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_kin_eq_2	Kinematic Equation (Displacement from Avg Velocity)	$\\Delta\\vec{d}=\\frac{1}{2}(\\vec{v}_{i}+\\vec{v}_{f})\\Delta t$	2	10	2025-11-13 20:06:22.333206+00	\N
d622f0b9-3e3a-46ba-85e5-aa06aec310cc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_derived_unit	Derived Unit	Units derived from base units (e.g., m/s).	8	1	2025-11-13 20:06:22.306022+00	\N
dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_relative_velocity	Relative Velocity	Velocity of an object relative to a specific frame of reference ($\\vec{v}_{AC} = \\vec{v}_{AB} + \\vec{v}_{BC}$).	0	11	2025-11-13 20:06:22.321569+00	\N
dec0deaf-d9b0-4823-ac49-811fc893abde	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_position	Position ($\\vec{d}$)	Distance and direction from a reference point.	8	2	2025-11-13 20:06:22.310735+00	\N
e0658139-bb9d-42a0-b2f8-93c63b3b0d98	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_graph_pos_time_accel	Position-Time Graph (Acceleration)	A curve (parabola) for uniform acceleration.	2	11	2025-11-13 20:06:22.326768+00	\N
e8fb18ed-8c01-451f-bc63-2567e08769dd	79f6869b-a9d1-4965-b864-dafd6a3faa6d	kp_inst_speed	Instantaneous Speed	Speed at a particular instant.	1	4	2025-11-13 20:06:22.307734+00	\N
9dd1e4cc-b2bd-4420-9972-b3ee50ffee01	c18d6d95-77ed-4b41-a833-dc5cddec74f4	halogens	Halogens	Elements in Group 17 of the periodic table, which are highly reactive non-metals that form salts with metals.	0	0	2025-11-24 07:34:14.219545+00	\N
0d586faa-0d57-448c-9bad-adb3d226ca2c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	eutrophication	Eutrophication	The process in which excess nutrients in a body of water cause a dense growth of plant life, such as algae.	0	0	2025-11-24 07:34:14.219545+00	\N
644b02cf-dc17-4ef5-b996-9ee9f2d826ce	c18d6d95-77ed-4b41-a833-dc5cddec74f4	synthesis_reaction	Synthesis Reaction	A reaction where two or more elements or compounds combine to form a single, more complex substance (A + B → C).	0	0	2025-11-24 07:34:14.219545+00	\N
9e6f6e21-867a-4bf8-9b2d-8e80ad2e421c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	metals	Metals	A class of elements, typically found on the left side of the periodic table's staircase line.	0	0	2025-11-24 07:34:14.219545+00	\N
005f56c9-d24d-45ec-b59b-ab4415c71814	c18d6d95-77ed-4b41-a833-dc5cddec74f4	international_system_of_units_si	International System of Units (SI)	The standardized system of measurement used by scientists worldwide, including base units like the metre (m), kilogram (kg), and second (s).	1	0	2025-11-24 07:34:14.219545+00	\N
a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_equations	Chemical Equations	A symbolic representation of a chemical reaction, showing reactants, products, and their states.	1	0	2025-11-24 07:34:14.219545+00	\N
f961bf35-afc8-4dce-876a-7e6f14108e29	c18d6d95-77ed-4b41-a833-dc5cddec74f4	intramolecular_forces	Intramolecular Forces	The forces that hold atoms together within a molecule, such as covalent bonds.	0	0	2025-11-24 07:34:14.219545+00	\N
0cfbe794-6522-4563-ae78-e6cdb0c540a2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	single_displacement_reaction	Single Displacement Reaction	A reaction in which one element in a compound is replaced by another, more reactive element (A + BC → AC + B).	1	0	2025-11-24 07:34:14.219545+00	\N
be5e4256-5c61-4b43-ace6-2cdef9cd4a17	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ionic_bond	Ionic Bond	A chemical bond formed by the transfer of valence electrons from one atom (usually a metal) to another (usually a non-metal), creating oppositely charged ions.	2	0	2025-11-24 07:34:14.219545+00	\N
22257e97-8a88-4665-87f5-a9d9c69d66b2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_change	Chemical Change	A change that alters the chemical composition of matter, resulting in the formation of one or more new substances, such as iron rusting.	1	0	2025-11-24 07:34:14.219545+00	\N
1284eb28-922c-4bca-9662-12150e3613da	c18d6d95-77ed-4b41-a833-dc5cddec74f4	periodic_trends	Periodic Trends	Predictable patterns in elemental properties that are observed across periods and down groups in the periodic table.	4	0	2025-11-24 07:34:14.219545+00	\N
8a9f80cc-f2c5-475b-bdd8-a42e94089093	c18d6d95-77ed-4b41-a833-dc5cddec74f4	alkali_metals	Alkali Metals	Elements in Group 1 of the periodic table, which are highly reactive metals with one valence electron.	0	0	2025-11-24 07:34:14.219545+00	\N
4db95075-7641-463c-b854-5d10ac13a13a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	modern_atomic_theory	Modern Atomic Theory	The current understanding of the atom, which modifies Dalton's theory to include the existence of subatomic particles, isotopes, and the possibility of nuclear reactions.	3	0	2025-11-24 07:34:14.219545+00	\N
c3a0f6ed-5c7e-4c46-b135-555a279f9670	c18d6d95-77ed-4b41-a833-dc5cddec74f4	properties_of_matter	Properties of Matter	Characteristics that help describe and identify matter.	0	0	2025-11-24 07:34:14.219545+00	\N
e9a33c37-4ab9-4e08-99bf-2a99287442d2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	matter	Matter	Anything that has mass and volume (takes up space). It is the fundamental component of the universe.	0	0	2025-11-24 07:34:14.219545+00	\N
f4bc3b56-1a4d-4965-9387-55fd28918dd1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	covalent_compounds	Covalent Compounds	Compounds formed through covalent bonds, typically between non-metals, characterized by low melting points and poor electrical conductivity. Also known as molecular compounds.	0	0	2025-11-24 07:34:14.219545+00	\N
039329d6-e56a-4e5e-af23-7779df97f7b6	c18d6d95-77ed-4b41-a833-dc5cddec74f4	incomplete_combustion	Incomplete Combustion	A combustion reaction in the absence of sufficient oxygen, leading to the formation of carbon monoxide (CO) and water.	0	0	2025-11-24 07:34:14.219545+00	\N
7ed53540-38ec-42bb-82af-ef61c751c004	c18d6d95-77ed-4b41-a833-dc5cddec74f4	alkaline_earth_metals	Alkaline Earth Metals	Elements in Group 2 of the periodic table, which are reactive metals with two valence electrons.	0	0	2025-11-24 07:34:14.219545+00	\N
ed556f7c-4ef2-4390-b3de-b9c185a0b7f1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	lewis_structures	Lewis Structures	Diagrams that show the bonding between atoms of a molecule and the lone pairs of electrons that may exist in the molecule.	1	0	2025-11-24 07:34:14.219545+00	\N
cdc61a35-0b01-4101-9e41-cdb32510c3a3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	transition_elements	Transition Elements	Elements in Groups 3 through 12 of the periodic table.	0	0	2025-11-24 07:34:14.219545+00	\N
c652b196-322b-4ee0-b263-abd18fe13b1d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	complete_combustion	Complete Combustion	A combustion reaction with sufficient oxygen, where a carbon-containing compound produces carbon dioxide (CO2) and water.	0	0	2025-11-24 07:34:14.219545+00	\N
b2802bcc-4594-4f29-ac85-6f4543e1ed29	c18d6d95-77ed-4b41-a833-dc5cddec74f4	metallic_bonding	Metallic Bonding	A type of chemical bonding that arises from the electrostatic attractive force between conduction electrons (in the form of an electron sea) and positively charged metal ions.	0	0	2025-11-24 07:34:14.219545+00	\N
7006ee00-0086-462e-9291-e1dbc4c119f1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_compounds	Chemical Compounds	A substance formed when two or more chemical elements are chemically bonded together.	0	0	2025-11-24 07:34:14.219545+00	\N
23566452-7649-4002-be86-4be63211aa0f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ionic_compounds	Ionic Compounds	Compounds formed through ionic bonds, typically between a metal and a non-metal, characterized by high melting points and electrical conductivity when molten or dissolved.	0	0	2025-11-24 07:34:14.219545+00	\N
33ee5649-eb89-403f-b2ea-9591452df4dd	c18d6d95-77ed-4b41-a833-dc5cddec74f4	decomposition_reaction	Decomposition Reaction	A reaction where a single compound breaks down into two or more simpler elements or compounds (C → A + B).	0	0	2025-11-24 07:34:14.219545+00	\N
7fcd7de4-2594-4e15-befb-91776b2cc407	c18d6d95-77ed-4b41-a833-dc5cddec74f4	rules_for_significant_digits_in_calculations	Rules for Significant Digits in Calculations	Rules for determining the number of significant digits to report in the answer of a calculation involving multiplication, division, addition, or subtraction.	2	0	2025-11-24 07:34:14.219545+00	\N
4f90bd49-8165-431c-bdc9-bf708f56e3d3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	covalent_bond	Covalent Bond	A chemical bond formed by the sharing of electron pairs between atoms, typically non-metals.	0	0	2025-11-24 07:34:14.219545+00	\N
c3f5120d-f32c-4b94-8eae-5c540039b78a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	lewis_structure	Lewis Structure	A simplified diagram that represents an element's valence electrons as dots placed around the atomic symbol.	3	0	2025-11-24 07:34:14.219545+00	\N
d036c0ed-76bc-46be-ae71-20047a940cd0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	accuracy_vs_precision	Accuracy vs. Precision	A concept that distinguishes between how close a measurement is to the true value (accuracy) and how close a series of measurements are to each other (precision).	1	0	2025-11-24 07:34:14.219545+00	\N
ee8253d0-ef7c-4704-ac3f-b3e7507d86a6	c18d6d95-77ed-4b41-a833-dc5cddec74f4	combustion_reaction	Combustion Reaction	The reaction of a compound or element with oxygen, typically producing heat and light, to form the most common oxides of the elements involved.	0	0	2025-11-24 07:34:14.219545+00	\N
0f5eed39-eded-4ab6-910e-c4c4aef03147	c18d6d95-77ed-4b41-a833-dc5cddec74f4	noble_gases	Noble Gases	Elements in Group 18 of the periodic table, which are highly unreactive due to having a full outer energy level of electrons.	4	0	2025-11-24 07:34:14.219545+00	\N
48be6756-72b9-4c9f-8608-3cbadf84891f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ionization_energy	Ionization Energy	The energy required to remove an electron from a neutral atom in its gaseous state.	3	0	2025-11-24 07:34:14.219545+00	\N
967128a0-6975-492f-a394-e456f3d2927f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	anion	Anion	A negatively charged ion formed when an atom gains one or more electrons.	0	0	2025-11-24 07:34:14.219545+00	\N
b7ea4228-050d-418c-8824-d3d24efb6404	c18d6d95-77ed-4b41-a833-dc5cddec74f4	physical_change	Physical Change	A change that affects the physical appearance of matter but not its chemical composition, such as a change of state (e.g., ice melting).	1	0	2025-11-24 07:34:14.219545+00	\N
9f50dba5-bdc5-406b-98b6-b2b336e3d05b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	mass_number_a	Mass Number (A)	The total number of protons and neutrons in the nucleus of an atom.	2	0	2025-11-24 07:34:14.219545+00	\N
7c1903dd-7ba0-4293-8ba1-f9d0473ef7b2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_bonds	Chemical Bonds	The forces that attract atoms to each other in compounds, involving the interaction of valence electrons.	0	0	2025-11-24 07:34:14.219545+00	\N
8bc0947c-fc7b-4ac9-b7e4-75de9cd8501c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	bohr_rutherford_diagram	Bohr-Rutherford Diagram	A diagram that represents the arrangement of electrons in an atom, showing the nucleus and concentric circles for each energy level with dots representing electrons.	2	0	2025-11-24 07:34:14.219545+00	\N
b217f16e-51b0-4121-a8e6-8d62ab84cd57	c18d6d95-77ed-4b41-a833-dc5cddec74f4	mixtures	Mixtures	A physical combination of two or more kinds of matter where each component retains its own identity and properties.	0	0	2025-11-24 07:34:14.219545+00	\N
04f0e698-00ba-4dbc-af60-8cc83833fb43	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_formula	Chemical Formula	A representation of a substance using symbols for its constituent elements and subscripts to indicate the number of atoms of each element.	1	0	2025-11-24 07:34:14.219545+00	\N
e704edef-1bbf-4ab8-86df-08cc199575f5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	qualitative_properties	Qualitative Properties	A property that can be described with words but not measured numerically, such as colour, odour, or texture.	0	0	2025-11-24 07:34:14.219545+00	\N
7e801f3f-b8d3-40f9-b251-8b43637ea597	c18d6d95-77ed-4b41-a833-dc5cddec74f4	heterogeneous_mixtures	Heterogeneous Mixtures	A mixture in which the different components are clearly visible and not uniformly distributed.	0	0	2025-11-24 07:34:14.219545+00	\N
46660a32-049e-4e5f-ab06-83a887567478	c18d6d95-77ed-4b41-a833-dc5cddec74f4	intermolecular_forces	Intermolecular Forces	The weak forces of attraction or repulsion that act between neighboring molecules, affecting properties like boiling and melting points.	4	0	2025-11-24 07:34:14.219545+00	\N
e90d1d47-7c6b-451f-9a20-c856c2287793	c18d6d95-77ed-4b41-a833-dc5cddec74f4	balanced_chemical_equations	Balanced Chemical Equations	A chemical equation in which the number of each type of atom is the same on both the reactant and product sides, satisfying the Law of Conservation of Mass.	3	0	2025-11-24 07:34:14.219545+00	\N
023c64de-a174-4a74-874a-79c9333812a8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	atomic_radius	Atomic Radius	A measure of the size of an atom, defined as the distance from its nucleus to the approximate outer boundary of its electron cloud.	0	0	2025-11-24 07:34:14.219545+00	\N
2acf682f-81ba-4ea3-887d-a01f89456fc0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	electron_affinity	Electron Affinity	The change in energy that occurs when an electron is added to a neutral atom to form a negative ion.	3	0	2025-11-24 07:34:14.219545+00	\N
dfec3acf-4e84-4e1f-a5bb-9f5851ace059	c18d6d95-77ed-4b41-a833-dc5cddec74f4	pure_substances	Pure Substances	A substance with a definite and constant composition that does not change in response to physical changes.	0	0	2025-11-24 07:34:14.219545+00	\N
000693e1-5479-4dd8-a63f-4535e7927c96	c18d6d95-77ed-4b41-a833-dc5cddec74f4	classifying_chemical_reactions	Classifying Chemical Reactions	The practice of grouping chemical reactions into different types based on their patterns, such as synthesis or decomposition, to predict outcomes.	0	0	2025-11-24 07:34:14.219545+00	\N
9f3e2e71-93a7-4cb6-bcb4-66444cb63aa4	c18d6d95-77ed-4b41-a833-dc5cddec74f4	cation	Cation	A positively charged ion formed when an atom loses one or more electrons.	0	0	2025-11-24 07:34:14.219545+00	\N
034af9f5-7609-4afe-b55a-22c567b3eeae	c18d6d95-77ed-4b41-a833-dc5cddec74f4	mole_mass_conversions	Mole-Mass Conversions	The calculation to convert between the amount of a substance in moles and its mass using the molar mass.	6	0	2025-11-24 07:34:14.219545+00	\N
513b8f18-4b0c-4c7a-8c84-dd2dd5ffcac4	c18d6d95-77ed-4b41-a833-dc5cddec74f4	mass_spectrometer	Mass Spectrometer	An analytical instrument that measures the mass-to-charge ratio of ions, used to determine the mass and relative abundance of isotopes.	0	0	2025-11-24 07:34:14.219545+00	\N
8c405318-6b27-45e9-a672-22db79ea406d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	mole_particle_conversions	Mole-Particle Conversions	The calculation to convert between the amount of a substance in moles and the number of constituent particles using Avogadro's constant.	2	0	2025-11-24 07:34:14.219545+00	\N
4e3fd033-be91-4441-a8e3-effccde6c247	c18d6d95-77ed-4b41-a833-dc5cddec74f4	atomic_nucleus	Atomic Nucleus	The central core of an atom, composed of protons and neutrons, containing most of the atom's mass.	1	0	2025-11-24 07:34:14.219545+00	\N
bad9a3fc-a0e7-473b-9e77-5973aadd86b4	c18d6d95-77ed-4b41-a833-dc5cddec74f4	compound	Compound	A pure substance formed when two or more elements are chemically combined in a fixed ratio.	0	0	2025-11-24 07:34:14.219545+00	\N
4504df02-da3f-4db7-b1ba-8328682ef48e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	non_metals	Non-metals	A class of elements, found on the right side of the periodic table's staircase line.	0	0	2025-11-24 07:34:14.219545+00	\N
2fb63cbc-a0d0-4925-8992-2128e165abd6	c18d6d95-77ed-4b41-a833-dc5cddec74f4	nuclear_reaction	Nuclear Reaction	A reaction that involves changes within the nucleus of an atom, responsible for the energy of stars.	0	0	2025-11-24 07:34:14.219545+00	\N
b8bb0b83-db9d-4852-9fdb-b99615bef4c3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	metalloids	Metalloids	Elements located along the staircase line of the periodic table that have properties intermediate between those of metals and non-metals.	0	0	2025-11-24 07:34:14.219545+00	\N
c45425f5-4e5f-4a00-b22d-f4b4f75ffb2a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	homogeneous_mixtures	Homogeneous Mixtures	A mixture in which the components are uniformly blended, appearing as a single substance. Also known as a solution.	0	0	2025-11-24 07:34:14.219545+00	\N
080408b6-2e23-42f9-ac8f-ee896f167e44	c18d6d95-77ed-4b41-a833-dc5cddec74f4	uncertainty_in_measurement	Uncertainty in Measurement	The inherent impossibility of measuring a quantity with complete certainty, arising from limitations of the measuring device and the observer.	0	3	2025-11-24 07:34:14.219545+00	\N
0b0cc80c-b8cd-4aa0-8a4f-6b83a4beb821	c18d6d95-77ed-4b41-a833-dc5cddec74f4	avogadros_constant	Avogadro's Constant	The number of constituent particles (atoms, molecules, or ions) in one mole of a substance. Its value is approximately 6.022 x 10^23 mol⁻¹.	0	4	2025-11-24 07:34:14.219545+00	\N
0b6934fa-1d81-47be-a7e7-bf00a0e8d672	c18d6d95-77ed-4b41-a833-dc5cddec74f4	groups_periodic_table	Groups (Periodic Table)	The vertical columns in the periodic table, where elements in a group share similar chemical properties and the same number of valence electrons.	0	4	2025-11-24 07:34:14.219545+00	\N
133f59c8-33de-4a31-87ec-1b0263e36684	c18d6d95-77ed-4b41-a833-dc5cddec74f4	electronegativity_difference	Electronegativity Difference	The difference in electronegativity values between two atoms in a bond, used to predict the bond type (ionic, polar covalent, or covalent).	1	4	2025-11-24 07:34:14.219545+00	\N
19667dda-e18c-4392-82d2-b3d3d43f086b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ion	Ion	A charged particle formed when a neutral atom or molecule gains or loses one or more electrons.	2	2	2025-11-24 07:34:14.219545+00	\N
2016da24-385f-4b89-a9fa-7a75fca6895d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	neutron	Neutron	A neutral subatomic particle (charge of 0) located in the atomic nucleus with a relative mass of approximately 1 atomic mass unit.	0	2	2025-11-24 07:34:14.219545+00	\N
21d0eba5-717e-4be9-a730-a39707edaafe	c18d6d95-77ed-4b41-a833-dc5cddec74f4	skeleton_equations	Skeleton Equations	A chemical equation that uses chemical formulas instead of names to represent reactants and products, and indicates their physical states.	1	2	2025-11-24 07:34:14.219545+00	\N
228a3e15-0186-487f-b5e9-b8167f2a530f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	element	Element	The basic substances that make up all matter, where each element is made up of only a single kind of atom.	0	6	2025-11-24 07:34:14.219545+00	\N
23c7d950-0603-4515-82d5-2fd2c2477bb0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	periodic_table	Periodic Table	A tabular arrangement of the chemical elements, ordered by their atomic number, electron configuration, and recurring chemical properties.	3	1	2025-11-24 07:34:14.219545+00	\N
273db938-5cc8-4b34-8eab-ca7c0228b69d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	average_atomic_mass	Average Atomic Mass	The weighted average mass of an element's naturally occurring isotopes, taking into account the abundance of each isotope. This is the mass value shown on the periodic table.	4	2	2025-11-24 07:34:14.219545+00	\N
28c26e6c-ea10-4e55-b961-897e6113674f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	metal_activity_series	Metal Activity Series	A ranked list of metals from most reactive to least reactive, used to predict whether a metal will displace another metal from a compound in a single displacement reaction.	0	1	2025-11-24 07:34:14.219545+00	\N
2c849279-4241-4d73-82ca-e720dfdb4c1d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	stable_octet	Stable Octet	A stable electron arrangement where an atom's outermost energy level is completely filled, typically with eight valence electrons.	3	1	2025-11-24 07:34:14.219545+00	\N
321ed919-f6e7-45e7-8e15-70dc04966054	c18d6d95-77ed-4b41-a833-dc5cddec74f4	valence	Valence	The combining capacity of an element, representing the number of electrons an atom can lose, gain, or share to form chemical bonds.	0	1	2025-11-24 07:34:14.219545+00	\N
36f222f3-edbf-4515-8187-f65e53de0af4	c18d6d95-77ed-4b41-a833-dc5cddec74f4	electron_energy_levels	Electron Energy Levels	Fixed, three-dimensional regions of space around an atomic nucleus where electrons are restricted to move.	1	5	2025-11-24 07:34:14.219545+00	\N
464b5adc-4ee5-468b-aedc-638ac8cbc498	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_reaction	Chemical Reaction	Interactions where elements and compounds interact with one another to form new substances.	0	1	2025-11-24 07:34:14.219545+00	\N
4afa5162-a1e5-474c-b761-b53d5987199a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	balancing_chemical_equations	Balancing Chemical Equations	The process of adding coefficients in front of chemical formulas in a skeleton equation to ensure the number of atoms for each element is equal on both sides.	2	1	2025-11-24 07:34:14.219545+00	\N
4f5767af-a51f-4c9b-ae88-4bfa70a9e090	c18d6d95-77ed-4b41-a833-dc5cddec74f4	word_equations	Word Equations	A chemical equation that identifies the reactants and products by their names.	0	3	2025-11-24 07:34:14.219545+00	\N
5109e661-34b4-4136-9e88-dbb049e4dd1a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	quantitative_properties	Quantitative Properties	A property that can be measured and expressed with a numerical value, such as density, mass, or temperature.	0	1	2025-11-24 07:34:14.219545+00	\N
5e899e6c-3ab7-49c2-94bc-97128921ca0b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	octet_rule	Octet Rule	The principle that atoms tend to bond in such a way that they each have eight electrons in their valence shell, giving them the same electronic configuration as a noble gas.	0	5	2025-11-24 07:34:14.219545+00	\N
6dbb9dd7-71df-4e31-b019-a9d1b4367466	c18d6d95-77ed-4b41-a833-dc5cddec74f4	halogen_activity_series	Halogen Activity Series	A ranked list of halogens by reactivity (F > Cl > Br > I) used to predict the outcome of single displacement reactions involving halogens.	0	1	2025-11-24 07:34:14.219545+00	\N
7826e10e-5679-467b-8c46-54573873de21	c18d6d95-77ed-4b41-a833-dc5cddec74f4	significant_digits	Significant Digits	The digits in a measurement that are known with certainty plus one final, estimated digit. They indicate the precision of a measurement.	1	1	2025-11-24 07:34:14.219545+00	\N
818d8a1c-db56-4ca0-a36a-d31e04d330ba	c18d6d95-77ed-4b41-a833-dc5cddec74f4	valence_electrons	Valence Electrons	The electrons that occupy the outermost energy level of an atom and are involved in chemical bonding and reactions.	2	3	2025-11-24 07:34:14.219545+00	\N
83051056-852e-488d-838b-60378a5ab269	c18d6d95-77ed-4b41-a833-dc5cddec74f4	daltons_atomic_theory	Dalton's Atomic Theory	An early atomic theory stating that all matter is made of indivisible atoms, atoms of an element are identical, and atoms combine in specific proportions to form compounds.	2	1	2025-11-24 07:34:14.219545+00	\N
8d1ed2d9-9781-4482-ab7e-5656d9662652	c18d6d95-77ed-4b41-a833-dc5cddec74f4	isotopes	Isotopes	Atoms of the same element that have the same number of protons but a different number of neutrons, resulting in different mass numbers.	2	4	2025-11-24 07:34:14.219545+00	\N
92382f9e-f3b4-426f-805a-cee1145787fa	c18d6d95-77ed-4b41-a833-dc5cddec74f4	the_mole	The Mole	The SI unit for the amount of a substance, defined as containing exactly 6.022 x 10^23 elementary entities (particles).	1	3	2025-11-24 07:34:14.219545+00	\N
97c705f8-22db-4d00-b6ca-d8778da611dd	c18d6d95-77ed-4b41-a833-dc5cddec74f4	product	Product	A substance that is formed in a chemical reaction.	0	1	2025-11-24 07:34:14.219545+00	\N
9afb1f1f-9d45-423d-b331-f0de28ad9498	c18d6d95-77ed-4b41-a833-dc5cddec74f4	law_of_definite_proportion	Law of Definite Proportion	A scientific law stating that elements always combine to form compounds in fixed proportions by mass.	0	2	2025-11-24 07:34:14.219545+00	\N
9d42e1af-d1c3-4f7d-ad4e-c894d20cd878	c18d6d95-77ed-4b41-a833-dc5cddec74f4	periodic_law	Periodic Law	The principle that the chemical and physical properties of the elements repeat in a regular, periodic pattern when they are arranged by increasing atomic number.	2	2	2025-11-24 07:34:14.219545+00	\N
a6bc1e6a-76ee-4dfc-bad0-474661023560	c18d6d95-77ed-4b41-a833-dc5cddec74f4	periods_periodic_table	Periods (Periodic Table)	The horizontal rows in the periodic table, where the period number corresponds to the number of electron energy levels.	0	6	2025-11-24 07:34:14.219545+00	\N
acf03374-c7a9-4e9f-8378-50d85cdfb926	c18d6d95-77ed-4b41-a833-dc5cddec74f4	electronegativity	Electronegativity	A measure of an atom's ability to attract shared electrons in a chemical bond.	0	5	2025-11-24 07:34:14.219545+00	\N
af9c8a49-54be-414c-b2d7-b6c1eebbfd86	c18d6d95-77ed-4b41-a833-dc5cddec74f4	molar_mass	Molar Mass	The mass of one mole of a substance, expressed in grams per mole (g/mol). It is numerically equal to the substance's average atomic or molecular mass in atomic mass units.	5	1	2025-11-24 07:34:14.219545+00	\N
b2f7d280-4509-46a7-beb4-765a8a857d5c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	polar_covalent_bond	Polar Covalent Bond	A type of covalent bond where electrons are shared unequally between two atoms due to a significant difference in electronegativity, creating partial positive and negative charges.	2	2	2025-11-24 07:34:14.219545+00	\N
b932e5fc-ef40-4a50-b7f3-f2ea1944cae0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	chemical_property	Chemical Property	A property that is observed when a substance undergoes a chemical change, converting it into a new substance. Examples include reactivity with acid and flammability.	0	1	2025-11-24 07:34:14.219545+00	\N
c1dde2a3-4c52-4d2e-8fd6-11e0329d40ba	c18d6d95-77ed-4b41-a833-dc5cddec74f4	atomic_mass_unit	Atomic Mass Unit	A unit of mass for expressing atomic and molecular weights, defined as one-twelfth of the mass of a single carbon-12 atom.	0	3	2025-11-24 07:34:14.219545+00	\N
c327243c-bf6c-4a4a-8ccf-bc9fb2371214	c18d6d95-77ed-4b41-a833-dc5cddec74f4	electron	Electron	A negatively charged subatomic particle (1-) that occupies the space surrounding the atomic nucleus and has a mass considered to be approximately zero for atomic mass calculations.	0	6	2025-11-24 07:34:14.219545+00	\N
d133a2ea-5af9-4d34-a757-1906c33a5914	c18d6d95-77ed-4b41-a833-dc5cddec74f4	law_of_conservation_of_mass	Law of Conservation of Mass	The principle that matter can be neither created nor destroyed in a chemical reaction, meaning the mass of the products equals the mass of the reactants.	0	4	2025-11-24 07:34:14.219545+00	\N
d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	atom	Atom	The smallest particle of an element that still retains the identity and properties of the element.	1	5	2025-11-24 07:34:14.219545+00	\N
d60a6e19-8692-4f5c-9bc8-516308754ae2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	reactant	Reactant	A substance that undergoes a chemical reaction.	0	1	2025-11-24 07:34:14.219545+00	\N
de17b869-c87c-431f-8e65-fac239ffd712	c18d6d95-77ed-4b41-a833-dc5cddec74f4	proton	Proton	A positively charged subatomic particle (1+) located in the atomic nucleus with a relative mass of approximately 1 atomic mass unit.	0	11	2025-11-24 07:34:14.219545+00	\N
e0247469-39ea-4d8b-8ceb-e56ff8c800e9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	physical_property	Physical Property	A property that can be observed without changing the chemical identity of the substance, such as color, density, or boiling point.	0	1	2025-11-24 07:34:14.219545+00	\N
e0f667c1-6299-4428-9c05-d7640cc34fc4	c18d6d95-77ed-4b41-a833-dc5cddec74f4	isotopic_abundance	Isotopic Abundance	The relative amount in which each isotope of an element is present in a naturally occurring sample, often expressed as a percentage.	3	3	2025-11-24 07:34:14.219545+00	\N
e2e7a557-986e-4545-8037-886ab96fc6c7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	atomic_number_z	Atomic Number (Z)	The number of protons in the nucleus of an atom, which uniquely identifies an element.	1	9	2025-11-24 07:34:14.219545+00	\N
ec48015c-776b-4bc2-9d39-9c2c22ceb2df	c18d6d95-77ed-4b41-a833-dc5cddec74f4	polar_molecules	Polar Molecules	Molecules that have a net dipole moment due to the presence of polar bonds and an asymmetrical shape, resulting in a partial positive and a partial negative end.	3	1	2025-11-24 07:34:14.219545+00	\N
fec31188-16ba-4bdb-aa84-7080dc0fd7dc	c18d6d95-77ed-4b41-a833-dc5cddec74f4	molecular_shape	Molecular Shape	The three-dimensional arrangement of atoms within a molecule, determined by the arrangement of electron pairs to minimize repulsion.	0	2	2025-11-24 07:34:14.219545+00	\N
\.


--
-- Data for Name: prerequisites; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.prerequisites (graph_id, from_node_id, to_node_id, weight, created_at) FROM stdin;
79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	ebdea86b-4b32-4edb-9b93-f13e64300bff	1	2025-11-13 20:06:22.370202+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	1	2025-11-13 20:06:22.37229+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	1	2025-11-13 20:06:22.373096+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	b341ac8a-5a51-44ea-acaa-d25047d77a5d	1	2025-11-13 20:06:22.373818+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	1a161ca5-68e2-4c97-8850-85f7c80aac24	ebdea86b-4b32-4edb-9b93-f13e64300bff	1	2025-11-13 20:06:22.374486+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	b341ac8a-5a51-44ea-acaa-d25047d77a5d	1	2025-11-13 20:06:22.375138+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	6675f374-dd03-41c2-8796-7e81999cc075	1	2025-11-13 20:06:22.375785+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	dec0deaf-d9b0-4823-ac49-811fc893abde	1a161ca5-68e2-4c97-8850-85f7c80aac24	1	2025-11-13 20:06:22.37645+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	448fef63-5446-41a9-b188-83a57b2d586f	dec0deaf-d9b0-4823-ac49-811fc893abde	1	2025-11-13 20:06:22.377082+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	448fef63-5446-41a9-b188-83a57b2d586f	1	2025-11-13 20:06:22.377694+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	6cb12ce7-228f-40f4-87c4-185b110e32b7	1	2025-11-13 20:06:22.378325+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	3fe283af-0a1a-4190-95b2-4322066bb104	1	2025-11-13 20:06:22.379006+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	182ddcaa-29bf-4484-8c6c-b18496d59832	6cb12ce7-228f-40f4-87c4-185b110e32b7	1	2025-11-13 20:06:22.379621+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	182ddcaa-29bf-4484-8c6c-b18496d59832	1	2025-11-13 20:06:22.380243+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	448fef63-5446-41a9-b188-83a57b2d586f	1	2025-11-13 20:06:22.380787+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	273ec2d4-2aa9-47a5-accc-02f852edf5e4	448fef63-5446-41a9-b188-83a57b2d586f	1	2025-11-13 20:06:22.381414+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	1a161ca5-68e2-4c97-8850-85f7c80aac24	1	2025-11-13 20:06:22.381989+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	60d09626-84eb-4770-8ec2-5ae442c65ade	1	2025-11-13 20:06:22.382796+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	273ec2d4-2aa9-47a5-accc-02f852edf5e4	1	2025-11-13 20:06:22.383402+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	1109f07f-9d32-408c-999c-73dbfb2d88cc	1	2025-11-13 20:06:22.383967+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	273ec2d4-2aa9-47a5-accc-02f852edf5e4	1	2025-11-13 20:06:22.384541+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	6cb12ce7-228f-40f4-87c4-185b110e32b7	1	2025-11-13 20:06:22.385248+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	1	2025-11-13 20:06:22.385818+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	1	2025-11-13 20:06:22.386383+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	20994d2d-564a-48b6-b508-1bc4ca91ba20	1	2025-11-13 20:06:22.387019+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	6cb12ce7-228f-40f4-87c4-185b110e32b7	1	2025-11-13 20:06:22.387634+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	1	2025-11-13 20:06:22.388249+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	bff0139a-f332-433b-b234-d722e796e2a6	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	1	2025-11-13 20:06:22.388813+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	bff0139a-f332-433b-b234-d722e796e2a6	1	2025-11-13 20:06:22.389459+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	182ddcaa-29bf-4484-8c6c-b18496d59832	1	2025-11-13 20:06:22.390112+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	bff0139a-f332-433b-b234-d722e796e2a6	1	2025-11-13 20:06:22.390734+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	1	2025-11-13 20:06:22.391564+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	1	2025-11-13 20:06:22.392237+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	538a4f93-25b2-4b30-8d1e-ece54261d891	1	2025-11-13 20:06:22.392961+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	e8fb18ed-8c01-451f-bc63-2567e08769dd	1	2025-11-13 20:06:22.393569+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	bff0139a-f332-433b-b234-d722e796e2a6	1	2025-11-13 20:06:22.39418+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	1	2025-11-13 20:06:22.394792+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	80495392-972a-42ec-a6ec-10e777152993	1	2025-11-13 20:06:22.395421+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	1	2025-11-13 20:06:22.39605+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	1	2025-11-13 20:06:22.396672+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	8a4f2710-f341-4455-9680-9665e0a584d6	bff0139a-f332-433b-b234-d722e796e2a6	1	2025-11-13 20:06:22.39728+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d5972321-2d2b-433e-b43b-760522bfd99b	5649bae7-fb7f-436c-a34e-5c085a6a014d	1	2025-11-13 20:06:22.397977+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	8a4f2710-f341-4455-9680-9665e0a584d6	1	2025-11-13 20:06:22.398695+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	d5972321-2d2b-433e-b43b-760522bfd99b	1	2025-11-13 20:06:22.399413+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	8a4f2710-f341-4455-9680-9665e0a584d6	1	2025-11-13 20:06:22.40021+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	d5972321-2d2b-433e-b43b-760522bfd99b	1	2025-11-13 20:06:22.400771+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	7c217eaf-391d-42b3-983c-2f2ef0b9013c	8a4f2710-f341-4455-9680-9665e0a584d6	1	2025-11-13 20:06:22.401364+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	7c217eaf-391d-42b3-983c-2f2ef0b9013c	d5972321-2d2b-433e-b43b-760522bfd99b	1	2025-11-13 20:06:22.401978+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	8a4f2710-f341-4455-9680-9665e0a584d6	1	2025-11-13 20:06:22.402556+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	d5972321-2d2b-433e-b43b-760522bfd99b	1	2025-11-13 20:06:22.403202+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	20865509-851f-4525-bc9a-fa7111c3c194	1	2025-11-13 20:06:22.40379+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	1	2025-11-13 20:06:22.404464+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	7c217eaf-391d-42b3-983c-2f2ef0b9013c	1	2025-11-13 20:06:22.405139+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	80495392-972a-42ec-a6ec-10e777152993	1	2025-11-13 20:06:22.40577+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0247469-39ea-4d8b-8ceb-e56ff8c800e9	b7ea4228-050d-418c-8824-d3d24efb6404	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	b932e5fc-ef40-4a50-b7f3-f2ea1944cae0	22257e97-8a88-4665-87f5-a9d9c69d66b2	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	080408b6-2e23-42f9-ac8f-ee896f167e44	7826e10e-5679-467b-8c46-54573873de21	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	080408b6-2e23-42f9-ac8f-ee896f167e44	d036c0ed-76bc-46be-ae71-20047a940cd0	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	7826e10e-5679-467b-8c46-54573873de21	7fcd7de4-2594-4e15-befb-91776b2cc407	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	5109e661-34b4-4136-9e88-dbb049e4dd1a	005f56c9-d24d-45ec-b59b-ab4415c71814	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	228a3e15-0186-487f-b5e9-b8167f2a530f	d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	83051056-852e-488d-838b-60378a5ab269	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	d133a2ea-5af9-4d34-a757-1906c33a5914	83051056-852e-488d-838b-60378a5ab269	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	9afb1f1f-9d45-423d-b331-f0de28ad9498	83051056-852e-488d-838b-60378a5ab269	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	83051056-852e-488d-838b-60378a5ab269	4db95075-7641-463c-b854-5d10ac13a13a	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	de17b869-c87c-431f-8e65-fac239ffd712	4e3fd033-be91-4441-a8e3-effccde6c247	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	2016da24-385f-4b89-a9fa-7a75fca6895d	4e3fd033-be91-4441-a8e3-effccde6c247	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	de17b869-c87c-431f-8e65-fac239ffd712	e2e7a557-986e-4545-8037-886ab96fc6c7	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e2e7a557-986e-4545-8037-886ab96fc6c7	9f50dba5-bdc5-406b-98b6-b2b336e3d05b	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	2016da24-385f-4b89-a9fa-7a75fca6895d	9f50dba5-bdc5-406b-98b6-b2b336e3d05b	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e2e7a557-986e-4545-8037-886ab96fc6c7	8d1ed2d9-9781-4482-ab7e-5656d9662652	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e2e7a557-986e-4545-8037-886ab96fc6c7	9d42e1af-d1c3-4f7d-ad4e-c894d20cd878	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	9d42e1af-d1c3-4f7d-ad4e-c894d20cd878	23c7d950-0603-4515-82d5-2fd2c2477bb0	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	c327243c-bf6c-4a4a-8ccf-bc9fb2371214	36f222f3-edbf-4515-8187-f65e53de0af4	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	a6bc1e6a-76ee-4dfc-bad0-474661023560	36f222f3-edbf-4515-8187-f65e53de0af4	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	36f222f3-edbf-4515-8187-f65e53de0af4	818d8a1c-db56-4ca0-a36a-d31e04d330ba	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b6934fa-1d81-47be-a7e7-bf00a0e8d672	818d8a1c-db56-4ca0-a36a-d31e04d330ba	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	36f222f3-edbf-4515-8187-f65e53de0af4	8bc0947c-fc7b-4ac9-b7e4-75de9cd8501c	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	818d8a1c-db56-4ca0-a36a-d31e04d330ba	c3f5120d-f32c-4b94-8eae-5c540039b78a	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	818d8a1c-db56-4ca0-a36a-d31e04d330ba	2c849279-4241-4d73-82ca-e720dfdb4c1d	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	2c849279-4241-4d73-82ca-e720dfdb4c1d	0f5eed39-eded-4ab6-910e-c4c4aef03147	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	19667dda-e18c-4392-82d2-b3d3d43f086b	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	23c7d950-0603-4515-82d5-2fd2c2477bb0	1284eb28-922c-4bca-9662-12150e3613da	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	19667dda-e18c-4392-82d2-b3d3d43f086b	48be6756-72b9-4c9f-8608-3cbadf84891f	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	19667dda-e18c-4392-82d2-b3d3d43f086b	2acf682f-81ba-4ea3-887d-a01f89456fc0	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	acf03374-c7a9-4e9f-8378-50d85cdfb926	133f59c8-33de-4a31-87ec-1b0263e36684	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	133f59c8-33de-4a31-87ec-1b0263e36684	be5e4256-5c61-4b43-ace6-2cdef9cd4a17	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	5e899e6c-3ab7-49c2-94bc-97128921ca0b	be5e4256-5c61-4b43-ace6-2cdef9cd4a17	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	5e899e6c-3ab7-49c2-94bc-97128921ca0b	ed556f7c-4ef2-4390-b3de-b9c185a0b7f1	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2f7d280-4509-46a7-beb4-765a8a857d5c	ec48015c-776b-4bc2-9d39-9c2c22ceb2df	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	fec31188-16ba-4bdb-aa84-7080dc0fd7dc	ec48015c-776b-4bc2-9d39-9c2c22ceb2df	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	ec48015c-776b-4bc2-9d39-9c2c22ceb2df	46660a32-049e-4e5f-ab06-83a887567478	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	321ed919-f6e7-45e7-8e15-70dc04966054	04f0e698-00ba-4dbc-af60-8cc83833fb43	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	133f59c8-33de-4a31-87ec-1b0263e36684	b2f7d280-4509-46a7-beb4-765a8a857d5c	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	5e899e6c-3ab7-49c2-94bc-97128921ca0b	b2f7d280-4509-46a7-beb4-765a8a857d5c	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	464b5adc-4ee5-468b-aedc-638ac8cbc498	a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	d60a6e19-8692-4f5c-9bc8-516308754ae2	a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	97c705f8-22db-4d00-b6ca-d8778da611dd	a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	4f5767af-a51f-4c9b-ae88-4bfa70a9e090	21d0eba5-717e-4be9-a730-a39707edaafe	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	21d0eba5-717e-4be9-a730-a39707edaafe	4afa5162-a1e5-474c-b761-b53d5987199a	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	d133a2ea-5af9-4d34-a757-1906c33a5914	4afa5162-a1e5-474c-b761-b53d5987199a	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	4afa5162-a1e5-474c-b761-b53d5987199a	e90d1d47-7c6b-451f-9a20-c856c2287793	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	28c26e6c-ea10-4e55-b961-897e6113674f	0cfbe794-6522-4563-ae78-e6cdb0c540a2	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	6dbb9dd7-71df-4e31-b019-a9d1b4367466	0cfbe794-6522-4563-ae78-e6cdb0c540a2	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	c1dde2a3-4c52-4d2e-8fd6-11e0329d40ba	273db938-5cc8-4b34-8eab-ca7c0228b69d	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	8d1ed2d9-9781-4482-ab7e-5656d9662652	e0f667c1-6299-4428-9c05-d7640cc34fc4	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0f667c1-6299-4428-9c05-d7640cc34fc4	273db938-5cc8-4b34-8eab-ca7c0228b69d	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b0cc80c-b8cd-4aa0-8a4f-6b83a4beb821	92382f9e-f3b4-426f-805a-cee1145787fa	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	92382f9e-f3b4-426f-805a-cee1145787fa	af9c8a49-54be-414c-b2d7-b6c1eebbfd86	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	273db938-5cc8-4b34-8eab-ca7c0228b69d	af9c8a49-54be-414c-b2d7-b6c1eebbfd86	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	af9c8a49-54be-414c-b2d7-b6c1eebbfd86	034af9f5-7609-4afe-b55a-22c567b3eeae	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b0cc80c-b8cd-4aa0-8a4f-6b83a4beb821	8c405318-6b27-45e9-a672-22db79ea406d	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	92382f9e-f3b4-426f-805a-cee1145787fa	034af9f5-7609-4afe-b55a-22c567b3eeae	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	92382f9e-f3b4-426f-805a-cee1145787fa	8c405318-6b27-45e9-a672-22db79ea406d	1	2025-11-24 07:34:14.219545+00
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.questions (id, graph_id, node_id, question_type, text, details, difficulty, created_by, created_at) FROM stdin;
4fbab897-5847-40ad-9c65-7bdc751cafd3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bed1e3d1-1c3e-4260-860b-6984b797eafb	multiple_choice	SAMPLE for 'Kinematics': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.406386+00
f70d0cb4-a576-441f-b0e7-64cfb4344eb6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bed1e3d1-1c3e-4260-860b-6984b797eafb	multiple_choice	SAMPLE for 'Kinematics': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.40884+00
fd274804-7073-4fda-88d2-9f34d2fec55e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bed1e3d1-1c3e-4260-860b-6984b797eafb	multiple_choice	SAMPLE for 'Kinematics': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.409829+00
6c544d46-8ee9-4fc4-87b7-bf0059d4d860	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bed1e3d1-1c3e-4260-860b-6984b797eafb	multiple_choice	SAMPLE for 'Kinematics': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.410557+00
46ec2c4c-c931-4fd8-887f-9ba6c2f1efb1	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bed1e3d1-1c3e-4260-860b-6984b797eafb	multiple_choice	SAMPLE for 'Kinematics': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.41124+00
1bed0180-2415-4b4d-b6d3-75ac8bbdd700	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ebdea86b-4b32-4edb-9b93-f13e64300bff	multiple_choice	SAMPLE for 'Scalar Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.411934+00
beb1ff7d-9c60-4d2d-a746-bc346614073c	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ebdea86b-4b32-4edb-9b93-f13e64300bff	multiple_choice	SAMPLE for 'Scalar Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.412636+00
8b6329bb-2cd3-4da0-9f8c-fd7df4dd68d2	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ebdea86b-4b32-4edb-9b93-f13e64300bff	multiple_choice	SAMPLE for 'Scalar Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.413265+00
7ccbb2e4-e846-494e-bc1d-6e3d128042a3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ebdea86b-4b32-4edb-9b93-f13e64300bff	multiple_choice	SAMPLE for 'Scalar Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.413897+00
650c399e-3359-4b72-9b8f-f8a78cfbf6c6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ebdea86b-4b32-4edb-9b93-f13e64300bff	multiple_choice	SAMPLE for 'Scalar Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.414531+00
337db634-d309-4817-9694-59857fb85733	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	multiple_choice	SAMPLE for 'Base Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.415166+00
dab67da0-6e73-4510-95f7-f2c0ec0ca625	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	multiple_choice	SAMPLE for 'Base Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.415799+00
1717eaf9-5221-4d9f-a5a2-5a49199bc51d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	multiple_choice	SAMPLE for 'Base Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.416453+00
935b962a-f1e4-4665-957f-91885cc42fd3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	multiple_choice	SAMPLE for 'Base Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.417116+00
71f250b9-f7c2-4d04-a9f1-6748dd1b9ee5	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	multiple_choice	SAMPLE for 'Base Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.417736+00
b05fbe65-74c7-437d-8da9-43289f83830e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	multiple_choice	SAMPLE for 'Derived Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.418379+00
7b366d60-2675-4363-b6e0-0544db601898	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	multiple_choice	SAMPLE for 'Derived Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.419028+00
2185d211-d92d-4dbd-8586-e654c3f1a779	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	multiple_choice	SAMPLE for 'Derived Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.41967+00
ee2fecc6-d22a-4514-a3b9-b6faf7afbe88	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	multiple_choice	SAMPLE for 'Derived Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.420321+00
f5be7725-81d7-411e-aed4-ec6b0fd55a4c	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	multiple_choice	SAMPLE for 'Derived Unit': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.420931+00
992ab8b6-0965-46d9-ab11-b6c516d8e0d6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	multiple_choice	SAMPLE for 'Average Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.421536+00
78971c9d-8d5d-4f26-9b5e-7e57f48b36f7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	multiple_choice	SAMPLE for 'Average Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.422401+00
1f2fe1e4-18f3-4d71-a5a8-bc199daa4f36	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	multiple_choice	SAMPLE for 'Average Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.423077+00
cab231d0-3b33-4a84-8c37-7291a7a59be6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	multiple_choice	SAMPLE for 'Average Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.423803+00
6311fda1-fa3f-41d5-9005-63ad92405aa2	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b341ac8a-5a51-44ea-acaa-d25047d77a5d	multiple_choice	SAMPLE for 'Average Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.424485+00
19ce3759-506f-4be6-ba02-cf52b821957d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	multiple_choice	SAMPLE for 'Instantaneous Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.425052+00
88fa7ff7-67f8-4787-9f3a-27b3897ce437	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	multiple_choice	SAMPLE for 'Instantaneous Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.425627+00
344c904d-f6d2-4deb-bdf9-51bb942f63e6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	multiple_choice	SAMPLE for 'Instantaneous Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.42621+00
d0721826-1d32-45ae-a000-2e6a243774d4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	multiple_choice	SAMPLE for 'Instantaneous Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.426782+00
0b1fc04e-539c-4109-877e-ac5169a6a394	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	multiple_choice	SAMPLE for 'Instantaneous Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.427437+00
e38284ec-aef7-4dc2-8c3c-c57b1bb72456	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6675f374-dd03-41c2-8796-7e81999cc075	multiple_choice	SAMPLE for 'Uniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.428043+00
c0b48249-e3f7-43a5-b75a-3df69dd90d4f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6675f374-dd03-41c2-8796-7e81999cc075	multiple_choice	SAMPLE for 'Uniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.428672+00
f7ceb30f-bc54-47b8-8a5f-a90532581aa7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6675f374-dd03-41c2-8796-7e81999cc075	multiple_choice	SAMPLE for 'Uniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.429339+00
d9d8fb7c-c095-4b1f-abaa-d9f06b2e848f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6675f374-dd03-41c2-8796-7e81999cc075	multiple_choice	SAMPLE for 'Uniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.429966+00
e46b6f76-e9f4-430d-b3e2-3d3ebe394ac4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6675f374-dd03-41c2-8796-7e81999cc075	multiple_choice	SAMPLE for 'Uniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.430709+00
e498abd0-b640-49ce-866c-2438bafcf497	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20994d2d-564a-48b6-b508-1bc4ca91ba20	multiple_choice	SAMPLE for 'Nonuniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.431383+00
b7610ed0-080a-4f48-81f0-e6a7be9989d4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20994d2d-564a-48b6-b508-1bc4ca91ba20	multiple_choice	SAMPLE for 'Nonuniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.432021+00
d648772c-9d9f-4edf-9e5a-f5da5d69fd16	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20994d2d-564a-48b6-b508-1bc4ca91ba20	multiple_choice	SAMPLE for 'Nonuniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.432676+00
15022964-1fa8-49d4-a8db-4ac0917bb20c	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20994d2d-564a-48b6-b508-1bc4ca91ba20	multiple_choice	SAMPLE for 'Nonuniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.433325+00
8c8772f5-6bbc-4336-90b8-f96e2dc89b48	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20994d2d-564a-48b6-b508-1bc4ca91ba20	multiple_choice	SAMPLE for 'Nonuniform Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.433963+00
8b0dd858-251a-4d00-8bae-963827a2d3fc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1a161ca5-68e2-4c97-8850-85f7c80aac24	multiple_choice	SAMPLE for 'Vector Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.434697+00
508df03f-f97e-4b33-bee7-211226be3509	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1a161ca5-68e2-4c97-8850-85f7c80aac24	multiple_choice	SAMPLE for 'Vector Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.435541+00
4817922e-b148-4a73-b07e-eb9e7dfad748	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1a161ca5-68e2-4c97-8850-85f7c80aac24	multiple_choice	SAMPLE for 'Vector Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.436234+00
d3fecfff-ffbe-4d2a-af77-e8ce3d449f15	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1a161ca5-68e2-4c97-8850-85f7c80aac24	multiple_choice	SAMPLE for 'Vector Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.436928+00
a72063ea-3a89-45d8-86be-967258a29d26	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1a161ca5-68e2-4c97-8850-85f7c80aac24	multiple_choice	SAMPLE for 'Vector Quantity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.437599+00
40a0e8e7-a050-42fe-a596-d51ce288b536	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dec0deaf-d9b0-4823-ac49-811fc893abde	multiple_choice	SAMPLE for 'Position ($\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.438252+00
3f0a3387-864b-4173-81c6-87a8ad910009	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dec0deaf-d9b0-4823-ac49-811fc893abde	multiple_choice	SAMPLE for 'Position ($\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.438907+00
fef77c17-70b1-477b-8c28-8c8ad9c03392	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dec0deaf-d9b0-4823-ac49-811fc893abde	multiple_choice	SAMPLE for 'Position ($\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.43958+00
5847c8cd-2d6d-4db3-8bc9-22af7807eb67	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dec0deaf-d9b0-4823-ac49-811fc893abde	multiple_choice	SAMPLE for 'Position ($\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.440238+00
b0a5cd0d-2b57-4f23-a3e5-848b71fce390	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dec0deaf-d9b0-4823-ac49-811fc893abde	multiple_choice	SAMPLE for 'Position ($\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.440859+00
7e235516-cd56-40ef-bcd4-f8ee0ebf0127	79f6869b-a9d1-4965-b864-dafd6a3faa6d	448fef63-5446-41a9-b188-83a57b2d586f	multiple_choice	SAMPLE for 'Displacement ($\\Delta\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.441502+00
853f6574-b166-45de-b100-9eb25d532da3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	448fef63-5446-41a9-b188-83a57b2d586f	multiple_choice	SAMPLE for 'Displacement ($\\Delta\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.442176+00
cab83bdb-beed-47e3-a998-9ee2f11f88ff	79f6869b-a9d1-4965-b864-dafd6a3faa6d	448fef63-5446-41a9-b188-83a57b2d586f	multiple_choice	SAMPLE for 'Displacement ($\\Delta\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.442831+00
0fced4ad-9d2f-4114-bea3-1fe01ff74e8b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	448fef63-5446-41a9-b188-83a57b2d586f	multiple_choice	SAMPLE for 'Displacement ($\\Delta\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.443557+00
44a094bf-b8fa-4043-888c-9cf79f1b2201	79f6869b-a9d1-4965-b864-dafd6a3faa6d	448fef63-5446-41a9-b188-83a57b2d586f	multiple_choice	SAMPLE for 'Displacement ($\\Delta\\vec{d}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.44421+00
dd6ca102-8fbc-473b-8e3d-a91cdbf7be67	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	multiple_choice	SAMPLE for 'Average Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.444913+00
7fd61270-773e-4ac7-a2d9-b97c2e3ee41f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	multiple_choice	SAMPLE for 'Average Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.445571+00
07891d94-b957-44b4-9ec1-d7cd9db00139	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	multiple_choice	SAMPLE for 'Average Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.446231+00
2bfae837-f763-48c8-b8f4-c767c085c764	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	multiple_choice	SAMPLE for 'Average Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.446879+00
af03f23a-d104-40de-9a72-5bd4d3d197c4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6cb12ce7-228f-40f4-87c4-185b110e32b7	multiple_choice	SAMPLE for 'Average Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.447593+00
d517817b-e548-4b9b-a3c3-db49b8817f49	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	multiple_choice	SAMPLE for 'Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.448234+00
8febb4e4-70cb-4b59-8e4c-30951fad590b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	multiple_choice	SAMPLE for 'Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.449108+00
8931e7b4-fdc5-4be5-9425-075c149f5509	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	multiple_choice	SAMPLE for 'Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.449755+00
e7857935-0a79-4976-b776-ceadac830368	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	multiple_choice	SAMPLE for 'Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.450816+00
374bb542-4190-46fe-8223-e6552b0f9323	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	multiple_choice	SAMPLE for 'Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.451554+00
fa44f67f-bb93-4e24-a694-eed01db44f36	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	multiple_choice	SAMPLE for 'Slope of Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.452191+00
ad261697-b52d-4cb5-9036-bac651570ba6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	multiple_choice	SAMPLE for 'Slope of Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.452828+00
ed150cae-9306-46eb-bff5-7243ec00b30e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	multiple_choice	SAMPLE for 'Slope of Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.453478+00
3e902e49-09e8-4cfc-b477-4bb8264414d3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	multiple_choice	SAMPLE for 'Slope of Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.454111+00
f8edc315-66b6-4943-a796-fd72a1f6b4de	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	multiple_choice	SAMPLE for 'Slope of Position-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.454747+00
d83562ff-d834-4dcf-b5f0-e18e039adcf9	79f6869b-a9d1-4965-b864-dafd6a3faa6d	182ddcaa-29bf-4484-8c6c-b18496d59832	multiple_choice	SAMPLE for 'Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.455415+00
a3711062-4604-47bc-b3ca-ceb1c6df5bb1	79f6869b-a9d1-4965-b864-dafd6a3faa6d	182ddcaa-29bf-4484-8c6c-b18496d59832	multiple_choice	SAMPLE for 'Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.456045+00
2c43f230-6b8c-4117-b518-14ad3af15bc4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	182ddcaa-29bf-4484-8c6c-b18496d59832	multiple_choice	SAMPLE for 'Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.456655+00
c3835a9c-c60c-4412-a9b4-3a5cd98f0f37	79f6869b-a9d1-4965-b864-dafd6a3faa6d	182ddcaa-29bf-4484-8c6c-b18496d59832	multiple_choice	SAMPLE for 'Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.457286+00
be682963-b88c-495a-a2c8-dcbb52711a41	79f6869b-a9d1-4965-b864-dafd6a3faa6d	182ddcaa-29bf-4484-8c6c-b18496d59832	multiple_choice	SAMPLE for 'Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.457919+00
0e28045d-9b56-4c05-adcb-a2d119826b31	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	multiple_choice	SAMPLE for 'Area under Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.45848+00
b9848760-7ef7-4338-9ab0-5cf90de3595e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	multiple_choice	SAMPLE for 'Area under Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.459079+00
eaf6a8a7-5772-4716-8255-136169cc76bf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	multiple_choice	SAMPLE for 'Area under Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.459717+00
e6cdf476-d40f-41c8-bb53-b173080a52bc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	multiple_choice	SAMPLE for 'Area under Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.460331+00
2603dee8-6fb4-4d03-9b85-a07270801e30	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5649bae7-fb7f-436c-a34e-5c085a6a014d	multiple_choice	SAMPLE for 'Area under Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.460985+00
d4d1ecd5-473c-4070-9733-01d6104a7e61	79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	multiple_choice	SAMPLE for 'Communicating Directions': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.461656+00
395debdd-a9d1-4dd6-b4e0-6c4244807dda	79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	multiple_choice	SAMPLE for 'Communicating Directions': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.462484+00
4660858e-07d7-4a56-8e07-8a7cb4f05d30	79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	multiple_choice	SAMPLE for 'Communicating Directions': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.463159+00
64ef064d-9754-4606-b62f-473ddaa55cf3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	multiple_choice	SAMPLE for 'Communicating Directions': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.463824+00
ed1641d3-0d9d-4bc6-b6ab-a243e374d9b2	79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	multiple_choice	SAMPLE for 'Communicating Directions': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.464434+00
5c7556ac-b6e8-4451-9221-3458eac17366	79f6869b-a9d1-4965-b864-dafd6a3faa6d	273ec2d4-2aa9-47a5-accc-02f852edf5e4	multiple_choice	SAMPLE for 'Resultant Displacement ($\\Delta\\vec{d}_{R}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.465062+00
5d37042e-497e-4377-976b-51373994a316	79f6869b-a9d1-4965-b864-dafd6a3faa6d	273ec2d4-2aa9-47a5-accc-02f852edf5e4	multiple_choice	SAMPLE for 'Resultant Displacement ($\\Delta\\vec{d}_{R}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.465685+00
c2745b12-17c0-435e-bd17-01f4357007da	79f6869b-a9d1-4965-b864-dafd6a3faa6d	273ec2d4-2aa9-47a5-accc-02f852edf5e4	multiple_choice	SAMPLE for 'Resultant Displacement ($\\Delta\\vec{d}_{R}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.466331+00
1cb67c05-43ab-428a-af58-2b12ff7cc837	79f6869b-a9d1-4965-b864-dafd6a3faa6d	273ec2d4-2aa9-47a5-accc-02f852edf5e4	multiple_choice	SAMPLE for 'Resultant Displacement ($\\Delta\\vec{d}_{R}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.467026+00
b3a8edb8-513b-4d9d-9ca2-fb8bc54d58e6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	273ec2d4-2aa9-47a5-accc-02f852edf5e4	multiple_choice	SAMPLE for 'Resultant Displacement ($\\Delta\\vec{d}_{R}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.467688+00
e42054c1-6277-4117-bac9-3f468c32e256	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	multiple_choice	SAMPLE for 'Vector Addition (Graphical)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.468361+00
91bb2f49-5317-4109-b5cc-4c954b15466a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	multiple_choice	SAMPLE for 'Vector Addition (Graphical)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.469032+00
1283b811-3d7d-49ec-bd9d-f79167b05034	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	multiple_choice	SAMPLE for 'Vector Addition (Graphical)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.469715+00
11193a60-190e-4007-a11b-8a0de7d02b8b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	multiple_choice	SAMPLE for 'Vector Addition (Graphical)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.470381+00
fdaa1be0-270c-45cd-80a8-8cbb11831ba8	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	multiple_choice	SAMPLE for 'Vector Addition (Graphical)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.471031+00
96ff3096-7b9c-4256-90d8-f0ceaba025c6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	multiple_choice	SAMPLE for 'Vector Addition (Algebraic)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.471679+00
393db177-ded8-49a5-9658-10835266dfda	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	multiple_choice	SAMPLE for 'Vector Addition (Algebraic)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.472324+00
e7e7c705-371c-4616-8e9c-8c4e15f8f9f7	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	multiple_choice	SAMPLE for 'Vector Addition (Algebraic)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.473007+00
01613bd0-0d6a-435a-9aea-46b71a610c9b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	multiple_choice	SAMPLE for 'Vector Addition (Algebraic)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.473642+00
f19019f1-a5ca-4669-92a5-98e1e6473dfb	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	multiple_choice	SAMPLE for 'Vector Addition (Algebraic)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.474266+00
6f8d94e2-f80f-47f9-b73b-950e66b45930	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	multiple_choice	SAMPLE for 'Average Velocity (2D)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.474878+00
4c4833a3-8f00-4620-be2d-1c98e02d15dc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	multiple_choice	SAMPLE for 'Average Velocity (2D)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.475701+00
23d9a90c-1177-4151-8222-4a662f3136a8	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	multiple_choice	SAMPLE for 'Average Velocity (2D)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.476386+00
26404599-5148-49f4-874f-9508b3802f79	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	multiple_choice	SAMPLE for 'Average Velocity (2D)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.477038+00
15d7ddee-4688-49e1-a8cf-2321f02b6fe9	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	multiple_choice	SAMPLE for 'Average Velocity (2D)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.477734+00
cdfa95d1-5862-47e2-a11c-1b22a660a5e6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	multiple_choice	SAMPLE for 'Frame of Reference': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.47838+00
b1bb97df-3867-4881-8a65-0f902ed09350	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	multiple_choice	SAMPLE for 'Frame of Reference': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.479026+00
97f2a899-5486-4a6d-86c4-9069b7e24971	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	multiple_choice	SAMPLE for 'Frame of Reference': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.47964+00
26302288-5a67-4928-8e0a-d0492a696c3d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	multiple_choice	SAMPLE for 'Frame of Reference': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.480221+00
7d99bac1-1f7a-400b-9ee8-d41249b57285	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	multiple_choice	SAMPLE for 'Frame of Reference': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.480795+00
a73a0267-1a14-4afa-8dca-7285d529ed61	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	multiple_choice	SAMPLE for 'Relative Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.48145+00
ddf7f29e-21e3-41e2-a14b-e8c571290576	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	multiple_choice	SAMPLE for 'Relative Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.482096+00
f248db01-9485-4776-a60d-b9a22e9c44d6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	multiple_choice	SAMPLE for 'Relative Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.482671+00
33a7fcba-76e9-471a-9704-4a60b2b7315f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	multiple_choice	SAMPLE for 'Relative Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.483356+00
5012b484-74a6-4c97-9c22-3a66abf87e49	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	multiple_choice	SAMPLE for 'Relative Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.48397+00
041a2432-821a-4477-97e1-265b356158c4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	multiple_choice	SAMPLE for 'Accelerated Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.484564+00
c858fea5-8d96-461f-a887-4a03fe5d2c6d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	multiple_choice	SAMPLE for 'Accelerated Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.485183+00
7414d456-93ff-4e2a-a697-edf32a52ad09	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	multiple_choice	SAMPLE for 'Accelerated Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.485823+00
1d4a2139-8dae-426a-a21b-8a934b84f65a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	multiple_choice	SAMPLE for 'Accelerated Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.48644+00
9505c742-afc8-433c-a2b8-228219ccac58	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	multiple_choice	SAMPLE for 'Accelerated Motion': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.487117+00
7e727f08-740b-46d2-918d-7eda8030fd0a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	multiple_choice	SAMPLE for 'Uniform Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.487737+00
614aea07-3bae-4564-aa70-3a015502e814	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	multiple_choice	SAMPLE for 'Uniform Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.488526+00
10b4564c-568b-4871-9b5b-eef19a78eaa3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	multiple_choice	SAMPLE for 'Uniform Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.489169+00
55fbf942-f61a-40df-b0cb-e43799f41553	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	multiple_choice	SAMPLE for 'Uniform Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.489843+00
db12034b-8eec-4c32-b6e6-53e431cbe2dc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	multiple_choice	SAMPLE for 'Uniform Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.490455+00
fd578f5e-f7ec-487b-a0e7-b58439258861	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bff0139a-f332-433b-b234-d722e796e2a6	multiple_choice	SAMPLE for 'Average Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.491088+00
7669e8bd-987a-43ac-ba0e-9b537e284334	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bff0139a-f332-433b-b234-d722e796e2a6	multiple_choice	SAMPLE for 'Average Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.49171+00
3abaa4ad-1568-4d5d-b495-51acbcf79960	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bff0139a-f332-433b-b234-d722e796e2a6	multiple_choice	SAMPLE for 'Average Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.49235+00
d203f8b5-0276-4545-984a-92c945b10e4a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bff0139a-f332-433b-b234-d722e796e2a6	multiple_choice	SAMPLE for 'Average Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.492985+00
0870db80-9448-464f-a915-f43a415d4341	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bff0139a-f332-433b-b234-d722e796e2a6	multiple_choice	SAMPLE for 'Average Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.493592+00
58d1d75a-9533-4607-9cfc-4aea50ce6819	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	multiple_choice	SAMPLE for 'Instantaneous Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.494237+00
21bb86b0-05a7-4c5e-a670-583d1bc8fd69	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	multiple_choice	SAMPLE for 'Instantaneous Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.494947+00
1b2567ee-c67e-442e-866a-90d6b1ff2353	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	multiple_choice	SAMPLE for 'Instantaneous Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.495707+00
a2083983-404f-4ad4-9a0b-c6332a79108a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	multiple_choice	SAMPLE for 'Instantaneous Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.496327+00
f24b2455-e31d-4b3b-93e1-6656f7df4281	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	multiple_choice	SAMPLE for 'Instantaneous Acceleration': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.496978+00
6c7aa66d-f1c8-4a24-ba94-b4724c3b1247	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	multiple_choice	SAMPLE for 'Slope of Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.497662+00
1e48076e-f9bc-4378-9ae7-f224f5d7aad5	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	multiple_choice	SAMPLE for 'Slope of Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.498344+00
3a3a5de1-92db-4ea1-8e6a-31e99105a2e6	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	multiple_choice	SAMPLE for 'Slope of Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.499007+00
a8f8fb69-5e5b-4605-b79f-595d83929acc	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	multiple_choice	SAMPLE for 'Slope of Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.499684+00
b6283972-dfa5-47dc-bb36-65262c8ef790	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	multiple_choice	SAMPLE for 'Slope of Velocity-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.500331+00
3b25a71d-507d-4045-be82-f0240c79c8e5	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	multiple_choice	SAMPLE for 'Position-Time Graph (Acceleration)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.501049+00
9c736beb-4de3-4d6e-8239-e1f72df90e52	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	multiple_choice	SAMPLE for 'Position-Time Graph (Acceleration)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.501737+00
c7a15377-db5c-4bc1-861c-8cb8fbe80e4d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	multiple_choice	SAMPLE for 'Position-Time Graph (Acceleration)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.502444+00
ecf4516c-4436-4a24-8590-1bd14e20efda	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	multiple_choice	SAMPLE for 'Position-Time Graph (Acceleration)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.503102+00
d5cfbeaf-51da-4ef5-976f-8205c1636ece	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	multiple_choice	SAMPLE for 'Position-Time Graph (Acceleration)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.50372+00
79460e05-b819-4db1-b60a-4e0a16d8b92a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	multiple_choice	SAMPLE for 'Tangent Technique': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.504374+00
e97d69f5-c24a-433e-993e-0373e1e37774	79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	multiple_choice	SAMPLE for 'Tangent Technique': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.505037+00
9457e9bd-633a-4729-8182-c143dabcf2f0	79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	multiple_choice	SAMPLE for 'Tangent Technique': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.505676+00
301e3c17-a926-4527-b590-e54efef2726e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	multiple_choice	SAMPLE for 'Tangent Technique': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.506306+00
d1147d90-31ba-4cd6-953f-6777cbe95125	79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	multiple_choice	SAMPLE for 'Tangent Technique': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.506923+00
f2d093c7-a9a4-4f33-a50d-b7227f04301f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	multiple_choice	SAMPLE for 'Instantaneous Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.507568+00
07ed798c-b374-4859-956f-e950895b6b93	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	multiple_choice	SAMPLE for 'Instantaneous Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.508203+00
040ab787-e31a-4f06-9e0e-408fd5f2b1a1	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	multiple_choice	SAMPLE for 'Instantaneous Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.508843+00
ea4bb261-92ed-4484-abd6-4fe0c6768e8e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	multiple_choice	SAMPLE for 'Instantaneous Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.50945+00
79c3f658-9be3-4494-b6ec-1d993515f373	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	multiple_choice	SAMPLE for 'Instantaneous Velocity': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.510065+00
88612425-c0f4-40d4-b849-2dcaad7e8f01	79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	multiple_choice	SAMPLE for 'Area under Acceleration-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.510685+00
7bd9206a-b6af-49d6-b7d7-c46bd3679492	79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	multiple_choice	SAMPLE for 'Area under Acceleration-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.51134+00
600e82cf-d974-4c65-b0cc-533ae2cfd9f4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	multiple_choice	SAMPLE for 'Area under Acceleration-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.511945+00
51db8d0f-ff9a-4aff-bc3c-23db77be4751	79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	multiple_choice	SAMPLE for 'Area under Acceleration-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.512549+00
fcbf38ef-1bc0-4cbc-9b13-df1ded2388ba	79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	multiple_choice	SAMPLE for 'Area under Acceleration-Time Graph': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.513166+00
bd84b8ef-9f3c-4292-8886-6657946d1d6c	79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	multiple_choice	SAMPLE for 'Acceleration Due to Gravity ($\\vec{g}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.513774+00
6b0f47ad-7347-42ba-b60f-2c1b7b5a273e	79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	multiple_choice	SAMPLE for 'Acceleration Due to Gravity ($\\vec{g}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.51452+00
380cf4a5-0893-4212-b244-6f2224000184	79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	multiple_choice	SAMPLE for 'Acceleration Due to Gravity ($\\vec{g}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.515178+00
2c02d4b6-4e1d-4244-bc4f-f36ad7e12900	79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	multiple_choice	SAMPLE for 'Acceleration Due to Gravity ($\\vec{g}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.515842+00
6b7ce061-7a02-46e9-a5b0-75013efeea42	79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	multiple_choice	SAMPLE for 'Acceleration Due to Gravity ($\\vec{g}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.51649+00
3e9c5be4-54b1-4a1c-8343-f7f0d9fb40da	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	multiple_choice	SAMPLE for 'Free Fall': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.517142+00
770d81b2-fb3f-4a2f-9b24-3e8c672b2de5	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	multiple_choice	SAMPLE for 'Free Fall': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.517768+00
460165da-2e2f-4d67-8485-41171314c5cb	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	multiple_choice	SAMPLE for 'Free Fall': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.518425+00
ee6cb3bd-56d8-424e-8a23-9a9fbd30edca	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	multiple_choice	SAMPLE for 'Free Fall': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.51906+00
e83b775f-e3ea-430a-ad43-38f0cab695aa	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	multiple_choice	SAMPLE for 'Free Fall': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.519677+00
bb080873-b3f3-4478-96c0-989e25182203	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	multiple_choice	SAMPLE for 'Terminal Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.520306+00
9359ca14-6a1a-48e1-b5c0-18fb6fb5bc32	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	multiple_choice	SAMPLE for 'Terminal Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.520934+00
b12899cb-e9ca-40cd-b2dd-c968f06799b0	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	multiple_choice	SAMPLE for 'Terminal Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.521554+00
417a069f-8b4f-4fab-ab97-bb0bce08a2f2	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	multiple_choice	SAMPLE for 'Terminal Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.522165+00
b354c5ee-3426-4abe-be69-6753b90ae6c9	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	multiple_choice	SAMPLE for 'Terminal Speed': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.522816+00
a2a1d1f8-ccbc-4266-ae5e-0a018a9a2cfd	79f6869b-a9d1-4965-b864-dafd6a3faa6d	8a4f2710-f341-4455-9680-9665e0a584d6	multiple_choice	SAMPLE for 'Kinematic Equation (Definition of $\\vec{a}_{av}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.523605+00
525ef7d6-77c1-459e-a1f9-aa03f830f2a4	79f6869b-a9d1-4965-b864-dafd6a3faa6d	8a4f2710-f341-4455-9680-9665e0a584d6	multiple_choice	SAMPLE for 'Kinematic Equation (Definition of $\\vec{a}_{av}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.524262+00
0604f1c2-c338-4d67-b926-06265e147a3a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	8a4f2710-f341-4455-9680-9665e0a584d6	multiple_choice	SAMPLE for 'Kinematic Equation (Definition of $\\vec{a}_{av}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.524936+00
148fe439-d55f-445e-baf1-18cfa6c7a81b	79f6869b-a9d1-4965-b864-dafd6a3faa6d	8a4f2710-f341-4455-9680-9665e0a584d6	multiple_choice	SAMPLE for 'Kinematic Equation (Definition of $\\vec{a}_{av}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.525591+00
c08a7781-1c7e-4204-8b1c-547d588bd78f	79f6869b-a9d1-4965-b864-dafd6a3faa6d	8a4f2710-f341-4455-9680-9665e0a584d6	multiple_choice	SAMPLE for 'Kinematic Equation (Definition of $\\vec{a}_{av}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.526229+00
7410ce87-0b7e-4d75-bf1b-b316b3c50f1a	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d5972321-2d2b-433e-b43b-760522bfd99b	multiple_choice	SAMPLE for 'Kinematic Equation (Displacement from Avg Velocity)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.526901+00
75694135-ee51-4452-86ce-d4cdc61a4002	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d5972321-2d2b-433e-b43b-760522bfd99b	multiple_choice	SAMPLE for 'Kinematic Equation (Displacement from Avg Velocity)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.527585+00
b782a97d-d9f9-44c8-9cc1-82f444e7ecd8	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d5972321-2d2b-433e-b43b-760522bfd99b	multiple_choice	SAMPLE for 'Kinematic Equation (Displacement from Avg Velocity)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.528526+00
5ca9227d-889d-44a7-9544-c70d9d669228	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d5972321-2d2b-433e-b43b-760522bfd99b	multiple_choice	SAMPLE for 'Kinematic Equation (Displacement from Avg Velocity)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.529163+00
fefb58f5-eae0-47ce-8d0a-a6086a344f85	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d5972321-2d2b-433e-b43b-760522bfd99b	multiple_choice	SAMPLE for 'Kinematic Equation (Displacement from Avg Velocity)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.529754+00
254cf439-699f-4d8d-8b62-b16b1fd10303	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\vec{v}_{f}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.530319+00
ad1d8ec3-de07-4fb5-8522-e2db63979eb9	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\vec{v}_{f}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.530924+00
c641db1b-4ca4-41e6-bea1-5065ae63e715	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\vec{v}_{f}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.531587+00
1b256a9b-cdda-4e2f-a64b-78bc64c07b72	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\vec{v}_{f}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.532258+00
1ed527a7-c97c-43cf-9591-b1e5d4c30990	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\vec{v}_{f}$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.532904+00
28bcc429-38ee-4182-b69d-f13fcc83d2f3	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\Delta t$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.533509+00
de663560-6d91-4d12-a6b5-727d4a9d4eb2	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\Delta t$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.534127+00
804dd9d0-1e05-4396-925e-7b99d9c34a3d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\Delta t$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.534783+00
2b90cf69-a29c-4663-b57b-54e3bb0aec93	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\Delta t$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.535443+00
badb3255-6f2e-4c31-9132-ea5dfbfee03d	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	multiple_choice	SAMPLE for 'Kinematic Equation (no $\\Delta t$)': [Your question text here]	{"p_g": 0.25, "p_s": 0.1, "options": ["Option A", "Option B", "Option C", "Option D"], "question_type": "multiple_choice", "correct_answer": 0}	medium	\N	2025-11-13 20:06:22.536089+00
f2fedefe-bb63-4e75-8288-4dd2c6fedc1c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d036c0ed-76bc-46be-ae71-20047a940cd0	multiple_choice	Which term describes how close a measurement is to the true value?	{"p_g": 0.25, "p_s": 0.1, "options": ["Accuracy", "Precision", "Reliability", "Consistency"], "explanation": "Accuracy refers to how close a measured value is to the actual or true value.", "correct_answer": 0}	easy	\N	2025-11-24 08:05:21.29788+00
5adbf4f2-84f5-4d5b-9cd8-1aecfc1e544a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d036c0ed-76bc-46be-ae71-20047a940cd0	multiple_choice	A dart player consistently hits the same spot on the dartboard, but it's always far from the bullseye. What best describes this player's throws?	{"p_g": 0.25, "p_s": 0.1, "options": ["High precision, low accuracy", "Low precision, high accuracy", "High precision, high accuracy", "Low precision, low accuracy"], "explanation": "Hitting the same spot repeatedly indicates high precision. However, being far from the bullseye (the true target) indicates low accuracy.", "correct_answer": 0}	medium	\N	2025-11-24 08:05:21.29788+00
0fc62a33-666a-4262-b3a7-4cd4f9e93229	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d036c0ed-76bc-46be-ae71-20047a940cd0	multiple_choice	A scientist uses a faulty balance that consistently adds 0.5 grams to every measurement. If the scientist performs multiple measurements on the same 10.0-gram sample and gets readings of 10.51 g, 10.49 g, and 10.50 g, how would you describe these measurements?	{"p_g": 0.25, "p_s": 0.1, "options": ["Precise but not accurate", "Accurate but not precise", "Both accurate and precise", "Neither accurate nor precise"], "explanation": "The measurements are very close to each other (10.51, 10.49, 10.50), indicating high precision. However, they are consistently off by 0.5 g from the true value of 10.0 g, meaning they are not accurate. This is an example of a systematic error affecting accuracy while precision remains high.", "correct_answer": 0}	hard	\N	2025-11-24 08:05:21.29788+00
a459bfa1-33cb-40ce-8423-059050d4ecde	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8a9f80cc-f2c5-475b-bdd8-a42e94089093	multiple_choice	Which group on the periodic table do alkali metals belong to?	{"p_g": 0.25, "p_s": 0.1, "options": ["Group 1", "Group 2", "Group 17", "Group 18"], "explanation": "Alkali metals are found in Group 1 of the periodic table, excluding hydrogen.", "correct_answer": 0}	easy	\N	2025-11-24 08:05:21.29788+00
d0fa50a4-e4ed-46d3-bbad-5313b82ff47f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8a9f80cc-f2c5-475b-bdd8-a42e94089093	multiple_choice	Why are alkali metals considered highly reactive?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have one valence electron that is easily lost.", "They have a full outer electron shell.", "They are gases at room temperature.", "They have very high ionization energies."], "explanation": "Alkali metals have only one valence electron, which they readily lose to achieve a stable electron configuration, making them highly reactive.", "correct_answer": 0}	medium	\N	2025-11-24 08:05:21.29788+00
0c8abd3f-ec3e-403b-b726-f8aa7dc34e5e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8a9f80cc-f2c5-475b-bdd8-a42e94089093	multiple_choice	Which of the following statements is TRUE regarding the reactivity of alkali metals down the group?	{"p_g": 0.25, "p_s": 0.1, "options": ["Reactivity increases as you go down the group.", "Reactivity decreases as you go down the group.", "Reactivity remains constant down the group.", "Reactivity is unpredictable down the group."], "explanation": "As you go down Group 1, the atomic radius increases, meaning the outermost electron is further from the nucleus and experiences less attraction. This makes it easier to lose the electron, thus increasing reactivity.", "correct_answer": 0}	hard	\N	2025-11-24 08:05:21.29788+00
58fc2e26-31d8-4fc9-b49f-30ee652e7be2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7ed53540-38ec-42bb-82af-ef61c751c004	multiple_choice	Alkaline earth metals are found in which group of the periodic table?	{"p_g": 0.25, "p_s": 0.1, "options": ["Group 1", "Group 2", "Group 17", "Group 18"], "explanation": "The node description explicitly states that alkaline earth metals are elements in Group 2 of the periodic table.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
bcd64b54-2326-460b-ad9d-7e1526ca11a7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7ed53540-38ec-42bb-82af-ef61c751c004	multiple_choice	What is a characteristic property of alkaline earth metals regarding their valence electrons?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have one valence electron.", "They have two valence electrons.", "They have seven valence electrons.", "They have a full outer shell of eight valence electrons."], "explanation": "Alkaline earth metals are defined by having two valence electrons, which they tend to lose to form +2 ions.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
de0205f1-245d-44dc-8d80-b9ecc50084d5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7ed53540-38ec-42bb-82af-ef61c751c004	multiple_choice	Compared to alkali metals, why are alkaline earth metals generally less reactive?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have a smaller atomic radius, making it harder to lose electrons.", "They have two valence electrons to lose, which requires more energy than losing one.", "They have a full d-subshell, making them less willing to react.", "They are non-metals, unlike alkali metals."], "explanation": "Alkaline earth metals have two valence electrons to lose, whereas alkali metals only need to lose one. Losing two electrons requires more energy (higher ionization energy) than losing just one, making alkali metals more reactive. Both are reactive, but the energy cost for the second electron makes alkaline earth metals slightly less so.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
07b84af6-777c-469a-b2a9-ae8d6dfabfec	c18d6d95-77ed-4b41-a833-dc5cddec74f4	967128a0-6975-492f-a394-e456f3d2927f	multiple_choice	What is an anion?	{"p_g": 0.25, "p_s": 0.1, "options": ["A positively charged ion", "A negatively charged ion", "A neutral atom", "A molecule composed of two or more atoms"], "explanation": "An anion is defined as an ion with a negative charge.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
82291ffa-6b92-4169-89bd-d05f39bce3ca	c18d6d95-77ed-4b41-a833-dc5cddec74f4	967128a0-6975-492f-a394-e456f3d2927f	multiple_choice	How does an atom become an anion?	{"p_g": 0.25, "p_s": 0.1, "options": ["By losing protons", "By gaining electrons", "By losing electrons", "By gaining neutrons"], "explanation": "An atom becomes negatively charged (an anion) when it gains one or more electrons.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
22cb47c8-5c64-4ab4-8cbd-f9b2a05d9295	c18d6d95-77ed-4b41-a833-dc5cddec74f4	967128a0-6975-492f-a394-e456f3d2927f	multiple_choice	Which of the following elements is most likely to form an anion?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sodium (Na)", "Magnesium (Mg)", "Chlorine (Cl)", "Helium (He)"], "explanation": "Non-metals, especially halogens like Chlorine (Cl), have a high electron affinity and tend to gain electrons to achieve a stable octet, thus forming anions.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
b102f2b5-04ec-412f-9d9c-fe06a5c6d46e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	multiple_choice	What is the smallest particle of an element that still retains the identity and properties of that element?	{"p_g": 0.25, "p_s": 0.1, "options": ["Molecule", "Atom", "Proton", "Electron"], "explanation": "By definition, an atom is the smallest unit of an element that maintains its unique characteristics.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
488abac1-467a-4cf0-b1b8-236dae8c1a6e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	multiple_choice	Which part of an atom determines its elemental identity?	{"p_g": 0.25, "p_s": 0.1, "options": ["Number of electrons", "Number of neutrons", "Number of protons", "Overall mass"], "explanation": "The number of protons in an atom's nucleus defines its atomic number, which in turn determines what element it is.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
faee377b-4d24-4e3f-94b4-3de842277ce2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d4c90a21-9433-4ed3-96e4-2e0ea0fb5e6c	multiple_choice	If an atom has 6 protons, 6 neutrons, and 5 electrons, what is its net charge?	{"p_g": 0.25, "p_s": 0.1, "options": ["Neutral", "-1", "+1", "+2"], "explanation": "Each proton has a +1 charge, and each electron has a -1 charge. With 6 protons (+6) and 5 electrons (-5), the net charge is +6 - 5 = +1.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
83f524b0-ba21-4b4d-925c-9edf363bdbc1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c1dde2a3-4c52-4d2e-8fd6-11e0329d40ba	multiple_choice	What is the primary purpose of the Atomic Mass Unit (amu)?	{"p_g": 0.25, "p_s": 0.1, "options": ["Measuring the speed of atoms", "Expressing atomic and molecular weights", "Calculating the energy of electrons", "Determining the volume of atoms"], "explanation": "The Atomic Mass Unit (amu) is specifically designed to express the very small masses of atoms and molecules in a convenient way.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
65035bd8-dd12-4902-9150-c20be5b7419a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c1dde2a3-4c52-4d2e-8fd6-11e0329d40ba	multiple_choice	The Atomic Mass Unit (amu) is defined as one-twelfth the mass of which specific atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["Hydrogen-1", "Oxygen-16", "Carbon-12", "Uranium-238"], "explanation": "The definition explicitly states that 1 amu is one-twelfth the mass of a single carbon-12 atom, making it the international standard.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
c07690e8-a782-429f-b6d3-cf1938c27f9c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c1dde2a3-4c52-4d2e-8fd6-11e0329d40ba	multiple_choice	Why was carbon-12 specifically chosen as the standard for defining the Atomic Mass Unit, rather than hydrogen-1 or oxygen-16?	{"p_g": 0.25, "p_s": 0.1, "options": ["Carbon-12 is the most abundant element in the universe.", "Carbon-12 has exactly 12 protons, making calculations simpler.", "It provides a stable and precise reference point that allows for accurate mass spectrometry measurements and avoids issues with isotopes of other elements.", "It was an arbitrary choice made by early chemists without scientific reasoning."], "explanation": "Carbon-12 provides a highly stable and precise reference point for mass spectrometry, and its isotopic purity and abundance make it ideal for defining a consistent unit of atomic mass, avoiding complications with other elements' isotopes.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
16d0dfad-2391-418c-b9cd-2ea3abe7af20	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4e3fd033-be91-4441-a8e3-effccde6c247	multiple_choice	What two subatomic particles are found in the atomic nucleus?	{"p_g": 0.25, "p_s": 0.1, "options": ["Protons and electrons", "Neutrons and electrons", "Protons and neutrons", "Electrons and positrons"], "explanation": "The atomic nucleus is defined as the central core of an atom, composed of protons and neutrons.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
ff31410f-52dc-47f3-a660-abb2599a0e4b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4e3fd033-be91-4441-a8e3-effccde6c247	multiple_choice	Which statement accurately describes the mass distribution within an atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["Electrons account for most of the atom's mass.", "The mass is evenly distributed throughout the atom.", "The atomic nucleus contains most of the atom's mass.", "The atom's mass is primarily located in its electron cloud."], "explanation": "The nucleus, though very small, contains protons and neutrons, which are significantly more massive than electrons. Therefore, most of the atom's mass is concentrated in the nucleus.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
b5a3e8c4-482c-4f33-871b-c56861e8df68	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4e3fd033-be91-4441-a8e3-effccde6c247	multiple_choice	If an atom loses a neutron from its nucleus, what changes about the atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["It becomes a different element.", "Its atomic number changes.", "It becomes an ion.", "It becomes an isotope of the original element."], "explanation": "Losing a neutron changes the mass number (protons + neutrons) but not the atomic number (number of protons). This results in an isotope of the original element, as the element identity is determined by the number of protons. The charge remains unchanged if only a neutron is lost.", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
f3ac6a71-1331-4ac6-99e5-ea3bfc971a5a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e2e7a557-986e-4545-8037-886ab96fc6c7	multiple_choice	What does the atomic number (Z) of an element represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["The number of protons", "The number of neutrons", "The number of electrons", "The total number of protons and neutrons"], "explanation": "The atomic number is defined as the number of protons in the nucleus of an atom, which uniquely identifies an element.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
550838ba-bb78-4956-897d-c1eef895b75a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e2e7a557-986e-4545-8037-886ab96fc6c7	multiple_choice	An atom with an atomic number of 8 belongs to which element?	{"p_g": 0.25, "p_s": 0.1, "options": ["Nitrogen", "Oxygen", "Fluorine", "Carbon"], "explanation": "The atomic number 8 uniquely identifies the element Oxygen on the periodic table.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
804a45a2-e690-43ea-a23c-c12389d5b417	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e2e7a557-986e-4545-8037-886ab96fc6c7	multiple_choice	An ion has 11 protons, 12 neutrons, and 10 electrons. What is its atomic number?	{"p_g": 0.25, "p_s": 0.1, "options": ["10", "11", "12", "23"], "explanation": "The atomic number is solely determined by the number of protons. The number of neutrons and electrons (especially in an ion) does not affect the atomic number.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
6c5a52cd-e8ae-40d9-938e-c9cffd047213	c18d6d95-77ed-4b41-a833-dc5cddec74f4	023c64de-a174-4a74-874a-79c9333812a8	multiple_choice	What does 'atomic radius' primarily measure?	{"p_g": 0.25, "p_s": 0.1, "options": ["The number of protons in an atom", "The size of an atom", "The mass of an atom's nucleus", "The energy level of an electron"], "explanation": "Atomic radius is defined as the distance from the nucleus to the outermost electron shell, which gives a measure of the atom's size.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
4ce69a44-ab8e-49f8-ae05-efb182d77dbe	c18d6d95-77ed-4b41-a833-dc5cddec74f4	023c64de-a174-4a74-874a-79c9333812a8	multiple_choice	As you move from left to right across a period in the periodic table, what generally happens to the atomic radius?	{"p_g": 0.25, "p_s": 0.1, "options": ["It increases", "It decreases", "It remains constant", "It first increases then decreases"], "explanation": "Across a period, the nuclear charge increases, pulling the electrons closer to the nucleus, thus decreasing the atomic radius.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
bd3a9408-6cb2-4e1b-8aaa-6434279a78e3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	023c64de-a174-4a74-874a-79c9333812a8	multiple_choice	Why does atomic radius generally decrease across a period in the periodic table, even though the number of electrons increases?	{"p_g": 0.25, "p_s": 0.1, "options": ["The shielding effect from inner electrons increases significantly.", "The number of electron shells decreases.", "The increased nuclear charge pulls the electrons closer to the nucleus.", "Electrons are removed from the atom as you move across a period."], "explanation": "Across a period, the number of protons (nuclear charge) increases, which exerts a stronger pull on the valence electrons, drawing them closer to the nucleus and reducing the overall atomic size. The added electrons are in the same principal energy level, so shielding is not significantly increased.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
35111fc4-58a0-4953-9446-06e7c4d787d1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	273db938-5cc8-4b34-8eab-ca7c0228b69d	multiple_choice	Where is the average atomic mass of an element typically found?	{"p_g": 0.25, "p_s": 0.1, "options": ["On the periodic table", "In the nucleus of an atom", "Only in specialized mass spectrometry reports", "It's a theoretical value not found anywhere"], "explanation": "The average atomic mass, which is a weighted average of an element's isotopes, is the mass value displayed for each element on the periodic table.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
8798a55f-f98e-4804-8a93-90b61835934b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	273db938-5cc8-4b34-8eab-ca7c0228b69d	multiple_choice	What does the 'weighted' aspect of average atomic mass primarily refer to?	{"p_g": 0.25, "p_s": 0.1, "options": ["The natural abundance of each isotope", "The number of electrons in the atom", "The atomic number of the element", "The density of the element in its standard state"], "explanation": "The 'weighted' aspect means that the contribution of each isotope's mass to the average is proportional to its natural abundance. More abundant isotopes have a greater influence on the average.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
c292638d-2d92-4086-a961-e59d23d4d9cc	c18d6d95-77ed-4b41-a833-dc5cddec74f4	273db938-5cc8-4b34-8eab-ca7c0228b69d	multiple_choice	An element has two isotopes: Isotope X with a mass of 20.0 amu and Isotope Y with a mass of 22.0 amu. If the average atomic mass of the element is 20.4 amu, which statement is true?	{"p_g": 0.25, "p_s": 0.1, "options": ["Isotope X is more abundant than Isotope Y", "Isotope Y is more abundant than Isotope X", "Both isotopes are equally abundant", "The abundances cannot be determined from this information"], "explanation": "Since the average atomic mass (20.4 amu) is closer to the mass of Isotope X (20.0 amu) than to Isotope Y (22.0 amu), Isotope X must be more abundant. The average is 'pulled' more towards the more abundant isotope.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
4c65d864-e6e1-4468-8550-0ab971f5b126	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b0cc80c-b8cd-4aa0-8a4f-6b83a4beb821	multiple_choice	What is the approximate value of Avogadro's Constant?	{"p_g": 0.25, "p_s": 0.1, "options": ["6.022 x 10^23 mol⁻¹", "1.0 x 10^23 mol⁻¹", "6.022 x 10^22 mol⁻¹", "12.044 x 10^23 mol⁻¹"], "explanation": "Avogadro's Constant is defined as approximately 6.022 x 10^23 particles per mole.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
2c126795-ad42-4d46-a236-103da55376ce	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b0cc80c-b8cd-4aa0-8a4f-6b83a4beb821	multiple_choice	What does Avogadro's Constant represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["The number of particles in one mole of a substance", "The mass of one atom of a substance", "The volume occupied by one mole of a gas at STP", "The charge of a single electron"], "explanation": "Avogadro's Constant defines the number of individual particles (atoms, molecules, ions) present in exactly one mole of any substance.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
c240b479-5def-49b3-9e29-defb551de321	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b0cc80c-b8cd-4aa0-8a4f-6b83a4beb821	multiple_choice	If you have 0.5 moles of water (H₂O), how many water molecules do you have?	{"p_g": 0.25, "p_s": 0.1, "options": ["3.011 x 10^23 molecules", "6.022 x 10^23 molecules", "1.0 mole of molecules", "18.015 grams of molecules"], "explanation": "One mole of any substance contains Avogadro's Constant number of particles. Therefore, 0.5 moles would contain 0.5 * (6.022 x 10^23) molecules, which is 3.011 x 10^23 molecules.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
0d7aa4e1-b401-4e0c-a59c-acc72898528e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e90d1d47-7c6b-451f-9a20-c856c2287793	multiple_choice	What fundamental law is satisfied when a chemical equation is balanced?	{"p_g": 0.25, "p_s": 0.1, "options": ["Law of Conservation of Mass", "Law of Conservation of Energy", "Law of Definite Proportions", "Law of Multiple Proportions"], "explanation": "Balancing a chemical equation ensures that the number of atoms of each element remains constant on both sides of the reaction, which is a direct application of the Law of Conservation of Mass.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
8baff9ea-4434-40ff-a800-c6c94404796c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e90d1d47-7c6b-451f-9a20-c856c2287793	multiple_choice	Which of the following chemical equations is correctly balanced?	{"p_g": 0.25, "p_s": 0.1, "options": ["H₂ + O₂ → H₂O", "2H₂ + O₂ → 2H₂O", "H₂ + 2O₂ → 2H₂O", "2H₂ + 2O₂ → 2H₂O"], "explanation": "In the equation 2H₂ + O₂ → 2H₂O, there are 4 hydrogen atoms and 2 oxygen atoms on both the reactant and product sides, satisfying the Law of Conservation of Mass.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
fdd80280-c357-4cc9-b5b8-b316065087c1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e90d1d47-7c6b-451f-9a20-c856c2287793	multiple_choice	When the equation C₃H₈ + O₂ → CO₂ + H₂O is balanced using the smallest whole number coefficients, what is the coefficient for O₂?	{"p_g": 0.25, "p_s": 0.1, "options": ["3", "4", "5", "6"], "explanation": "To balance the equation C₃H₈ + O₂ → CO₂ + H₂O, we first balance carbon (3 CO₂) and hydrogen (4 H₂O). This results in 6 oxygen atoms from CO₂ and 4 from H₂O, totaling 10 oxygen atoms on the product side. Therefore, 5 O₂ molecules are needed on the reactant side.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
73dadde6-f1f3-40b0-965f-85e93d34b0cc	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4afa5162-a1e5-474c-b761-b53d5987199a	multiple_choice	What is the main reason for balancing a chemical equation?	{"p_g": 0.25, "p_s": 0.1, "options": ["To make the equation look aesthetically pleasing", "To ensure the number of atoms for each element is equal on both sides", "To change the products formed in the reaction", "To determine the speed of the chemical reaction"], "explanation": "Balancing chemical equations ensures that the Law of Conservation of Mass is upheld, meaning atoms are neither created nor destroyed during a chemical reaction.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
505f3059-e607-4946-93df-27c4a1fc6076	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4afa5162-a1e5-474c-b761-b53d5987199a	multiple_choice	When balancing the equation H₂ + O₂ → H₂O, what are the correct coefficients?	{"p_g": 0.25, "p_s": 0.1, "options": ["1, 1, 1", "2, 1, 2", "1, 2, 1", "2, 2, 2"], "explanation": "To balance the oxygen atoms, we need two H₂O molecules on the product side (2 oxygen atoms). This then requires four hydrogen atoms on the reactant side, so we need two H₂ molecules. Thus, 2H₂ + O₂ → 2H₂O.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
63a2be18-ab91-4ed0-abce-2e0236797fde	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4afa5162-a1e5-474c-b761-b53d5987199a	multiple_choice	What is the coefficient for O₂ when the following equation is correctly balanced: C₃H₈ + O₂ → CO₂ + H₂O?	{"p_g": 0.25, "p_s": 0.1, "options": ["3", "5", "7", "10"], "explanation": "First, balance C and H: C₃H₈ + O₂ → 3CO₂ + 4H₂O. Now count oxygen atoms on the product side: (3 * 2) + (4 * 1) = 6 + 4 = 10 oxygen atoms. Therefore, we need 5 O₂ molecules on the reactant side. The balanced equation is C₃H₈ + 5O₂ → 3CO₂ + 4H₂O.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
d2c42cbf-acdc-43f9-a7db-3d9e81404a5c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8bc0947c-fc7b-4ac9-b7e4-75de9cd8501c	multiple_choice	What is the primary purpose of a Bohr-Rutherford diagram?	{"p_g": 0.25, "p_s": 0.1, "options": ["To show the number of protons and neutrons in the nucleus.", "To illustrate the arrangement of electrons in an atom's shells.", "To depict the chemical bonds between atoms.", "To measure the atomic mass of an element."], "explanation": "Bohr-Rutherford diagrams visually represent how electrons are arranged in different energy levels around the nucleus of an atom.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
7ace69ae-cf88-4632-b4d6-793bbd1f6cde	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8bc0947c-fc7b-4ac9-b7e4-75de9cd8501c	multiple_choice	In a Bohr-Rutherford diagram, what do the concentric circles around the nucleus represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["The different isotopes of an element.", "The pathways of protons within the nucleus.", "Different electron energy levels or shells.", "The magnetic fields surrounding the atom."], "explanation": "Each concentric circle in a Bohr-Rutherford diagram corresponds to a specific electron energy level or shell, where electrons are found.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
985ad5ab-442a-49a5-948c-905af87ca55c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8bc0947c-fc7b-4ac9-b7e4-75de9cd8501c	multiple_choice	An atom's Bohr-Rutherford diagram shows 2 electrons in the first shell, 8 electrons in the second shell, and 1 electron in the third shell. What is the atomic number of this neutral atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["10", "11", "12", "18"], "explanation": "The total number of electrons in a neutral atom equals its atomic number. In this case, 2 + 8 + 1 = 11 electrons, so the atomic number is 11.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
564ca76c-25a1-476b-91fa-46da3cf07745	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9f3e2e71-93a7-4cb6-bcb4-66444cb63aa4	multiple_choice	What type of charge does a cation have?	{"p_g": 0.25, "p_s": 0.1, "options": ["Positive", "Negative", "Neutral", "Both positive and negative"], "explanation": "A cation is defined as a positively charged ion.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
3f09a0d9-0391-476d-ac04-f1a2de5e52aa	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9f3e2e71-93a7-4cb6-bcb4-66444cb63aa4	multiple_choice	How is a cation formed from a neutral atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["By gaining electrons", "By losing electrons", "By gaining protons", "By losing neutrons"], "explanation": "Cations are formed when an atom loses one or more negatively charged electrons, resulting in a net positive charge.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
99f201fb-ffff-46e2-8c48-7e46df40140c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9f3e2e71-93a7-4cb6-bcb4-66444cb63aa4	multiple_choice	Which of the following elements is most likely to form a cation?	{"p_g": 0.25, "p_s": 0.1, "options": ["Chlorine (Cl)", "Sodium (Na)", "Oxygen (O)", "Neon (Ne)"], "explanation": "Sodium (Na) is an alkali metal in Group 1, meaning it readily loses its single valence electron to achieve a stable electron configuration, thus forming a +1 cation (Na+). Chlorine (Cl) typically forms anions, Oxygen (O) forms anions, and Neon (Ne) is a noble gas and is generally unreactive.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
f5030955-c5e8-4e95-ba35-7dbe144be6f7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	22257e97-8a88-4665-87f5-a9d9c69d66b2	multiple_choice	Which of the following is an example of a chemical change?	{"p_g": 0.25, "p_s": 0.1, "options": ["Melting ice", "Boiling water", "Dissolving sugar in water", "Iron rusting"], "explanation": "Rusting iron involves a reaction between iron and oxygen to form a new substance, iron oxide, which is a chemical change.", "correct_answer": 3}	easy	\N	2025-11-24 08:08:04.009802+00
581217b5-8a0d-4149-b653-2acaa5011db9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	22257e97-8a88-4665-87f5-a9d9c69d66b2	multiple_choice	What is the primary characteristic that distinguishes a chemical change from a physical change?	{"p_g": 0.25, "p_s": 0.1, "options": ["A change in state (solid, liquid, gas)", "The formation of one or more new substances", "A change in temperature", "The dissolving of one substance into another"], "explanation": "Chemical changes result in the formation of entirely new substances with different chemical properties, unlike physical changes which only alter appearance or state.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
963c4519-6b9b-4783-bc8e-60fd104facbe	c18d6d95-77ed-4b41-a833-dc5cddec74f4	22257e97-8a88-4665-87f5-a9d9c69d66b2	multiple_choice	When a chemical change occurs, which of the following statements is always true?	{"p_g": 0.25, "p_s": 0.1, "options": ["The mass of the substances involved decreases.", "The physical state of the matter always changes.", "New atoms are created or destroyed.", "The atoms are rearranged to form new substances."], "explanation": "In a chemical change, the atoms are rearranged to form new molecules or compounds, but the total number of atoms of each element remains constant, adhering to the Law of Conservation of Mass.", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
2e33ba36-712c-44c0-b686-62343727ed24	c18d6d95-77ed-4b41-a833-dc5cddec74f4	a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	multiple_choice	What does the arrow (→) in a chemical equation primarily represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["The rate of reaction", "The energy change", "The separation of reactants from products", "A reversible reaction"], "explanation": "The arrow in a chemical equation separates the reactants (on the left) from the products (on the right) and indicates the direction of the chemical reaction.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
aa9f28f3-952b-4ce1-a3ac-232b6509b860	c18d6d95-77ed-4b41-a833-dc5cddec74f4	a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	multiple_choice	In the balanced chemical equation 2H₂ + O₂ → 2H₂O, what do the coefficients (the '2's) represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["The physical state of the substance", "The molar ratio of reactants and products", "The atomic number of the element", "The temperature at which the reaction occurs"], "explanation": "The coefficients in a balanced chemical equation indicate the relative number of moles or molecules of each reactant and product involved in the reaction. In this case, 2 molecules of hydrogen react with 1 molecule of oxygen to produce 2 molecules of water.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
fb6bcbaf-08ad-4d91-81ca-2463698c111c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	a5f7aa82-f23e-4c3b-b7a5-84588d0aa55e	multiple_choice	Consider the chemical equation: C₆H₁₂O₆(aq) + 6O₂(g) → 6CO₂(g) + 6H₂O(l). Which statement about the state symbols is correct?	{"p_g": 0.25, "p_s": 0.1, "options": ["Glucose is a solid reactant.", "Oxygen is produced as a liquid.", "Carbon dioxide is a gaseous product.", "Water is an aqueous reactant."], "explanation": "The state symbol '(aq)' indicates an aqueous solution, meaning the substance is dissolved in water. '(g)' indicates a gas, and '(l)' indicates a liquid. Therefore, glucose is dissolved in water, not solid. Oxygen is a gas, as is carbon dioxide, and water is produced as a liquid.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f5ec2566-db10-41b1-8caf-01aafe79c82b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	04f0e698-00ba-4dbc-af60-8cc83833fb43	multiple_choice	What does the '2' in H₂O represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["Two oxygen atoms", "Two hydrogen atoms", "Two molecules of water", "The charge of the molecule"], "explanation": "In a chemical formula, the subscript number indicates the number of atoms of the element immediately preceding it. So, '2' in H₂O means there are two hydrogen atoms.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
30af598d-3c32-4806-9c1e-023f6472efad	c18d6d95-77ed-4b41-a833-dc5cddec74f4	04f0e698-00ba-4dbc-af60-8cc83833fb43	multiple_choice	Which of the following chemical formulas correctly represents a compound with one carbon atom and two oxygen atoms?	{"p_g": 0.25, "p_s": 0.1, "options": ["CO", "C₂O", "CO₂", "C₂O₂"], "explanation": "The formula CO₂ indicates one carbon atom (no subscript means 1) and two oxygen atoms (subscript 2).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
802edd61-b947-496c-9ac8-fd01d794e7ce	c18d6d95-77ed-4b41-a833-dc5cddec74f4	04f0e698-00ba-4dbc-af60-8cc83833fb43	multiple_choice	In the chemical formula Ca₃(PO₄)₂, how many oxygen atoms are present?	{"p_g": 0.25, "p_s": 0.1, "options": ["4", "2", "8", "6"], "explanation": "The subscript '4' inside the parenthesis indicates four oxygen atoms per phosphate group (PO₄). The subscript '2' outside the parenthesis means there are two phosphate groups. Therefore, 4 oxygen atoms/group * 2 groups = 8 oxygen atoms in total.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
15f4545f-bebf-493f-aed6-aa80d78e6d49	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b932e5fc-ef40-4a50-b7f3-f2ea1944cae0	multiple_choice	Which of the following is an example of a chemical property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Density", "Boiling point", "Flammability", "Color"], "explanation": "Flammability describes a substance's ability to burn, which is a chemical change where it reacts with oxygen to form new substances.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
a98cf092-ea25-4d8e-859b-74ea8d7b6da0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b932e5fc-ef40-4a50-b7f3-f2ea1944cae0	multiple_choice	A chemical property is best described as a characteristic that:	{"p_g": 0.25, "p_s": 0.1, "options": ["Can be measured without changing the substance's composition.", "Describes the physical state of matter (solid, liquid, gas).", "Is observed when a substance is converted into a new substance.", "Relates to the amount of matter in an object."], "explanation": "Chemical properties are observed when a substance undergoes a chemical reaction, transforming it into one or more new substances. For example, iron rusting forms iron oxide, a new substance.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
3e8c3a01-c380-4be2-b368-5869835795b0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b932e5fc-ef40-4a50-b7f3-f2ea1944cae0	multiple_choice	When a silver spoon tarnishes and turns black, which chemical property is being demonstrated?	{"p_g": 0.25, "p_s": 0.1, "options": ["Silver's ductility (ability to be drawn into wires).", "Silver's melting point.", "Silver's luster (shininess).", "Silver's reactivity with sulfur compounds."], "explanation": "Tarnishing is a chemical reaction where silver reacts with sulfur compounds in the air to form silver sulfide, a new substance. This demonstrates silver's reactivity.", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
86d85a11-e20b-4058-8921-17312b202fe9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	464b5adc-4ee5-468b-aedc-638ac8cbc498	multiple_choice	Which of the following best describes a chemical reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["A change in the state of matter (e.g., solid to liquid)", "The formation of new substances with different properties", "A physical change that alters the appearance but not the composition", "The separation of a mixture into its components"], "explanation": "A chemical reaction is defined by the formation of new substances with different properties from the original reactants.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
99c4c916-f248-4eaa-8a0d-66486fe227b5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	464b5adc-4ee5-468b-aedc-638ac8cbc498	multiple_choice	Which of these is a clear indicator that a chemical reaction has likely occurred?	{"p_g": 0.25, "p_s": 0.1, "options": ["Water boiling", "Sugar dissolving in water", "Formation of a gas (bubbles) when two liquids are mixed", "Ice melting"], "explanation": "The production of a gas (like bubbles), a change in color, or the formation of a precipitate are common visual signs of a chemical reaction, indicating new substances have formed.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
8583b933-3e2a-4ba4-a1cf-325c8d24f70c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	464b5adc-4ee5-468b-aedc-638ac8cbc498	multiple_choice	When iron rusts, it combines with oxygen to form iron oxide. This is an example of a chemical reaction because:	{"p_g": 0.25, "p_s": 0.1, "options": ["The iron changes its physical state", "A new substance with different properties is formed", "The iron simply changes color but remains iron", "It requires heat to occur"], "explanation": "Rusting is a chemical reaction because iron oxide (rust) has completely different chemical and physical properties than elemental iron and oxygen, indicating a new substance has been formed.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
57577328-4545-4bef-8b02-b6cba0397f11	c18d6d95-77ed-4b41-a833-dc5cddec74f4	000693e1-5479-4dd8-a63f-4535e7927c96	multiple_choice	Which type of reaction combines two or more reactants to form a single, more complex product?	{"p_g": 0.25, "p_s": 0.1, "options": ["Synthesis reaction", "Decomposition reaction", "Single displacement reaction", "Combustion reaction"], "explanation": "A synthesis reaction is characterized by the formation of a single product from multiple reactants, often represented as A + B → AB.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
0e8f790d-3c12-4482-8194-a32b1a545ade	c18d6d95-77ed-4b41-a833-dc5cddec74f4	000693e1-5479-4dd8-a63f-4535e7927c96	multiple_choice	Consider the reaction: 2KClO₃(s) → 2KCl(s) + 3O₂(g). How would you classify this chemical reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["Synthesis reaction", "Decomposition reaction", "Single displacement reaction", "Double displacement reaction"], "explanation": "In this reaction, a single compound (potassium chlorate) breaks down into two simpler substances (potassium chloride and oxygen gas), which is the definition of a decomposition reaction.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
039386b6-1f66-4eeb-a1d8-770669297258	c18d6d95-77ed-4b41-a833-dc5cddec74f4	000693e1-5479-4dd8-a63f-4535e7927c96	multiple_choice	Which of the following reactions is an example of a single displacement reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["H₂SO₄ + 2NaOH → Na₂SO₄ + 2H₂O", "CH₄ + 2O₂ → CO₂ + 2H₂O", "Zn + 2HCl → ZnCl₂ + H₂", "2Mg + O₂ → 2MgO"], "explanation": "In a single displacement reaction, one element replaces another element in a compound. In choice C, zinc replaces hydrogen in hydrochloric acid to form zinc chloride and hydrogen gas.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
cc78ad22-42e2-4635-8b0b-30cfc35abeea	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ee8253d0-ef7c-4704-ac3f-b3e7507d86a6	multiple_choice	What is typically produced in a combustion reaction, besides heat and light?	{"p_g": 0.25, "p_s": 0.1, "options": ["Oxygen and nitrogen", "Carbon dioxide and water", "Hydrogen and helium", "Acids and bases"], "explanation": "Combustion reactions involve a substance reacting with oxygen to form oxides. For organic compounds, this commonly means carbon dioxide and water.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
be5fbffa-54af-4866-9bca-c1a39ac91fc2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ee8253d0-ef7c-4704-ac3f-b3e7507d86a6	multiple_choice	Which of the following is always a reactant in a combustion reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["Carbon", "Hydrogen", "Oxygen", "Nitrogen"], "explanation": "By definition, a combustion reaction is the reaction of a compound or element with oxygen. Oxygen is essential for combustion to occur.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
60bc14e5-ed3b-47b3-ae12-6593e688cfda	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ee8253d0-ef7c-4704-ac3f-b3e7507d86a6	multiple_choice	Why is a combustion reaction considered an exothermic process?	{"p_g": 0.25, "p_s": 0.1, "options": ["It absorbs heat from the surroundings.", "It requires a catalyst to occur.", "It releases energy in the form of heat and light.", "It only occurs at very low temperatures."], "explanation": "Exothermic reactions release energy, typically in the form of heat and light, into the surroundings. Combustion reactions are characterized by this release of energy.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
261a92c9-6e9a-4332-b450-b61f7bd9c19e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c652b196-322b-4ee0-b263-abd18fe13b1d	multiple_choice	What are the primary products of a complete combustion reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["Carbon dioxide and water", "Carbon monoxide and water", "Carbon and hydrogen", "Oxygen and fuel"], "explanation": "In complete combustion, with sufficient oxygen, a carbon-containing compound always produces carbon dioxide and water.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
d39fabca-fc5a-4e27-85df-10ee3ce4f8a5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c652b196-322b-4ee0-b263-abd18fe13b1d	multiple_choice	Which of the following conditions is essential for a complete combustion reaction to occur?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sufficient oxygen", "High pressure", "Absence of heat", "Presence of a catalyst"], "explanation": "Complete combustion requires a sufficient supply of oxygen. If oxygen is limited, incomplete combustion occurs, producing carbon monoxide or soot.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
9ffcb17e-083f-4378-8911-39da0b25ad92	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c652b196-322b-4ee0-b263-abd18fe13b1d	multiple_choice	Why is carbon monoxide (CO) typically NOT a product of complete combustion?	{"p_g": 0.25, "p_s": 0.1, "options": ["Complete combustion provides enough oxygen for carbon to fully oxidize to CO2.", "Carbon monoxide is a noble gas and does not form in reactions.", "The reaction temperature is too low for CO to form.", "Carbon monoxide is only produced from nitrogen-containing compounds."], "explanation": "Carbon monoxide is a product of incomplete combustion, which occurs when there is insufficient oxygen. In complete combustion, carbon reacts fully with oxygen to form carbon dioxide.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
fc5da311-68f6-47e8-a0d0-99494030a6e7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	bad9a3fc-a0e7-473b-9e77-5973aadd86b4	multiple_choice	Which of the following best describes a compound?	{"p_g": 0.25, "p_s": 0.1, "options": ["A substance made of only one type of atom.", "A mixture of different elements that are not chemically bonded.", "A pure substance formed when two or more elements are chemically combined in a fixed ratio.", "Any combination of two or more substances."], "explanation": "A compound is defined as a pure substance made of two or more different elements chemically bonded together in a fixed ratio.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
1ffa6046-afc6-4594-bbc4-6aa86e823c18	c18d6d95-77ed-4b41-a833-dc5cddec74f4	bad9a3fc-a0e7-473b-9e77-5973aadd86b4	multiple_choice	Which of the following is an example of a compound?	{"p_g": 0.25, "p_s": 0.1, "options": ["Oxygen gas (O₂)", "Water (H₂O)", "Air", "Gold (Au)"], "explanation": "Water (H₂O) is a compound because it consists of hydrogen and oxygen atoms chemically bonded together in a fixed ratio (2:1). Oxygen gas (O₂) is an element, air is a mixture, and gold (Au) is an element.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
38e1e651-5a56-48f3-9454-360b636aada7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	bad9a3fc-a0e7-473b-9e77-5973aadd86b4	multiple_choice	What is a key difference between a compound and a mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["Compounds can be separated by physical means, while mixtures cannot.", "Elements in a compound retain their original properties, unlike in a mixture.", "Compounds have a fixed ratio of elements and new chemical properties, whereas mixtures have variable ratios and retain component properties.", "Mixtures always have a uniform composition, while compounds do not."], "explanation": "In a compound, elements are chemically bonded, forming a new substance with properties distinct from its constituent elements. In a mixture, substances are physically combined and retain their individual properties.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
6915fe3b-5c08-437a-a16e-6f9647715b7a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	f4bc3b56-1a4d-4965-9387-55fd28918dd1	multiple_choice	Which type of elements typically combine to form covalent compounds?	{"p_g": 0.25, "p_s": 0.1, "options": ["Metals and non-metals", "Two metals", "Two non-metals", "Noble gases"], "explanation": "Covalent compounds are formed by the sharing of electrons, primarily between two or more non-metal atoms.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
66ef627b-30eb-4f55-a2e0-67bba2a9b981	c18d6d95-77ed-4b41-a833-dc5cddec74f4	f4bc3b56-1a4d-4965-9387-55fd28918dd1	multiple_choice	Which of the following is a characteristic property of covalent compounds?	{"p_g": 0.25, "p_s": 0.1, "options": ["High melting points", "Good electrical conductivity when dissolved in water", "Low melting points", "Formation of ions in solid state"], "explanation": "Covalent compounds consist of discrete molecules held together by weaker intermolecular forces, leading to lower energy required to separate them, hence lower melting and boiling points compared to ionic compounds.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
9a691f57-525c-4445-8a50-e68862444154	c18d6d95-77ed-4b41-a833-dc5cddec74f4	f4bc3b56-1a4d-4965-9387-55fd28918dd1	multiple_choice	Why are most covalent compounds poor conductors of electricity?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have strong metallic bonds", "They readily form positive and negative ions", "Their electrons are delocalized throughout the structure", "They consist of discrete molecules with no free-moving charged particles"], "explanation": "Covalent compounds are made up of neutral molecules, meaning they do not have free-moving ions or delocalized electrons that are necessary to conduct electricity.", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
0ad3e951-5a65-4975-adaa-ba1911045864	c18d6d95-77ed-4b41-a833-dc5cddec74f4	83051056-852e-488d-838b-60378a5ab269	multiple_choice	According to Dalton's Atomic Theory, what is the fundamental building block of all matter?	{"p_g": 0.25, "p_s": 0.1, "options": ["Molecules", "Protons", "Atoms", "Electrons"], "explanation": "One of the core postulates of Dalton's theory is that all matter is composed of tiny, indivisible particles called atoms.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
824210c7-9c36-43ce-968c-a4e1eac1cce7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	83051056-852e-488d-838b-60378a5ab269	multiple_choice	Which statement best describes how atoms of a specific element are characterized according to Dalton's theory?	{"p_g": 0.25, "p_s": 0.1, "options": ["They are all different in mass and properties.", "They are identical in mass and properties.", "They can be divided into smaller particles.", "They can change into atoms of another element."], "explanation": "Dalton proposed that all atoms of a given element are identical in mass and properties, distinguishing them from atoms of other elements.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
8dfd5629-d1ca-4c79-8f24-b3c5d133eb27	c18d6d95-77ed-4b41-a833-dc5cddec74f4	83051056-852e-488d-838b-60378a5ab269	multiple_choice	Dalton's theory states that atoms combine in specific proportions to form compounds. What does this imply about the composition of a pure compound?	{"p_g": 0.25, "p_s": 0.1, "options": ["The composition of a compound can vary depending on its source.", "Compounds are formed by random combinations of atoms.", "A pure compound always has the same elemental composition by mass.", "Atoms within a compound lose their individual identities completely."], "explanation": "The idea of atoms combining in specific, fixed ratios means that a given compound will always have the same relative numbers and types of atoms, leading to a consistent composition.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
51cd4a3f-c99a-4ea1-b72f-016505941d07	c18d6d95-77ed-4b41-a833-dc5cddec74f4	33ee5649-eb89-403f-b2ea-9591452df4dd	multiple_choice	Which of the following represents the general form of a decomposition reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["C → A + B", "A + B → C", "AB + CD → AD + CB", "A + BC → AC + B"], "explanation": "A decomposition reaction involves a single compound breaking down into two or more simpler substances, fitting the C → A + B pattern.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
96d8bf78-c62a-42a6-b12b-6d920545cae8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	33ee5649-eb89-403f-b2ea-9591452df4dd	multiple_choice	Which of the following is an example of a decomposition reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["2H₂O → 2H₂ + O₂", "N₂ + 3H₂ → 2NH₃", "HCl + NaOH → NaCl + H₂O", "Zn + CuSO₄ → ZnSO₄ + Cu"], "explanation": "In this reaction, a single compound (H₂O) breaks down into two simpler elements (H₂ and O₂), which is characteristic of a decomposition reaction.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
79b5d3d5-0b36-4249-8bdf-8f52419e60b2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	33ee5649-eb89-403f-b2ea-9591452df4dd	multiple_choice	Why do many decomposition reactions require an input of energy (e.g., heat, light, electricity)?	{"p_g": 0.25, "p_s": 0.1, "options": ["To break existing bonds in the reactant compound.", "To form new bonds in the product compounds.", "To increase the activation energy of the reverse reaction.", "To prevent the products from recombining."], "explanation": "Energy is required to break the chemical bonds holding the original compound together. Once these bonds are broken, the atoms can rearrange to form simpler products.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
b029bc3a-389c-478d-89ff-1dcd9959da3f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c327243c-bf6c-4a4a-8ccf-bc9fb2371214	multiple_choice	What is the electrical charge of an electron?	{"p_g": 0.25, "p_s": 0.1, "options": ["Positive", "Negative", "Neutral", "Varies depending on the atom"], "explanation": "Electrons are defined as negatively charged subatomic particles, carrying a charge of -1.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
75aa19a4-6ec2-4234-a042-713e8318cc52	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c327243c-bf6c-4a4a-8ccf-bc9fb2371214	multiple_choice	In an atom, where are electrons primarily located?	{"p_g": 0.25, "p_s": 0.1, "options": ["Inside the nucleus with protons", "Inside the nucleus with neutrons", "In the space surrounding the nucleus", "They are not part of the atom's structure"], "explanation": "Electrons occupy the space surrounding the atomic nucleus, often described as electron shells or orbitals.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
cc49d464-9e0e-4204-a7fa-28efc05cb537	c18d6d95-77ed-4b41-a833-dc5cddec74f4	039329d6-e56a-4e5e-af23-7779df97f7b6	multiple_choice	Why is incomplete combustion considered more dangerous than complete combustion in an enclosed space?	{"p_g": 0.25, "p_s": 0.1, "options": ["It produces toxic carbon monoxide gas", "It releases more heat energy", "It consumes oxygen at a faster rate", "It creates a visible smoke that obscures vision"], "explanation": "Incomplete combustion produces carbon monoxide (CO), a highly toxic and odorless gas that can cause severe health issues or death by reducing oxygen transport in the blood.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
c9540abc-82b8-408d-93b1-f0dcdd75f25b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c327243c-bf6c-4a4a-8ccf-bc9fb2371214	multiple_choice	Why is the mass of an electron often considered approximately zero in atomic mass calculations?	{"p_g": 0.25, "p_s": 0.1, "options": ["Because electrons have no mass at all", "Because their mass is much smaller compared to protons and neutrons", "Because they are not fundamental particles", "Because their negative charge cancels out their mass"], "explanation": "While electrons do have mass, it is significantly smaller (about 1/1836) than the mass of protons and neutrons, making its contribution to the overall atomic mass negligible for most calculations.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
61f56e38-9fb7-4a29-a4dc-3f13ded159f9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2acf682f-81ba-4ea3-887d-a01f89456fc0	multiple_choice	What does electron affinity measure?	{"p_g": 0.25, "p_s": 0.1, "options": ["The energy required to remove an electron from an atom.", "The energy released or absorbed when an electron is added to a neutral atom.", "The ability of an atom to attract electrons in a chemical bond.", "The size of an atom's electron cloud."], "explanation": "Electron affinity is defined as the energy change when an electron is added to a neutral atom to form a negative ion.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
7350354c-949e-47f0-876c-71f00c7434c1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2acf682f-81ba-4ea3-887d-a01f89456fc0	multiple_choice	Which of the following elements would generally have the most negative (most favorable) electron affinity?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sodium (Na)", "Argon (Ar)", "Chlorine (Cl)", "Carbon (C)"], "explanation": "Elements in Group 17 (halogens) have a strong tendency to gain one electron to achieve a stable noble gas configuration, making their electron affinities highly negative (exothermic).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
60d5d1cb-d4ed-4abb-bf5e-5122da1841f9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2acf682f-81ba-4ea3-887d-a01f89456fc0	multiple_choice	Why do noble gases typically have positive (unfavorable) electron affinities?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have very small atomic radii, making it difficult to add an electron.", "Their nuclei are not strong enough to attract an additional electron.", "They already have a stable, full valence electron shell, so adding an electron requires energy.", "They readily form positive ions, not negative ones."], "explanation": "Noble gases already have a stable, full outer electron shell. Adding an electron would require it to occupy a higher energy level, making the process energetically unfavorable (requires energy input, thus positive electron affinity).", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
00ca81c3-ffac-4660-ae83-8247b91cc80f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	36f222f3-edbf-4515-8187-f65e53de0af4	multiple_choice	What describes the regions where electrons are found around an atomic nucleus?	{"p_g": 0.25, "p_s": 0.1, "options": ["Nucleons", "Proton shells", "Electron energy levels", "Neutron clouds"], "explanation": "Electron energy levels are specific regions where electrons orbit the nucleus, each with a distinct energy.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
4a5367f2-ff07-41ed-90f2-07bd85201b7e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	36f222f3-edbf-4515-8187-f65e53de0af4	multiple_choice	What happens when an electron moves from a higher energy level to a lower energy level?	{"p_g": 0.25, "p_s": 0.1, "options": ["It absorbs energy", "It emits a photon of light", "Its mass increases", "It becomes a neutron"], "explanation": "When an electron moves from a higher (less stable) energy level to a lower (more stable) energy level, it releases the energy difference in the form of a photon of light.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
11840979-2b2e-42a0-826e-43d7ce5fb454	c18d6d95-77ed-4b41-a833-dc5cddec74f4	36f222f3-edbf-4515-8187-f65e53de0af4	multiple_choice	Which statement best explains why electron energy levels are 'quantized'?	{"p_g": 0.25, "p_s": 0.1, "options": ["Electrons can occupy any energy value around the nucleus.", "Electrons can only exist at specific, discrete energy values.", "The energy of an electron continuously changes as it orbits.", "Electron energy levels are defined by the number of neutrons."], "explanation": "Quantized means that electrons can only exist at specific, discrete energy values, not in between. This is a fundamental concept in quantum mechanics and explains atomic spectra.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
7f3972e9-e2d7-4e20-ba46-8685ce3f6bd3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	acf03374-c7a9-4e9f-8378-50d85cdfb926	multiple_choice	What does electronegativity measure?	{"p_g": 0.25, "p_s": 0.1, "options": ["The ability of an atom to lose an electron.", "The size of an atom's nucleus.", "The ability of an atom to attract shared electrons in a bond.", "The number of valence electrons an atom has."], "explanation": "Electronegativity quantifies an atom's tendency to attract shared electrons towards itself in a covalent bond.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
9868b30f-b60f-43ac-a7ea-bc59787962ce	c18d6d95-77ed-4b41-a833-dc5cddec74f4	acf03374-c7a9-4e9f-8378-50d85cdfb926	multiple_choice	Which of the following elements is generally considered the most electronegative?	{"p_g": 0.25, "p_s": 0.1, "options": ["Lithium (Li)", "Oxygen (O)", "Fluorine (F)", "Carbon (C)"], "explanation": "Fluorine (F) is the most electronegative element on the periodic table due to its small size and high effective nuclear charge.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
e3d677c3-f578-4820-ab67-309c11d442e5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	acf03374-c7a9-4e9f-8378-50d85cdfb926	multiple_choice	If two atoms have a very large difference in their electronegativity values, what type of bond are they most likely to form?	{"p_g": 0.25, "p_s": 0.1, "options": ["Nonpolar covalent bond", "Polar covalent bond", "Ionic bond", "Metallic bond"], "explanation": "A large difference in electronegativity indicates a strong attraction of electrons by one atom, leading to a complete transfer of electrons and the formation of an ionic bond.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
35baf122-2f57-4c7f-aad0-554c231d0719	c18d6d95-77ed-4b41-a833-dc5cddec74f4	133f59c8-33de-4a31-87ec-1b0263e36684	multiple_choice	What is the primary purpose of calculating the electronegativity difference between two atoms in a bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["To determine the atomic number of the elements.", "To predict the type of chemical bond formed.", "To calculate the molecular mass of the compound.", "To measure the boiling point of the substance."], "explanation": "The electronegativity difference is a key indicator used to predict whether a chemical bond will be ionic, polar covalent, or nonpolar covalent.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
fb38688b-1af2-4071-af98-edde23d47d8c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	133f59c8-33de-4a31-87ec-1b0263e36684	multiple_choice	If two atoms have a very large electronegativity difference (e.g., greater than 1.7), what type of bond is most likely to form between them?	{"p_g": 0.25, "p_s": 0.1, "options": ["Nonpolar covalent bond", "Polar covalent bond", "Ionic bond", "Metallic bond"], "explanation": "A large electronegativity difference indicates that one atom has a much stronger pull on shared electrons than the other, leading to a complete transfer of electrons and the formation of an ionic bond.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
b993bacc-0245-4a85-9370-ac3be525379f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	133f59c8-33de-4a31-87ec-1b0263e36684	multiple_choice	A bond between two atoms has an electronegativity difference of 0.6. Which statement accurately describes this bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["It is a nonpolar covalent bond because the difference is less than 1.0.", "It is an ionic bond due to a significant electron transfer.", "It is a polar covalent bond with unequal sharing of electrons.", "It is a metallic bond, indicating a sea of delocalized electrons."], "explanation": "An electronegativity difference between approximately 0.4 and 1.7 generally indicates a polar covalent bond, where electrons are shared unequally, creating partial positive and negative charges on the atoms.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
5ac656bd-8967-4449-b40b-c94c55d55617	c18d6d95-77ed-4b41-a833-dc5cddec74f4	228a3e15-0186-487f-b5e9-b8167f2a530f	multiple_choice	Which of the following best describes an element?	{"p_g": 0.25, "p_s": 0.1, "options": ["A substance made of different types of atoms bonded together.", "A mixture of various compounds.", "A basic substance made up of only one kind of atom.", "A substance that can be broken down into simpler substances by chemical means."], "explanation": "An element is defined as a pure substance consisting only of atoms that all have the same numbers of protons in their nuclei.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
a3215dfc-ca5e-410e-bcd7-26436bf97cb0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	228a3e15-0186-487f-b5e9-b8167f2a530f	multiple_choice	Which of these is an example of an element?	{"p_g": 0.25, "p_s": 0.1, "options": ["Water (H2O)", "Oxygen (O2)", "Air", "Salt water"], "explanation": "Oxygen (O) is found on the periodic table and consists only of oxygen atoms. Water (H2O) is a compound, and air and salt water are mixtures.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
7cbf236e-ce0c-4a5d-b3f7-e5244d766d15	c18d6d95-77ed-4b41-a833-dc5cddec74f4	228a3e15-0186-487f-b5e9-b8167f2a530f	multiple_choice	Why is a compound like water (H2O) NOT considered an element?	{"p_g": 0.25, "p_s": 0.1, "options": ["Because it is a liquid at room temperature.", "Because it can be found in nature.", "Because it is made up of more than one type of atom.", "Because its atoms are too small to be seen."], "explanation": "An element is composed of only one type of atom. Water is composed of two different types of atoms (hydrogen and oxygen) chemically bonded together, making it a compound.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
063cbafb-9749-4454-816d-4f39b3262275	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0d586faa-0d57-448c-9bad-adb3d226ca2c	multiple_choice	What is the primary factor that leads to eutrophication in a body of water?	{"p_g": 0.25, "p_s": 0.1, "options": ["Excess sediment", "Excess nutrients", "Low water temperature", "High levels of salinity"], "explanation": "Eutrophication is caused by an excessive input of nutrients, primarily nitrates and phosphates, into aquatic ecosystems.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
8680e0cd-ca00-4744-96ff-8252d365c4fa	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0d586faa-0d57-448c-9bad-adb3d226ca2c	multiple_choice	Which of the following is a common direct consequence of the dense plant growth (like algal blooms) associated with eutrophication?	{"p_g": 0.25, "p_s": 0.1, "options": ["Increased biodiversity", "Improved water clarity", "Depletion of dissolved oxygen", "Lower water acidity"], "explanation": "When the dense plant life from eutrophication dies, decomposers consume large amounts of dissolved oxygen in the water, leading to hypoxia or anoxia.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
2eaced48-e072-4288-a096-d5c03865426e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0d586faa-0d57-448c-9bad-adb3d226ca2c	multiple_choice	Which human activity is most likely to contribute to eutrophication in a nearby freshwater lake?	{"p_g": 0.25, "p_s": 0.1, "options": ["Building a dam for hydroelectric power", "Discharging treated wastewater from a modern sewage treatment plant", "Extensive use of fertilizers on agricultural fields upstream", "Increased recreational boating activity"], "explanation": "Agricultural runoff often contains fertilizers rich in nitrogen and phosphorus, which are the key excess nutrients that drive eutrophication when they enter bodies of water.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
bd08ef57-0d6f-406f-bf26-2d67bb69cb05	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b6934fa-1d81-47be-a7e7-bf00a0e8d672	multiple_choice	What do the vertical columns in the periodic table represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["Periods", "Groups", "Blocks", "Series"], "explanation": "Vertical columns in the periodic table are called groups, and elements within them share similar properties.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
fc008cae-ce00-482e-8ee6-63e6bd16b365	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b6934fa-1d81-47be-a7e7-bf00a0e8d672	multiple_choice	Elements in the same group of the periodic table typically have the same number of what?	{"p_g": 0.25, "p_s": 0.1, "options": ["Protons", "Neutrons", "Valence electrons", "Electron shells"], "explanation": "Elements in the same group have the same number of valence electrons, which largely determines their chemical reactivity and similar properties.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
b6b42c06-bb9c-4fc3-9588-b622c9815640	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0b6934fa-1d81-47be-a7e7-bf00a0e8d672	multiple_choice	Which of the following statements is true regarding elements within the same group?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have identical chemical properties.", "Their atomic number is always the same.", "They tend to have similar chemical properties.", "Their atomic radius always decreases down the group."], "explanation": "While elements in a group share similar chemical properties due to valence electrons, their atomic radius generally increases down a group because more electron shells are added.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
c5e329d9-dd5c-4fb5-8dad-b1c5bfe2d941	c18d6d95-77ed-4b41-a833-dc5cddec74f4	6dbb9dd7-71df-4e31-b019-a9d1b4367466	multiple_choice	Which of the following halogens is the most reactive?	{"p_g": 0.25, "p_s": 0.1, "options": ["Fluorine", "Chlorine", "Bromine", "Iodine"], "explanation": "The halogen activity series ranks reactivity as F > Cl > Br > I, making Fluorine the most reactive.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
4f9cb226-5c45-4a5e-90eb-e43258332ec0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	6dbb9dd7-71df-4e31-b019-a9d1b4367466	multiple_choice	Based on the halogen activity series, which of the following reactions will occur?	{"p_g": 0.25, "p_s": 0.1, "options": ["NaCl(aq) + Br₂(g) →", "NaBr(aq) + I₂(s) →", "NaI(aq) + Cl₂(g) →", "NaF(aq) + Br₂(g) →"], "explanation": "A more reactive free halogen can displace a less reactive halide ion from its salt. Chlorine (Cl) is more reactive than Iodine (I), so Cl₂ will displace I⁻ from NaI. In the other options, the free halogen is less reactive than the halide ion in the salt, so no reaction occurs.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
1763a213-48e0-4e8d-ac1c-298efc03d1d8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	46660a32-049e-4e5f-ab06-83a887567478	multiple_choice	What do intermolecular forces primarily act between?	{"p_g": 0.25, "p_s": 0.1, "options": ["Atoms within a molecule", "Protons and neutrons in a nucleus", "Neighboring molecules", "Ions in an ionic compound"], "explanation": "Intermolecular forces are defined as the attractive or repulsive forces that act between neighboring molecules, not within them or between atoms in a covalent bond.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
e90f3449-f93d-4932-b1bc-78cc33eb783d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	6dbb9dd7-71df-4e31-b019-a9d1b4367466	multiple_choice	You have an aqueous solution containing a mixture of bromide (Br⁻) and chloride (Cl⁻) ions. If you wanted to selectively displace *only* the bromide ions from the solution, which free halogen would you use?	{"p_g": 0.25, "p_s": 0.1, "options": ["Fluorine (F₂)", "Chlorine (Cl₂)", "Iodine (I₂)", "No single halogen can achieve this selectively."], "explanation": "According to the activity series (F > Cl > Br > I), Chlorine (Cl₂) is more reactive than bromide (Br⁻) but not chloride (Cl⁻). Therefore, Cl₂ would displace Br⁻ to form Br₂, but it would not react with the Cl⁻ ions already present, effectively achieving selective displacement of only bromide.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
f3726a72-f801-4006-aa57-55f027417df8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9dd1e4cc-b2bd-4420-9972-b3ee50ffee01	multiple_choice	Which group of the periodic table do halogens belong to?	{"p_g": 0.25, "p_s": 0.1, "options": ["Group 1", "Group 17", "Group 2", "Group 18"], "explanation": "Halogens are specifically defined as the elements found in Group 17 of the periodic table.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
b0dddcb7-e65f-4da9-9c64-e9ecd33d2003	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9dd1e4cc-b2bd-4420-9972-b3ee50ffee01	multiple_choice	What is a characteristic property of halogens?	{"p_g": 0.25, "p_s": 0.1, "options": ["They are typically shiny and good conductors of electricity.", "They are highly reactive non-metals.", "They are inert gases.", "They are metalloids with properties of both metals and non-metals."], "explanation": "The node description states that halogens are 'highly reactive non-metals' and 'form salts with metals'. Highly reactive is a key characteristic.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
8498edb2-1c78-45da-9aa7-31fac53913a5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9dd1e4cc-b2bd-4420-9972-b3ee50ffee01	multiple_choice	Why do halogens readily form salts with metals?	{"p_g": 0.25, "p_s": 0.1, "options": ["Halogens are good electrical conductors and metals are insulators.", "Halogens have a strong tendency to gain an electron, while metals tend to lose electrons.", "Both halogens and metals are noble gases and do not react.", "Halogens are very large atoms that easily share electrons with metals."], "explanation": "Halogens are highly reactive non-metals that need to gain one electron to achieve a stable electron configuration (like a noble gas). Metals tend to lose electrons, making them ideal partners for ionic bond formation, leading to salts.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
6b71ff7b-f8c5-4bc7-b549-e14fff7d677c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7e801f3f-b8d3-40f9-b251-8b43637ea597	multiple_choice	Which of the following describes a heterogeneous mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["Its components are uniformly distributed.", "Its components are clearly visible and separated.", "It has a single phase throughout.", "It is impossible to separate its components."], "explanation": "In a heterogeneous mixture, the different components are not uniformly distributed and can often be seen separately.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
8bf4cf93-a10c-4112-bd1a-26b718ed6341	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7e801f3f-b8d3-40f9-b251-8b43637ea597	multiple_choice	Which of the following is the best example of a heterogeneous mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["Salt dissolved in water", "Air", "Oil and vinegar salad dressing", "Bronze alloy"], "explanation": "Salad dressing, especially oil and vinegar, separates into distinct layers, making it a classic example of a heterogeneous mixture.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
db5739ca-7c64-441d-8f9a-6222620d618b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7e801f3f-b8d3-40f9-b251-8b43637ea597	multiple_choice	A chemist observes a sample that contains solid particles suspended in a liquid, and these particles eventually settle to the bottom. This observation is characteristic of which type of mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["Homogeneous solution", "Pure compound", "Colloid", "Heterogeneous mixture"], "explanation": "The settling of solid particles in a liquid indicates that the components are not uniformly distributed and can separate over time, which is a defining feature of a heterogeneous mixture (specifically, a suspension).", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
56587498-3bfb-41ec-9bc2-4bf5416af1f2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c45425f5-4e5f-4a00-b22d-f4b4f75ffb2a	multiple_choice	Which of the following is an example of a homogeneous mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sand and water", "Oil and water", "Saltwater", "A salad"], "explanation": "Saltwater is a classic example of a homogeneous mixture (a solution) because the salt dissolves completely and is uniformly distributed throughout the water, making it appear as a single substance.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
05150379-c02b-4db8-95cd-2c3839c7a986	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c45425f5-4e5f-4a00-b22d-f4b4f75ffb2a	multiple_choice	What is a key characteristic of a homogeneous mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["Its components can be easily separated by filtration.", "Its components remain visibly distinct.", "It has a uniform composition throughout.", "It always consists of only two components."], "explanation": "In a homogeneous mixture, the components are uniformly distributed at a molecular level, meaning any sample taken from the mixture will have the same composition and properties.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
562d3e33-ffd6-4155-800f-147d91c58764	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c45425f5-4e5f-4a00-b22d-f4b4f75ffb2a	multiple_choice	Why is air considered a homogeneous mixture?	{"p_g": 0.25, "p_s": 0.1, "options": ["It is made up of only one type of element.", "Its components can be seen separately under a microscope.", "The different gases are uniformly distributed and indistinguishable.", "It can be easily separated into its individual components by simple physical means."], "explanation": "Air is a mixture of several gases (primarily nitrogen, oxygen, argon, etc.) that are thoroughly mixed and evenly distributed, making it impossible to distinguish individual gases with the naked eye. This uniform composition makes it homogeneous.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
b3159900-ed78-4dc7-b3db-11da5562e935	c18d6d95-77ed-4b41-a833-dc5cddec74f4	039329d6-e56a-4e5e-af23-7779df97f7b6	multiple_choice	Which gas is commonly produced during incomplete combustion, in addition to water?	{"p_g": 0.25, "p_s": 0.1, "options": ["Carbon monoxide", "Carbon dioxide", "Oxygen", "Hydrogen"], "explanation": "Incomplete combustion occurs when there isn't enough oxygen, leading to the formation of carbon monoxide (CO) instead of carbon dioxide (CO2).", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
faede68b-e9a4-4027-885f-7e3b25125201	c18d6d95-77ed-4b41-a833-dc5cddec74f4	039329d6-e56a-4e5e-af23-7779df97f7b6	multiple_choice	What is the main condition that leads to incomplete combustion?	{"p_g": 0.25, "p_s": 0.1, "options": ["Insufficient oxygen supply", "Excessive fuel", "Very low temperature", "Presence of a catalyst"], "explanation": "The defining characteristic of incomplete combustion is the lack of sufficient oxygen for the fuel to burn completely.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
f98fe1d3-6e88-4efb-954d-75dabdad317d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	af9c8a49-54be-414c-b2d7-b6c1eebbfd86	multiple_choice	What are the standard units for molar mass?	{"p_g": 0.25, "p_s": 0.1, "options": ["g/mol", "mol/g", "grams", "moles"], "explanation": "Molar mass represents the mass per mole of a substance, hence its units are grams per mole (g/mol).", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
dfd4dd2a-cfb3-47ef-ad36-fbc38425ea6d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	46660a32-049e-4e5f-ab06-83a887567478	multiple_choice	Which of the following properties is most directly influenced by the strength of intermolecular forces?	{"p_g": 0.25, "p_s": 0.1, "options": ["Bond length", "Boiling point", "Atomic radius", "pH value"], "explanation": "Stronger intermolecular forces require more energy to overcome, leading to higher boiling and melting points. Bond length and atomic radius are related to intramolecular forces or atomic structure, and pH is related to acidity/basicity.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
009a8571-75a2-4d5b-99ec-537c8ae4d475	c18d6d95-77ed-4b41-a833-dc5cddec74f4	46660a32-049e-4e5f-ab06-83a887567478	multiple_choice	Consider three substances: Methane (CH₄), Ammonia (NH₃), and Water (H₂O). Which substance would you expect to have the highest boiling point, and why?	{"p_g": 0.25, "p_s": 0.1, "options": ["Methane, because it has the smallest molecular mass.", "Ammonia, because it has a polar covalent bond.", "Water, because it forms extensive hydrogen bonds.", "All three would have similar boiling points as they are all small molecules."], "explanation": "Water (H₂O) has the strongest intermolecular forces because it can form extensive hydrogen bonds, which are stronger than the dipole-dipole forces in ammonia (NH₃) and the London dispersion forces in methane (CH₄). Ammonia also forms hydrogen bonds, but they are generally weaker than those in water due to less electronegative nitrogen and fewer lone pairs capable of accepting H-bonds. Methane only exhibits weak London dispersion forces.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
dabc2d25-5919-4a15-8872-115fb282f472	c18d6d95-77ed-4b41-a833-dc5cddec74f4	005f56c9-d24d-45ec-b59b-ab4415c71814	multiple_choice	Which of the following is the SI base unit for length?	{"p_g": 0.25, "p_s": 0.1, "options": ["Kilogram", "Metre", "Second", "Litre"], "explanation": "The metre (m) is the fundamental unit of length in the International System of Units.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
e2fe8d3d-e17d-4278-b441-8c9ca2e8c422	c18d6d95-77ed-4b41-a833-dc5cddec74f4	005f56c9-d24d-45ec-b59b-ab4415c71814	multiple_choice	Which of these is NOT an SI base unit?	{"p_g": 0.25, "p_s": 0.1, "options": ["Ampere", "Kelvin", "Newton", "Candela"], "explanation": "The Newton (N) is a derived unit (kg·m/s²) for force, not a base unit. The base units listed are Ampere (electric current), Kelvin (temperature), and Candela (luminous intensity).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
119d6a60-7e75-46e2-921e-ce32a331b2af	c18d6d95-77ed-4b41-a833-dc5cddec74f4	005f56c9-d24d-45ec-b59b-ab4415c71814	multiple_choice	Why is a standardized system like SI crucial for scientific research and international collaboration?	{"p_g": 0.25, "p_s": 0.1, "options": ["It makes calculations more complex.", "It allows for easier conversion to imperial units.", "It ensures consistency and universal understanding of measurements.", "It is preferred by a specific country's scientific community."], "explanation": "A standardized system ensures that measurements are consistent and universally understood, preventing misinterpretations and facilitating accurate data sharing and collaboration across different regions and disciplines.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
1ffd8d11-fc23-409c-b18a-bf1ed1f479bd	c18d6d95-77ed-4b41-a833-dc5cddec74f4	f961bf35-afc8-4dce-876a-7e6f14108e29	multiple_choice	Which of the following is an example of an intramolecular force?	{"p_g": 0.25, "p_s": 0.1, "options": ["Hydrogen bond", "London dispersion force", "Covalent bond", "Dipole-dipole interaction"], "explanation": "Covalent bonds are the forces that hold atoms together within a molecule, which is the definition of an intramolecular force.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
99963918-c860-417e-95f9-c08be8fa9004	c18d6d95-77ed-4b41-a833-dc5cddec74f4	f961bf35-afc8-4dce-876a-7e6f14108e29	multiple_choice	What is the primary role of intramolecular forces within a molecule?	{"p_g": 0.25, "p_s": 0.1, "options": ["To determine the boiling point of a substance", "To hold atoms together within a molecule", "To attract different molecules to each other", "To allow molecules to dissolve in water"], "explanation": "Intramolecular forces, such as covalent bonds, are responsible for holding the individual atoms together to form a stable molecule.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
159d80c4-8714-44f1-a9bc-8103cd8ed37f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	f961bf35-afc8-4dce-876a-7e6f14108e29	multiple_choice	Which statement best describes the relative strength of intramolecular forces compared to intermolecular forces?	{"p_g": 0.25, "p_s": 0.1, "options": ["Intramolecular forces are generally much weaker than intermolecular forces.", "Intramolecular forces are generally much stronger than intermolecular forces.", "Intramolecular forces and intermolecular forces are typically of similar strength.", "The strength comparison depends entirely on the specific molecule and cannot be generalized."], "explanation": "Intramolecular forces (like covalent bonds) are much stronger than intermolecular forces. Breaking intramolecular bonds typically requires chemical reactions and significantly more energy than overcoming intermolecular forces (which is what happens during phase changes like boiling or melting).", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
245d9ffc-234b-43fb-a1df-5f66a74492c8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	19667dda-e18c-4392-82d2-b3d3d43f086b	multiple_choice	What is an ion?	{"p_g": 0.25, "p_s": 0.1, "options": ["A neutral atom with an equal number of protons and electrons.", "A charged particle formed by gaining or losing electrons.", "A particle with no protons or electrons.", "A molecule that has undergone nuclear fission."], "explanation": "An ion is defined as a charged particle, which is formed when a neutral atom or molecule either gains or loses electrons.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
83df2cf5-62dc-42dd-8c4f-ba2dc6c2ccdf	c18d6d95-77ed-4b41-a833-dc5cddec74f4	19667dda-e18c-4392-82d2-b3d3d43f086b	multiple_choice	What type of ion is formed when a neutral atom *loses* one or more electrons?	{"p_g": 0.25, "p_s": 0.1, "options": ["An anion (negatively charged ion).", "A neutral atom.", "A cation (positively charged ion).", "An isotope."], "explanation": "When a neutral atom loses negatively charged electrons, it will have more protons than electrons, resulting in a net positive charge. This positively charged ion is called a cation.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
358ecd7b-e5f1-409a-9027-78ada920b922	c18d6d95-77ed-4b41-a833-dc5cddec74f4	19667dda-e18c-4392-82d2-b3d3d43f086b	multiple_choice	Which of the following statements about ions is true?	{"p_g": 0.25, "p_s": 0.1, "options": ["Ions always have an equal number of protons and electrons.", "The formation of an ion involves a change in the number of protons.", "An atom that gains electrons becomes a negatively charged ion.", "All ions are radioactive."], "explanation": "Ions are formed when the number of electrons changes, leading to a net positive or negative charge. The number of protons (determining the element) and neutrons (determining the isotope) typically remains constant during ion formation.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f5bf4c06-8d53-469b-a7da-2aac4e95bb32	c18d6d95-77ed-4b41-a833-dc5cddec74f4	be5e4256-5c61-4b43-ace6-2cdef9cd4a17	multiple_choice	What is the fundamental process involved in the formation of an ionic bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sharing of electrons", "Transfer of electrons", "Overlapping of orbitals", "Formation of a sea of electrons"], "explanation": "Ionic bonds are formed when one atom donates electrons to another, resulting in the formation of oppositely charged ions that attract each other.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
6d2fb644-54df-4bb4-ac02-8cad879c0fb9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	be5e4256-5c61-4b43-ace6-2cdef9cd4a17	multiple_choice	Which combination of elements is most likely to form an ionic bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["Two non-metals", "Two metals", "A metal and a non-metal", "Noble gas and a metal"], "explanation": "Ionic bonds typically form between a metal, which tends to lose electrons, and a non-metal, which tends to gain electrons, to achieve stable electron configurations.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
4042c366-122e-413b-9635-f11e215ddd43	c18d6d95-77ed-4b41-a833-dc5cddec74f4	be5e4256-5c61-4b43-ace6-2cdef9cd4a17	multiple_choice	What is the primary driving force for atoms to form ionic bonds?	{"p_g": 0.25, "p_s": 0.1, "options": ["To achieve a higher energy state", "To increase their atomic radius", "To attain a stable electron configuration, typically an octet", "To become electrically neutral as individual atoms"], "explanation": "Atoms form ionic bonds to achieve a more stable electron configuration, often a full outer shell (like the noble gases), by either losing or gaining electrons to become ions. The resulting electrostatic attraction between these oppositely charged ions forms the bond.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
58cfbb70-f344-40ff-8cdd-f44453f023d6	c18d6d95-77ed-4b41-a833-dc5cddec74f4	23566452-7649-4002-be86-4be63211aa0f	multiple_choice	Ionic compounds are typically formed between which types of elements?	{"p_g": 0.25, "p_s": 0.1, "options": ["Two non-metals", "Two metals", "A metal and a non-metal", "A metalloid and a non-metal"], "explanation": "Ionic bonds form when electrons are transferred from a metal atom to a non-metal atom, resulting in oppositely charged ions that attract each other.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
005c2a65-35ca-4ef3-a4ec-9cd2ffacfcf0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	23566452-7649-4002-be86-4be63211aa0f	multiple_choice	Which of the following is a characteristic property of most ionic compounds?	{"p_g": 0.25, "p_s": 0.1, "options": ["Low melting point", "Poor electrical conductivity in all states", "High melting point", "Exist as discrete molecules"], "explanation": "Ionic compounds have strong electrostatic forces between ions, requiring a large amount of energy to overcome, leading to high melting and boiling points.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
da2ec2bb-5f4f-4fa8-8b33-98af5419b037	c18d6d95-77ed-4b41-a833-dc5cddec74f4	23566452-7649-4002-be86-4be63211aa0f	multiple_choice	Why do ionic compounds typically conduct electricity when molten or dissolved in water, but not in their solid state?	{"p_g": 0.25, "p_s": 0.1, "options": ["They form free electrons in the molten state.", "The covalent bonds within the compound break down.", "The ions become mobile and are free to move.", "Metallic bonds are formed upon melting."], "explanation": "In the solid state, ions in an ionic compound are held in a rigid lattice structure and are not free to move, hence they cannot conduct electricity. When molten or dissolved, the lattice breaks down, and the ions become mobile, allowing them to carry charge and conduct electricity.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
98acaf27-a1f6-40bd-9f18-35dc6654caee	c18d6d95-77ed-4b41-a833-dc5cddec74f4	48be6756-72b9-4c9f-8608-3cbadf84891f	multiple_choice	What does ionization energy measure?	{"p_g": 0.25, "p_s": 0.1, "options": ["The energy released when an electron is added to an atom.", "The energy required to remove an electron from a neutral atom.", "The energy required to break a chemical bond.", "The energy an atom emits when it loses an electron."], "explanation": "Ionization energy is specifically defined as the energy required to remove an electron from a neutral atom in its gaseous state.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
3ab55947-e005-4a2e-a74e-51e3366c3598	c18d6d95-77ed-4b41-a833-dc5cddec74f4	48be6756-72b9-4c9f-8608-3cbadf84891f	multiple_choice	Which of the following elements would generally have the highest first ionization energy?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sodium (Na)", "Magnesium (Mg)", "Aluminum (Al)", "Neon (Ne)"], "explanation": "Across a period, ionization energy generally increases due to an increase in effective nuclear charge and a decrease in atomic radius, making it harder to remove an electron. Neon is a noble gas with a full valence shell, making it very stable and requiring a large amount of energy to remove an electron.", "correct_answer": 3}	medium	\N	2025-11-24 08:08:04.009802+00
919107b8-0a39-4a74-b240-a63b416b1026	c18d6d95-77ed-4b41-a833-dc5cddec74f4	48be6756-72b9-4c9f-8608-3cbadf84891f	multiple_choice	Why is the second ionization energy of an atom always greater than its first ionization energy?	{"p_g": 0.25, "p_s": 0.1, "options": ["The second electron is always removed from an inner shell.", "The atom becomes smaller after losing the first electron, increasing electron-electron repulsion.", "The resulting ion has a net positive charge, increasing the electrostatic attraction for the remaining electrons.", "The second electron is always in a higher energy level."], "explanation": "After the first electron is removed, the atom becomes a positively charged ion. It takes more energy to remove an electron from a positively charged ion because the remaining electrons are held more tightly by the increased effective nuclear charge.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
264a01f4-23aa-4792-a023-6a1b4bb8918e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8d1ed2d9-9781-4482-ab7e-5656d9662652	multiple_choice	What is the primary difference between isotopes of the same element?	{"p_g": 0.25, "p_s": 0.1, "options": ["Number of protons", "Number of electrons", "Number of neutrons", "Atomic number"], "explanation": "Isotopes are defined by having the same number of protons (and thus being the same element) but a different number of neutrons, which leads to different mass numbers.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
372d0c5d-581f-4bdf-baaa-72d4cd4463ef	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8d1ed2d9-9781-4482-ab7e-5656d9662652	multiple_choice	Which statement accurately describes isotopes?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have different atomic numbers.", "They have the same mass number.", "They have different chemical properties.", "They have the same number of protons."], "explanation": "By definition, isotopes are atoms of the same element, meaning they must have the same number of protons. Their difference lies in the number of neutrons, which affects their mass number but not their fundamental identity as an element.", "correct_answer": 3}	medium	\N	2025-11-24 08:08:04.009802+00
5a8f6678-4e59-4bca-a2a3-22c996bd642d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8d1ed2d9-9781-4482-ab7e-5656d9662652	multiple_choice	Atom A has 17 protons and 18 neutrons. Atom B has 17 protons and 20 neutrons. What is the relationship between Atom A and Atom B?	{"p_g": 0.25, "p_s": 0.1, "options": ["They are different elements.", "They are ions of the same element.", "They are isotopes of the same element.", "They have the same mass number."], "explanation": "Both Atom A and Atom B have 17 protons, which means they are atoms of the same element (Chlorine, since atomic number 17). However, they have different numbers of neutrons (18 vs. 20), making them isotopes of that element.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
323b8968-0336-4ef1-b42f-428415930fe0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0f667c1-6299-4428-9c05-d7640cc34fc4	multiple_choice	What does isotopic abundance primarily describe?	{"p_g": 0.25, "p_s": 0.1, "options": ["The total number of isotopes an element can have.", "The relative amount of each isotope present in a naturally occurring sample.", "The atomic mass of a single, specific isotope.", "The stability of a particular isotope."], "explanation": "Isotopic abundance refers to the relative proportion of each isotope of an element found in a natural sample.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
ca1bf0cc-924a-4d11-ab06-3a13688c184d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0f667c1-6299-4428-9c05-d7640cc34fc4	multiple_choice	An element has two isotopes: Isotope A with a mass of 20 amu and Isotope B with a mass of 22 amu. If the average atomic mass of the element is 20.4 amu, which isotope is more abundant?	{"p_g": 0.25, "p_s": 0.1, "options": ["Isotope A", "Isotope B", "Both isotopes are equally abundant.", "The abundance cannot be determined from this information."], "explanation": "The average atomic mass is closer to the mass of the more abundant isotope. Since 20.4 amu is closer to 20 amu (Isotope A) than to 22 amu (Isotope B), Isotope A must be more abundant.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
87bf35b2-781d-4745-9c81-06e6509f5cc9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0f667c1-6299-4428-9c05-d7640cc34fc4	multiple_choice	Element Z has two stable isotopes: Z-63 (mass 62.930 amu) and Z-65 (mass 64.928 amu). If the average atomic mass of Element Z is 63.546 amu, what can be inferred about the isotopic abundance?	{"p_g": 0.25, "p_s": 0.1, "options": ["Z-65 is significantly more abundant than Z-63.", "Z-63 and Z-65 are present in roughly equal amounts.", "Z-63 is significantly more abundant than Z-65.", "The abundance of Z-63 is exactly 50%."], "explanation": "The average atomic mass (63.546 amu) is closer to the mass of Z-63 (62.930 amu) than to Z-65 (64.928 amu). This indicates that Z-63 is more abundant than Z-65. To be precise, (63.546 - 62.930) = 0.616 and (64.928 - 63.546) = 1.382, showing it's significantly closer to Z-63.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
d3fc113c-cf2a-440a-8dbe-205df78e6365	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d133a2ea-5af9-4d34-a757-1906c33a5914	multiple_choice	In a chemical reaction, how does the total mass of the reactants compare to the total mass of the products?	{"p_g": 0.25, "p_s": 0.1, "options": ["The mass of reactants is greater than the mass of products.", "The mass of products is greater than the mass of reactants.", "The mass of reactants equals the mass of products.", "There is no relationship between the mass of reactants and products."], "explanation": "The Law of Conservation of Mass states that mass is neither created nor destroyed in a chemical reaction, so the total mass remains constant.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
5188d644-f864-4e39-97c3-b89af6d0d07f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d133a2ea-5af9-4d34-a757-1906c33a5914	multiple_choice	If 10 grams of hydrogen gas react completely with 80 grams of oxygen gas to form water, what is the total mass of the water produced?	{"p_g": 0.25, "p_s": 0.1, "options": ["10 grams", "80 grams", "90 grams", "70 grams"], "explanation": "According to the Law of Conservation of Mass, the total mass of the reactants must equal the total mass of the products. So, 10 g (hydrogen) + 80 g (oxygen) = 90 g (water).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
94ab7e44-4745-4f55-90c6-bf1c1cfad2af	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d133a2ea-5af9-4d34-a757-1906c33a5914	multiple_choice	A student performs an experiment where a solid reactant is heated in an open crucible, and the mass decreases. Which of the following best explains this observation in the context of the Law of Conservation of Mass?	{"p_g": 0.25, "p_s": 0.1, "options": ["Mass was destroyed during the heating process.", "The Law of Conservation of Mass does not apply to reactions involving heat.", "A gaseous product was formed and escaped into the atmosphere.", "The solid reactant simply converted into energy."], "explanation": "The Law of Conservation of Mass still holds; the decrease in mass indicates that a gaseous product escaped into the atmosphere. If the crucible were sealed, the total mass would remain constant.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
b88da04a-fb0f-4022-8a76-90d04c22cd0a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9afb1f1f-9d45-423d-b331-f0de28ad9498	multiple_choice	What does the Law of Definite Proportion state about the composition of a pure chemical compound?	{"p_g": 0.25, "p_s": 0.1, "options": ["Elements combine in variable proportions by mass.", "Elements always combine in fixed proportions by mass.", "The total mass of reactants equals the total mass of products.", "Energy is always conserved in a chemical reaction."], "explanation": "The Law of Definite Proportion, also known as Proust's Law, states that a given chemical compound always contains its component elements in fixed ratios by mass, regardless of the source or method of preparation.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
a792fbdf-403c-4f51-b111-1075ae147c33	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9afb1f1f-9d45-423d-b331-f0de28ad9498	multiple_choice	If you analyze two different samples of pure table salt (sodium chloride, NaCl), what would the Law of Definite Proportion predict about their composition?	{"p_g": 0.25, "p_s": 0.1, "options": ["The ratio of sodium to chlorine by mass will vary between the two samples.", "The mass of sodium will always be equal to the mass of chlorine in both samples.", "The ratio of sodium to chlorine by mass will be identical for both samples.", "One sample will contain more atoms than the other."], "explanation": "According to the Law of Definite Proportion, any pure sample of a specific compound will always have the same proportion of its constituent elements by mass. For NaCl, the ratio of sodium to chlorine by mass will always be fixed.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
9ed0dd72-9480-4763-bf01-a8f4f7d5b466	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9afb1f1f-9d45-423d-b331-f0de28ad9498	multiple_choice	Consider a compound formed from elements A and B. If a 100g sample of this compound always contains 20g of A and 80g of B, which of the following statements is a direct implication of the Law of Definite Proportion?	{"p_g": 0.25, "p_s": 0.1, "options": ["Elements A and B can combine in other mass ratios to form different compounds.", "If a 50g sample of the same compound is analyzed, it will contain 10g of A and 40g of B.", "The atomic mass of element A is four times greater than that of element B.", "The total mass of reactants used to form the compound must always be 100g."], "explanation": "The Law of Definite Proportion asserts that the elemental composition by mass of a pure compound is always the same, regardless of how it was prepared or where it came from. Therefore, any pure sample of this specific compound will maintain the 20g A to 80g B ratio (or 1:4 ratio) by mass.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
268d62c3-0d5b-4b0d-a7e5-e88e16e9305a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3f5120d-f32c-4b94-8eae-5c540039b78a	multiple_choice	What do the dots in a Lewis structure primarily represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["Valence electrons", "Protons", "Neutrons", "Core electrons"], "explanation": "Lewis structures use dots to show the valence electrons, which are the electrons in the outermost shell and are involved in chemical bonding.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
c856d1b8-ab29-462c-a48b-d108704a5870	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3f5120d-f32c-4b94-8eae-5c540039b78a	multiple_choice	How many lone pairs of electrons are typically found on the central oxygen atom in the Lewis structure of a water molecule (H₂O)?	{"p_g": 0.25, "p_s": 0.1, "options": ["0", "1", "2", "3"], "explanation": "Oxygen has 6 valence electrons. In H₂O, it forms two single bonds with hydrogen atoms (using 2 electrons), leaving 4 electrons as two lone pairs.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
d266da8a-ec74-4828-9175-0afac78d9c0a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0f5eed39-eded-4ab6-910e-c4c4aef03147	multiple_choice	Which group of elements on the periodic table is known as the Noble Gases?	{"p_g": 0.25, "p_s": 0.1, "options": ["Group 1", "Group 2", "Group 17", "Group 18"], "explanation": "Noble Gases are found in Group 18 of the periodic table.", "correct_answer": 3}	easy	\N	2025-11-24 08:08:04.009802+00
7ca6818f-195c-4137-b2bb-0dba7b468459	c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3f5120d-f32c-4b94-8eae-5c540039b78a	multiple_choice	Which of the following elements is known to commonly form Lewis structures where it expands its octet?	{"p_g": 0.25, "p_s": 0.1, "options": ["Carbon", "Nitrogen", "Oxygen", "Sulfur"], "explanation": "Elements in Period 3 and beyond (like Sulfur) have available d orbitals, allowing them to accommodate more than eight valence electrons, thus expanding their octet.", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
c78db7cf-614d-49d1-acea-97efbd0c37fe	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ed556f7c-4ef2-4390-b3de-b9c185a0b7f1	multiple_choice	What do the dots in a Lewis structure primarily represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["Protons", "Neutrons", "Core electrons", "Valence electrons"], "explanation": "In a Lewis structure, dots are used to represent the valence electrons of an atom, which are the electrons involved in bonding.", "correct_answer": 3}	easy	\N	2025-11-24 08:08:04.009802+00
7343cb19-f4ba-4ee6-8439-485bb833251a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ed556f7c-4ef2-4390-b3de-b9c185a0b7f1	multiple_choice	How many valence electrons does a carbon atom typically form bonds with to achieve a stable octet in a neutral molecule?	{"p_g": 0.25, "p_s": 0.1, "options": ["2", "4", "6", "8"], "explanation": "Carbon is in group 14 and has 4 valence electrons. To achieve a stable octet (8 electrons), it typically forms 4 covalent bonds.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
7ca5f211-c094-4f6f-b0b1-f19368107f8f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ed556f7c-4ef2-4390-b3de-b9c185a0b7f1	multiple_choice	Which of the following molecules contains an atom that can expand its octet?	{"p_g": 0.25, "p_s": 0.1, "options": ["CO2", "H2O", "SF6", "NCl3"], "explanation": "Sulfur (S) is in period 3 of the periodic table, meaning it has access to d-orbitals and can accommodate more than 8 valence electrons, as seen in molecules like SF6. Carbon, Oxygen, and Nitrogen typically obey the octet rule.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
0cd3cfa6-10b1-495a-bbd5-8cef9326051e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9f50dba5-bdc5-406b-98b6-b2b336e3d05b	multiple_choice	What does the mass number (A) of an atom represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["The total number of protons and neutrons", "The number of protons only", "The number of electrons only", "The number of neutrons only"], "explanation": "The mass number is defined as the sum of protons and neutrons in the nucleus.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
d45f1fe2-881b-41ac-b37d-e2ef696d8dd7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9f50dba5-bdc5-406b-98b6-b2b336e3d05b	multiple_choice	An atom has 8 protons and 9 neutrons. What is its mass number?	{"p_g": 0.25, "p_s": 0.1, "options": ["17", "8", "9", "1"], "explanation": "The mass number (A) is the sum of protons and neutrons. So, 8 protons + 9 neutrons = 17.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
b3906318-6059-4d12-9c20-6397a42422c6	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9f50dba5-bdc5-406b-98b6-b2b336e3d05b	multiple_choice	Two isotopes of an element have the same number of protons but different mass numbers. Which atomic component differs between these two isotopes?	{"p_g": 0.25, "p_s": 0.1, "options": ["Number of neutrons", "Number of protons", "Number of electrons", "Atomic number"], "explanation": "Isotopes are atoms of the same element (same number of protons) but with different numbers of neutrons. Since the mass number is protons + neutrons, a different mass number implies a different number of neutrons.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
e81d170b-1a02-4e8a-9507-ce365f505b6a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	513b8f18-4b0c-4c7a-8c84-dd2dd5ffcac4	multiple_choice	What fundamental property of ions does a mass spectrometer primarily measure?	{"p_g": 0.25, "p_s": 0.1, "options": ["Temperature", "Velocity", "Mass-to-charge ratio", "Density"], "explanation": "The core function of a mass spectrometer, as described, is to measure the mass-to-charge ratio of ions.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
b8e65b49-138e-4865-bc20-8aa8aac967da	c18d6d95-77ed-4b41-a833-dc5cddec74f4	513b8f18-4b0c-4c7a-8c84-dd2dd5ffcac4	multiple_choice	Which of the following is a key application of a mass spectrometer?	{"p_g": 0.25, "p_s": 0.1, "options": ["Measuring the pH of a solution", "Determining the relative abundance of isotopes", "Analyzing the color spectrum of light", "Calculating the boiling point of a compound"], "explanation": "Mass spectrometry is widely used to determine the relative abundance of different isotopes within a sample, providing insights into elemental composition.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
9794f57b-4aa3-4ac3-973f-a74ea8c9a015	c18d6d95-77ed-4b41-a833-dc5cddec74f4	513b8f18-4b0c-4c7a-8c84-dd2dd5ffcac4	multiple_choice	Consider two singly-charged ions, Ion A (mass = 20 amu) and Ion B (mass = 40 amu), entering the magnetic deflection chamber of a mass spectrometer with the same kinetic energy. Which ion will experience greater deflection?	{"p_g": 0.25, "p_s": 0.1, "options": ["Ion A (mass 20 amu)", "Ion B (mass 40 amu)", "Both ions will be deflected equally", "Neither ion will be deflected"], "explanation": "For ions with the same charge and kinetic energy in a magnetic field, the radius of their path is proportional to the square root of their mass (r ∝ √m). A smaller radius means greater deflection. Therefore, the lighter ion (Ion A) will have a smaller radius of curvature and be deflected more significantly than the heavier ion (Ion B).", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
768d70f0-c2b9-4dc4-99c5-5d9d2e610906	c18d6d95-77ed-4b41-a833-dc5cddec74f4	28c26e6c-ea10-4e55-b961-897e6113674f	multiple_choice	What is the primary purpose of the Metal Activity Series?	{"p_g": 0.25, "p_s": 0.1, "options": ["To classify metals by their color", "To determine the density of metals", "To predict the outcome of single displacement reactions", "To measure the melting points of metals"], "explanation": "The Metal Activity Series ranks metals based on their reactivity, which helps predict whether one metal can displace another in a chemical reaction.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
71a1d395-b087-41bf-a177-7aed5f384da8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	28c26e6c-ea10-4e55-b961-897e6113674f	multiple_choice	Given the activity series: K > Na > Ca > Mg > Al > Zn > Fe > Pb > H > Cu > Ag. Which of the following reactions would occur spontaneously?	{"p_g": 0.25, "p_s": 0.1, "options": ["Cu(s) + ZnSO₄(aq) →", "Ag(s) + CuSO₄(aq) →", "Zn(s) + CuSO₄(aq) →", "Pb(s) + MgSO₄(aq) →"], "explanation": "A more reactive metal (higher in the series) can displace a less reactive metal (lower in the series) from its compound. Zinc is more reactive than copper, so it can displace copper from copper sulfate.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
611950cc-c12d-4a27-9315-792b064fb4d8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	28c26e6c-ea10-4e55-b961-897e6113674f	multiple_choice	Consider three unknown metals P, Q, and R. Metal P can displace metal Q from its salt solution, but metal R cannot displace metal Q. Which of the following represents the correct order of reactivity from most reactive to least reactive?	{"p_g": 0.25, "p_s": 0.1, "options": ["P > Q > R", "R > Q > P", "Q > P > R", "P > R > Q"], "explanation": "If P can displace Q, then P is more reactive than Q (P > Q). If R cannot displace Q, then Q is more reactive than R (Q > R). Combining these, the order is P > Q > R.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
5bf66bfa-4a3c-4ec8-9e12-d7ffc332de8f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2802bcc-4594-4f29-ac85-6f4543e1ed29	multiple_choice	What type of particles are responsible for conducting electricity in a metallic bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["Positively charged metal ions", "Conduction electrons", "Neutral metal atoms", "Anions"], "explanation": "Metallic bonding involves a 'sea' of delocalized electrons, known as conduction electrons, which are free to move and carry charge.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
840e7012-3904-4dfa-8a35-4cbee8353bda	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2802bcc-4594-4f29-ac85-6f4543e1ed29	multiple_choice	Which of the following properties of metals is *best* explained by the 'electron sea' model of metallic bonding?	{"p_g": 0.25, "p_s": 0.1, "options": ["High melting points", "Brittleness", "Good electrical conductivity", "Low density"], "explanation": "The delocalized nature of conduction electrons allows them to easily move throughout the metal structure, making metals excellent conductors of heat and electricity.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
423e80e8-fb10-4573-98af-bce1f9170082	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2802bcc-4594-4f29-ac85-6f4543e1ed29	multiple_choice	How does the 'electron sea' model explain the malleability and ductility of metals?	{"p_g": 0.25, "p_s": 0.1, "options": ["The strong directional bonds between atoms prevent deformation.", "The fixed positions of electrons create rigid structures.", "The delocalized electrons can re-form bonds around displaced metal ions, preventing repulsion.", "The positive ions repel each other strongly, leading to easy fracturing."], "explanation": "When a force is applied, the metal ions can slide past each other without breaking the overall metallic bond because the electron sea can re-form around the new positions of the ions, preventing strong repulsive forces.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f710dba1-5307-47c9-bb60-bd4cbd44d097	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b8bb0b83-db9d-4852-9fdb-b99615bef4c3	multiple_choice	Where are metalloids typically located on the periodic table?	{"p_g": 0.25, "p_s": 0.1, "options": ["Along the staircase line", "In the first column (Group 1)", "In the last column (Group 18)", "In the bottom two rows (Lanthanides and Actinides)"], "explanation": "Metalloids are found along the diagonal 'staircase line' that separates metals from non-metals.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
85bf90bb-3c2e-4d9e-8e1e-90406d8f016b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b8bb0b83-db9d-4852-9fdb-b99615bef4c3	multiple_choice	Which statement accurately describes a key characteristic of metalloids?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have properties intermediate between metals and non-metals.", "They are all highly reactive gases at room temperature.", "They are excellent conductors of heat and electricity, like all metals.", "They form only ionic bonds with other elements."], "explanation": "Metalloids possess properties that are a mix of both metals (like some conductivity) and non-metals (like brittleness or being semiconductors).", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
8eab345c-7389-4eed-8915-3b1cbb167559	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b8bb0b83-db9d-4852-9fdb-b99615bef4c3	multiple_choice	Silicon is a well-known metalloid. Which of its properties best illustrates its metalloid nature?	{"p_g": 0.25, "p_s": 0.1, "options": ["It acts as a semiconductor, conducting electricity under certain conditions.", "It is a very soft, silvery-white solid that reacts vigorously with water.", "It is a colorless, odorless gas that is unreactive.", "It has a very low melting point and is highly ductile."], "explanation": "Silicon is a semiconductor, meaning its electrical conductivity is intermediate between that of a conductor (metal) and an insulator (non-metal), and can be controlled. This is a defining characteristic of many metalloids.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
8b964e50-341c-476a-a20e-ab6571b8d2fb	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9e6f6e21-867a-4bf8-9b2d-8e80ad2e421c	multiple_choice	Which of the following is a common characteristic of most metals?	{"p_g": 0.25, "p_s": 0.1, "options": ["Dull appearance", "Good electrical conductivity", "Brittle nature", "Low density"], "explanation": "Metals are known for their ability to conduct electricity due to their delocalized electrons.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
d5a97fd2-111a-4351-9861-fdb0f11eb2f5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9e6f6e21-867a-4bf8-9b2d-8e80ad2e421c	multiple_choice	On the periodic table, where are most metallic elements typically located?	{"p_g": 0.25, "p_s": 0.1, "options": ["Exclusively in the far right column", "Only in the top two rows", "On the left side and center, below the staircase line", "Only in the bottom two rows (lanthanides and actinides)"], "explanation": "Metals occupy the left side and the center of the periodic table, generally below the metalloid staircase line.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
7100216f-a129-4faa-88d3-ebaa9d64f1ed	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9e6f6e21-867a-4bf8-9b2d-8e80ad2e421c	multiple_choice	Which statement about the chemical properties of typical metals is generally TRUE?	{"p_g": 0.25, "p_s": 0.1, "options": ["They readily gain electrons to form negative ions.", "They are poor reducing agents.", "They tend to lose electrons and form positive ions.", "They typically form covalent bonds with other metals."], "explanation": "Metals typically have low ionization energies and electronegativity, meaning they tend to lose their valence electrons to form positive ions (cations) in chemical reactions.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
77adaafb-9c9f-4620-8b88-0289ed20fab0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4db95075-7641-463c-b854-5d10ac13a13a	multiple_choice	Which of the following concepts was NOT part of Dalton's original atomic theory but is included in the Modern Atomic Theory?	{"p_g": 0.25, "p_s": 0.1, "options": ["Atoms are indivisible", "Atoms of the same element are identical", "The existence of subatomic particles", "Atoms combine in simple whole-number ratios"], "explanation": "Dalton's theory stated that atoms are indivisible. Modern Atomic Theory recognizes the existence of subatomic particles (protons, neutrons, electrons), which means atoms can be divided.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
6b703875-a89d-46ed-a636-41d3f7097e88	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4db95075-7641-463c-b854-5d10ac13a13a	multiple_choice	According to Modern Atomic Theory, what distinguishes isotopes of the same element?	{"p_g": 0.25, "p_s": 0.1, "options": ["Different number of protons", "Different number of electrons", "Different number of neutrons", "Different atomic number"], "explanation": "Isotopes are atoms of the same element (meaning they have the same number of protons) but differ in their number of neutrons, leading to different mass numbers.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
f1f9507a-a856-4fc2-9c22-aad9d4efbad4	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4db95075-7641-463c-b854-5d10ac13a13a	multiple_choice	Which aspect of Modern Atomic Theory contradicts Dalton's postulate that atoms of one element cannot be changed into atoms of another element?	{"p_g": 0.25, "p_s": 0.1, "options": ["The discovery of electrons", "The existence of isotopes", "The possibility of nuclear reactions", "The law of definite proportions"], "explanation": "Dalton believed atoms were immutable. Modern Atomic Theory, however, includes the concept of nuclear reactions (like fission or fusion), where one element can be transformed into another by changes in the nucleus.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
5f4f90c3-4b27-4a8a-835a-2b1792876d3c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	af9c8a49-54be-414c-b2d7-b6c1eebbfd86	multiple_choice	What is the molar mass of carbon (C)? (Atomic mass of C ≈ 12.01 amu)	{"p_g": 0.25, "p_s": 0.1, "options": ["12.01 g/mol", "6.022 x 10^23 g/mol", "1.00 g/mol", "24.02 g/mol"], "explanation": "The molar mass of an element in g/mol is numerically equal to its average atomic mass in atomic mass units (amu). Therefore, carbon's molar mass is 12.01 g/mol.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
b6abb49e-9f07-4f8b-b1a0-4ece879aa721	c18d6d95-77ed-4b41-a833-dc5cddec74f4	af9c8a49-54be-414c-b2d7-b6c1eebbfd86	multiple_choice	Calculate the molar mass of water (H₂O). (Given atomic masses: H ≈ 1.01 g/mol, O ≈ 16.00 g/mol)	{"p_g": 0.25, "p_s": 0.1, "options": ["18.02 g/mol", "17.01 g/mol", "34.02 g/mol", "18.02 amu"], "explanation": "To find the molar mass of H₂O, sum the molar masses of its constituent atoms: (2 × Molar Mass of H) + (1 × Molar Mass of O) = (2 × 1.01 g/mol) + (1 × 16.00 g/mol) = 2.02 g/mol + 16.00 g/mol = 18.02 g/mol.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
f685410e-f698-4da4-a30a-9cb68a878a1a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	034af9f5-7609-4afe-b55a-22c567b3eeae	multiple_choice	What information is needed to convert moles of a substance to its mass in grams?	{"p_g": 0.25, "p_s": 0.1, "options": ["Molar mass", "Density", "Volume", "Temperature"], "explanation": "To convert moles to mass, you multiply the number of moles by the molar mass (g/mol).", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
d4fd84cf-5958-45b3-94ab-97c3de3b3ae8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	034af9f5-7609-4afe-b55a-22c567b3eeae	multiple_choice	If the molar mass of water (H₂O) is 18.02 g/mol, how many grams are in 3.5 moles of water?	{"p_g": 0.25, "p_s": 0.1, "options": ["63.07 g", "5.15 g", "0.19 g", "18.02 g"], "explanation": "Mass = Moles × Molar Mass. So, 3.5 mol × 18.02 g/mol = 63.07 g.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
f15dbd70-906b-4cfd-aff8-01fb69806cb8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	034af9f5-7609-4afe-b55a-22c567b3eeae	multiple_choice	You have a sample of pure iron (Fe) with a mass of 111.7 g. Given that the molar mass of iron is 55.85 g/mol, how many moles of iron are in the sample?	{"p_g": 0.25, "p_s": 0.1, "options": ["2.00 mol", "0.50 mol", "6241.65 mol", "55.85 mol"], "explanation": "Moles = Mass / Molar Mass. So, 111.7 g / 55.85 g/mol = 2.00 mol.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
f7e67ea9-8c38-420a-90ef-67e9e3ad5b9c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8c405318-6b27-45e9-a672-22db79ea406d	multiple_choice	What is the approximate value of Avogadro's constant?	{"p_g": 0.25, "p_s": 0.1, "options": ["6.022 x 10^23 particles/mol", "6.022 x 10^22 particles/mol", "1.000 x 10^23 particles/mol", "1.000 x 10^24 particles/mol"], "explanation": "Avogadro's constant represents the number of constituent particles (atoms, molecules, ions, etc.) in one mole of a substance.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
c2735f12-b0aa-495f-8f26-1f4e5ec08a73	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8c405318-6b27-45e9-a672-22db79ea406d	multiple_choice	How many atoms are present in 0.5 moles of helium?	{"p_g": 0.25, "p_s": 0.1, "options": ["3.011 x 10^23 atoms", "6.022 x 10^23 atoms", "1.204 x 10^24 atoms", "0.5 atoms"], "explanation": "To find the number of particles, multiply the number of moles by Avogadro's constant (0.5 mol * 6.022 x 10^23 particles/mol = 3.011 x 10^23 particles).", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
1ec3b55e-0427-414b-9887-ed9c2bd7502f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	8c405318-6b27-45e9-a672-22db79ea406d	multiple_choice	A sample contains 1.8066 x 10^24 molecules of water. How many moles of water are in the sample?	{"p_g": 0.25, "p_s": 0.1, "options": ["3.0 moles", "1.5 moles", "0.3 moles", "18 moles"], "explanation": "To find the number of moles, divide the number of particles by Avogadro's constant (1.8066 x 10^24 molecules / 6.022 x 10^23 molecules/mol = 3.0 moles).", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
d9ccaec0-adf1-466d-b4f2-7bd26faa3a10	c18d6d95-77ed-4b41-a833-dc5cddec74f4	fec31188-16ba-4bdb-aa84-7080dc0fd7dc	multiple_choice	What is the primary factor that determines the three-dimensional arrangement of atoms in a molecule?	{"p_g": 0.25, "p_s": 0.1, "options": ["Minimization of electron pair repulsion", "Maximization of bond energy", "Minimization of atomic size", "Maximization of electronegativity difference"], "explanation": "According to VSEPR theory, electron pairs around a central atom will orient themselves to minimize repulsion, thus dictating the molecular shape.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
7675dc4c-2fcd-402b-857e-0ba52c0b1dac	c18d6d95-77ed-4b41-a833-dc5cddec74f4	fec31188-16ba-4bdb-aa84-7080dc0fd7dc	multiple_choice	A molecule has a central atom with four electron domains, two of which are bonding pairs and two are lone pairs. What is its molecular shape?	{"p_g": 0.25, "p_s": 0.1, "options": ["Linear", "Trigonal Planar", "Bent", "Tetrahedral"], "explanation": "Four electron domains lead to a tetrahedral electron geometry. With two bonding pairs and two lone pairs, the molecular geometry is bent (e.g., H2O), as the lone pairs influence the shape but are not part of the 'molecular' geometry itself.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
1c405a13-51cc-47c8-9b81-ca1fdf5ac2a8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	fec31188-16ba-4bdb-aa84-7080dc0fd7dc	multiple_choice	If a central atom has five electron domains, with three bonding pairs and two lone pairs, what is its molecular geometry?	{"p_g": 0.25, "p_s": 0.1, "options": ["Trigonal Bipyramidal", "See-saw", "T-shaped", "Square Planar"], "explanation": "Five electron domains correspond to a trigonal bipyramidal electron geometry. With two lone pairs, they occupy the equatorial positions to minimize repulsion. Removing two equatorial positions from a trigonal bipyramidal structure leaves a T-shaped molecular geometry (e.g., ClF3).", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
8c0ac8d8-a097-4746-b3e4-0d48a2a182fc	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2016da24-385f-4b89-a9fa-7a75fca6895d	multiple_choice	What is the electric charge of a neutron?	{"p_g": 0.25, "p_s": 0.1, "options": ["Positive (+1)", "Negative (-1)", "Zero (0)", "Variable"], "explanation": "Neutrons are defined as neutral subatomic particles, meaning they have no electric charge.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
ac526837-e955-4dd1-b4ef-deb7389ebdda	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2016da24-385f-4b89-a9fa-7a75fca6895d	multiple_choice	Where is a neutron primarily located within an atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["Orbiting the nucleus in shells", "In the electron cloud", "Within the atomic nucleus", "Outside the atom entirely"], "explanation": "Neutrons, along with protons, are found in the dense central part of the atom called the nucleus.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
337d71f6-69c8-48b8-9384-66b3861af380	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2016da24-385f-4b89-a9fa-7a75fca6895d	multiple_choice	Which statement accurately describes the relative mass of a neutron compared to other subatomic particles?	{"p_g": 0.25, "p_s": 0.1, "options": ["It is significantly less massive than an electron.", "It has approximately the same mass as a proton.", "It has no measurable mass.", "It is exactly twice the mass of a proton."], "explanation": "A neutron has a relative mass of approximately 1 atomic mass unit (amu), which is very close to the mass of a proton and significantly greater than the mass of an electron.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
73dc1f02-33b1-4554-a23e-f9cb643c49ac	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0f5eed39-eded-4ab6-910e-c4c4aef03147	multiple_choice	What is the primary reason noble gases are highly unreactive?	{"p_g": 0.25, "p_s": 0.1, "options": ["They are very light elements.", "They have a full outer energy level of electrons.", "They are all gases at room temperature.", "They have a high electronegativity."], "explanation": "Noble gases have a full outer energy level of electrons, making them stable and unwilling to gain or lose electrons to form bonds.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
eb86a9a4-340e-46ee-8498-06bc018a9917	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0f5eed39-eded-4ab6-910e-c4c4aef03147	multiple_choice	Which of the following statements about noble gases is INCORRECT?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have a stable electron configuration.", "They are generally found as monatomic gases.", "They readily form stable compounds with other elements.", "They are used in applications like neon signs and inert atmospheres."], "explanation": "Due to their full outer electron shells, noble gases are highly unreactive and do not readily form stable compounds under normal conditions. While some can form compounds under extreme conditions, it's not a general characteristic.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
a9e6b84b-f4e4-4792-a86a-22a7addc5304	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4504df02-da3f-4db7-b1ba-8328682ef48e	multiple_choice	Which of the following is a general characteristic of non-metals?	{"p_g": 0.25, "p_s": 0.1, "options": ["Good conductors of heat and electricity", "Malleable and ductile", "Brittle and poor conductors", "Lustrous appearance"], "explanation": "Non-metals typically lack the metallic luster, are poor conductors of heat and electricity, and are often brittle in their solid state.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
6a10ccdb-73d2-40da-b732-e23c408ce5a3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4504df02-da3f-4db7-b1ba-8328682ef48e	multiple_choice	Which of these elements is classified as a non-metal?	{"p_g": 0.25, "p_s": 0.1, "options": ["Iron (Fe)", "Copper (Cu)", "Oxygen (O)", "Aluminum (Al)"], "explanation": "Oxygen is found on the right side of the periodic table and exhibits non-metallic properties, such as being a gas at room temperature and a poor conductor.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
ff47ce8e-742c-487d-bac4-3690c4ca13f5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4504df02-da3f-4db7-b1ba-8328682ef48e	multiple_choice	In chemical reactions, how do non-metals typically achieve a stable electron configuration?	{"p_g": 0.25, "p_s": 0.1, "options": ["By losing electrons to form positive ions", "By gaining electrons to form negative ions", "By sharing electrons only, never forming ions", "By losing or gaining protons"], "explanation": "Non-metals have a tendency to gain electrons to fill their outer electron shells, forming negative ions (anions) and achieving a stable octet.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
8ee16186-84eb-4b77-a4ed-15d728db761b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2fb63cbc-a0d0-4925-8992-2128e165abd6	multiple_choice	What part of an atom is primarily involved in a nuclear reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["Electrons", "Protons and neutrons in the nucleus", "Orbitals", "Valence shell"], "explanation": "Nuclear reactions specifically involve changes to the nucleus of an atom, unlike chemical reactions which involve electrons.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
075f75f9-e4fd-44a3-b573-0f800aa4046c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2fb63cbc-a0d0-4925-8992-2128e165abd6	multiple_choice	Which of the following is a characteristic outcome of nuclear reactions that is not typical of chemical reactions?	{"p_g": 0.25, "p_s": 0.1, "options": ["Rearrangement of atoms", "Formation of new compounds", "Conversion of mass into a significant amount of energy", "Changes in electron configuration"], "explanation": "Nuclear reactions involve changes to the atomic nuclei, often resulting in the formation of new elements due to changes in the number of protons. Chemical reactions only rearrange atoms.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
14a1225e-92f9-491c-9cbd-521bc60d9e52	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2fb63cbc-a0d0-4925-8992-2128e165abd6	multiple_choice	The energy released in nuclear reactions, such as those powering stars, is primarily a result of what principle?	{"p_g": 0.25, "p_s": 0.1, "options": ["Conservation of charge", "Conservation of momentum", "Conversion of mass into energy (mass defect)", "Changes in the electron shells"], "explanation": "Nuclear reactions convert a small amount of mass into a very large amount of energy, as described by Einstein's famous equation E=mc². This mass defect is the source of the immense energy.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
db1c9210-0a7f-438a-b6ce-be6e7823f5c8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	5e899e6c-3ab7-49c2-94bc-97128921ca0b	multiple_choice	What is the primary goal for atoms when they follow the octet rule?	{"p_g": 0.25, "p_s": 0.1, "options": ["To increase their atomic number", "To achieve a stable electron configuration with eight valence electrons", "To become radioactive", "To decrease their reactivity significantly"], "explanation": "The octet rule describes the tendency of atoms to gain, lose, or share electrons in order to achieve a stable configuration with eight electrons in their outermost (valence) shell, similar to noble gases.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
748e87dc-7316-4405-acff-e17249ea927c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	5e899e6c-3ab7-49c2-94bc-97128921ca0b	multiple_choice	When an atom achieves an octet, its electron configuration becomes similar to that of which group of elements?	{"p_g": 0.25, "p_s": 0.1, "options": ["Alkali metals", "Halogens", "Noble gases", "Transition metals"], "explanation": "Atoms follow the octet rule to attain the highly stable electron configuration of a noble gas, which typically has eight valence electrons (with the exception of Helium, which has two).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
0f00fe7c-3ed3-435e-b510-7218b65f9d51	c18d6d95-77ed-4b41-a833-dc5cddec74f4	5e899e6c-3ab7-49c2-94bc-97128921ca0b	multiple_choice	Which of the following elements is most likely to form compounds that exhibit an 'expanded octet', meaning it can have more than eight valence electrons?	{"p_g": 0.25, "p_s": 0.1, "options": ["Nitrogen", "Carbon", "Sulfur", "Oxygen"], "explanation": "Elements in the third period and beyond (like Sulfur, Phosphorus, Chlorine) have available d-orbitals that allow them to accommodate more than eight electrons in their valence shell, leading to an expanded octet. Nitrogen and Carbon are typically limited to an octet.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
a280d714-9981-43d7-8d85-703fc3c10949	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9d42e1af-d1c3-4f7d-ad4e-c894d20cd878	multiple_choice	According to the modern Periodic Law, how are elements arranged in the periodic table?	{"p_g": 0.25, "p_s": 0.1, "options": ["By increasing atomic mass", "By increasing atomic number", "By alphabetical order of their symbols", "By their natural abundance"], "explanation": "The modern Periodic Law states that the properties of elements are a periodic function of their atomic number, leading to their arrangement by increasing atomic number.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
fd315f9c-eb86-49a3-b177-86bf4ceb3548	c18d6d95-77ed-4b41-a833-dc5cddec74f4	97c705f8-22db-4d00-b6ca-d8778da611dd	multiple_choice	For the reaction: 2Na + Cl₂ → 2NaCl, which substance represents the product?	{"p_g": 0.25, "p_s": 0.1, "options": ["Na", "Cl₂", "2NaCl", "Both Na and Cl₂"], "explanation": "In a chemical equation, reactants are on the left side of the arrow, and products are on the right side. NaCl (sodium chloride) is formed in this reaction.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
6b496590-01d9-463e-b129-01d14637d4c3	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9d42e1af-d1c3-4f7d-ad4e-c894d20cd878	multiple_choice	Which of the following phenomena is directly explained by the Periodic Law?	{"p_g": 0.25, "p_s": 0.1, "options": ["The existence of isotopes for a single element", "The consistent similarity in chemical reactivity among elements in the same group", "The constant speed of light in a vacuum", "The random distribution of electrons around an atom's nucleus"], "explanation": "The Periodic Law explains why elements in the same group (vertical column) often exhibit similar chemical behaviors and physical properties due to their similar electron configurations.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
78575cb3-8f37-4966-8770-1f6c953c2a12	c18d6d95-77ed-4b41-a833-dc5cddec74f4	9d42e1af-d1c3-4f7d-ad4e-c894d20cd878	multiple_choice	How did the Periodic Law aid in the discovery of new elements?	{"p_g": 0.25, "p_s": 0.1, "options": ["It provided a direct method for synthesizing elements in a lab.", "It allowed scientists to precisely calculate the atomic mass of any element.", "It enabled the prediction of properties for undiscovered elements based on their expected position.", "It explained why certain elements are radioactive and others are not."], "explanation": "Dmitri Mendeleev, using an early form of the Periodic Law, left gaps in his table and accurately predicted the properties of undiscovered elements like germanium and gallium, which were later found to match his predictions.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
77338972-b774-430f-9cc3-00b7e8b8d116	c18d6d95-77ed-4b41-a833-dc5cddec74f4	23c7d950-0603-4515-82d5-2fd2c2477bb0	multiple_choice	The elements in the periodic table are primarily ordered by which of the following?	{"p_g": 0.25, "p_s": 0.1, "options": ["Atomic mass", "Atomic number", "Number of neutrons", "Melting point"], "explanation": "The periodic table arranges elements in increasing order of their atomic number, which represents the number of protons in an atom's nucleus.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
19efa516-7aed-4e37-934a-df5ca6de32ec	c18d6d95-77ed-4b41-a833-dc5cddec74f4	23c7d950-0603-4515-82d5-2fd2c2477bb0	multiple_choice	Which of the following statements about elements in the same group (column) of the periodic table is generally true?	{"p_g": 0.25, "p_s": 0.1, "options": ["They have the same number of protons.", "They have similar chemical properties.", "They have the same atomic mass.", "They are all liquids at room temperature."], "explanation": "Elements in the same group have the same number of valence electrons, which largely determines their chemical reactivity and similar chemical properties.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
92d58b8f-8f56-46eb-93c5-2b25a9797e5c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	23c7d950-0603-4515-82d5-2fd2c2477bb0	multiple_choice	As you move from left to right across a period in the periodic table, what generally happens to the atomic radius?	{"p_g": 0.25, "p_s": 0.1, "options": ["It increases.", "It decreases.", "It remains constant.", "It first increases then decreases."], "explanation": "Moving across a period, the number of protons (atomic number) increases, leading to a stronger nuclear charge. This stronger positive charge pulls the electron shells closer to the nucleus, resulting in a decrease in atomic radius, even though the number of electron shells remains the same.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
81c28cdc-99b9-4fbd-bcc5-f4b8d9ff6a69	c18d6d95-77ed-4b41-a833-dc5cddec74f4	1284eb28-922c-4bca-9662-12150e3613da	multiple_choice	As you move down a group in the periodic table, what generally happens to the atomic radius?	{"p_g": 0.25, "p_s": 0.1, "options": ["It increases.", "It decreases.", "It stays the same.", "It first increases then decreases."], "explanation": "Down a group, the number of electron shells increases, adding more layers of electrons around the nucleus, which results in a larger atomic radius.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
9296a4c5-7fa9-41b3-a896-f1ebb4e79a73	c18d6d95-77ed-4b41-a833-dc5cddec74f4	1284eb28-922c-4bca-9662-12150e3613da	multiple_choice	Which of the following elements has the highest electronegativity?	{"p_g": 0.25, "p_s": 0.1, "options": ["Fluorine", "Oxygen", "Chlorine", "Nitrogen"], "explanation": "Electronegativity generally increases across a period from left to right and decreases down a group. Fluorine (F) is the most electronegative element on the periodic table.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
d8a57aca-3e1f-4ae4-acec-2a52bb8a4a01	c18d6d95-77ed-4b41-a833-dc5cddec74f4	1284eb28-922c-4bca-9662-12150e3613da	multiple_choice	When moving from left to right across a period in the periodic table, what is the general trend for ionization energy?	{"p_g": 0.25, "p_s": 0.1, "options": ["It generally increases due to increasing nuclear charge and decreasing atomic radius.", "It generally decreases due to increasing shielding effect.", "It remains constant because the number of valence electrons is the same.", "It increases, but only for transition metals."], "explanation": "Across a period, the effective nuclear charge increases and the atomic radius decreases. This means the outermost electrons are held more tightly by the nucleus, requiring more energy to remove them, thus increasing the ionization energy.", "correct_answer": 0}	hard	\N	2025-11-24 08:08:04.009802+00
32463bb2-926a-41b9-81d8-b6bef18d2007	c18d6d95-77ed-4b41-a833-dc5cddec74f4	a6bc1e6a-76ee-4dfc-bad0-474661023560	multiple_choice	What are the horizontal rows on the periodic table called?	{"p_g": 0.25, "p_s": 0.1, "options": ["Groups", "Blocks", "Periods", "Families"], "explanation": "The periodic table is organized into horizontal rows called periods and vertical columns called groups.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
c92cc9f8-6bb0-48a7-9553-8988455183e7	c18d6d95-77ed-4b41-a833-dc5cddec74f4	a6bc1e6a-76ee-4dfc-bad0-474661023560	multiple_choice	What does the period number of an element primarily indicate?	{"p_g": 0.25, "p_s": 0.1, "options": ["The number of protons in its nucleus", "The number of electron energy levels it possesses", "Its reactivity with other elements", "The number of valence electrons it has"], "explanation": "The period number directly corresponds to the principal quantum number (n), which represents the number of electron energy levels or shells an atom has.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
347b4bbb-ca53-47bd-aa8a-930592ceca10	c18d6d95-77ed-4b41-a833-dc5cddec74f4	a6bc1e6a-76ee-4dfc-bad0-474661023560	multiple_choice	An element is located in Period 4 of the periodic table. What can be inferred about its electron configuration?	{"p_g": 0.25, "p_s": 0.1, "options": ["It has 4 valence electrons.", "Its outermost electrons are in the first energy level.", "It has electrons occupying up to the fourth electron energy level.", "It is a noble gas."], "explanation": "Elements in Period 4 begin filling the fourth principal energy level (n=4) with electrons. This means their outermost electrons are in the fourth energy level.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
b1305b3a-e9b7-4fc2-9e7e-760b166865dc	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b7ea4228-050d-418c-8824-d3d24efb6404	multiple_choice	Which of the following is an example of a physical change?	{"p_g": 0.25, "p_s": 0.1, "options": ["Burning wood", "Rusting of iron", "Melting ice", "Baking a cake"], "explanation": "Melting ice changes water from a solid to a liquid, but its chemical composition (H2O) remains the same.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
e5f4fb2c-6497-40d4-b107-0435350847af	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b7ea4228-050d-418c-8824-d3d24efb6404	multiple_choice	Which characteristic best describes a physical change?	{"p_g": 0.25, "p_s": 0.1, "options": ["Formation of a new substance", "Change in chemical composition", "The substance retains its original chemical identity", "Irreversible alteration of molecular structure"], "explanation": "In a physical change, the identity of the substance remains the same, even if its form or state changes. No new substances are formed.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
54adb4b4-4182-4145-bddf-991589acb56d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b7ea4228-050d-418c-8824-d3d24efb6404	multiple_choice	When sugar dissolves in water, which statement accurately describes the change?	{"p_g": 0.25, "p_s": 0.1, "options": ["The sugar undergoes a chemical reaction with water to form a new compound.", "The sugar molecules break down into individual atoms, which then combine with water atoms.", "The sugar changes its physical state and disperses evenly in the water, but its chemical composition remains unchanged.", "The water molecules chemically bond with the sugar molecules, creating a permanent new substance."], "explanation": "Dissolving is a physical change because the sugar molecules are still sugar molecules, just dispersed among water molecules. The solution can be separated (e.g., by evaporation) to recover the sugar in its original form. No new chemical bonds are formed or broken to create a new substance.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
5e10b4cb-cfe1-4d53-9f92-6548a80eaf5e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0247469-39ea-4d8b-8ceb-e56ff8c800e9	multiple_choice	Which of the following is an example of a physical property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Flammability", "Reactivity with acid", "Color", "Ability to rust"], "explanation": "Color can be observed without changing the chemical composition of a substance.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
d5c53d60-da5d-41ac-ad23-b4984e0e1c87	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0247469-39ea-4d8b-8ceb-e56ff8c800e9	multiple_choice	When you boil water, which physical property are you primarily observing?	{"p_g": 0.25, "p_s": 0.1, "options": ["Density", "Boiling point", "Chemical reactivity", "Combustibility"], "explanation": "Boiling point is the temperature at which a liquid turns into a gas, and it's a characteristic physical property of a substance.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
b6b15256-8ff1-4b5d-919c-148e7a3bf941	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e0247469-39ea-4d8b-8ceb-e56ff8c800e9	multiple_choice	Which of the following statements correctly describes a physical property?	{"p_g": 0.25, "p_s": 0.1, "options": ["A substance's ability to react with oxygen is a physical property.", "The pH of a solution is considered a physical property.", "Malleability and ductility are examples of physical properties.", "The energy released during combustion is a physical property."], "explanation": "Malleability (ability to be hammered into thin sheets) and ductility (ability to be drawn into wires) are both physical properties as they describe how a material behaves under stress without changing its chemical identity.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
b05bd6ff-25e6-4236-b03e-84c841208ac8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2f7d280-4509-46a7-beb4-765a8a857d5c	multiple_choice	What is the defining characteristic of a polar covalent bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["Electrons are completely transferred from one atom to another.", "Electrons are shared equally between two atoms.", "Electrons are shared unequally between two atoms.", "Atoms are held together by electrostatic attraction without sharing electrons."], "explanation": "In a polar covalent bond, electrons are not shared equally between the bonded atoms due to differences in electronegativity.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
48ad026d-2fcd-4fc6-ba38-2b8f8225e2d9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2f7d280-4509-46a7-beb4-765a8a857d5c	multiple_choice	What causes the unequal sharing of electrons in a polar covalent bond?	{"p_g": 0.25, "p_s": 0.1, "options": ["A large difference in atomic size between the bonded atoms.", "The presence of a lone pair of electrons on one of the atoms.", "A significant difference in electronegativity between the bonded atoms.", "The total number of valence electrons in the molecule."], "explanation": "The significant difference in electronegativity between the two bonded atoms causes one atom to pull the shared electrons closer to itself, leading to unequal sharing.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
88cbe7e0-cbc9-4012-8396-79fea950d3f1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	b2f7d280-4509-46a7-beb4-765a8a857d5c	multiple_choice	Which of the following compounds contains polar covalent bonds?	{"p_g": 0.25, "p_s": 0.1, "options": ["N₂ (Nitrogen gas)", "F₂ (Fluorine gas)", "NaCl (Sodium chloride)", "H₂O (Water)"], "explanation": "In water (H₂O), oxygen is significantly more electronegative than hydrogen, leading to unequal sharing of electrons in the O-H bonds, making them polar covalent. N₂ and F₂ have nonpolar covalent bonds because the atoms have identical electronegativity. NaCl forms an ionic bond due to a large electronegativity difference resulting in electron transfer.", "correct_answer": 3}	hard	\N	2025-11-24 08:08:04.009802+00
04d33801-3554-4db3-a143-a77ab571d580	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ec48015c-776b-4bc2-9d39-9c2c22ceb2df	multiple_choice	Which characteristic is essential for a molecule to be considered polar?	{"p_g": 0.25, "p_s": 0.1, "options": ["Having a net dipole moment", "Being perfectly symmetrical", "Containing only nonpolar bonds", "Having a high molecular weight"], "explanation": "A polar molecule must have a net dipole moment, meaning there's an uneven distribution of electron density.", "correct_answer": 0}	easy	\N	2025-11-24 08:08:04.009802+00
a92522e7-30f6-4808-b3e4-de2c9cc9533c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ec48015c-776b-4bc2-9d39-9c2c22ceb2df	multiple_choice	Which of the following molecules is polar?	{"p_g": 0.25, "p_s": 0.1, "options": ["CO2 (Carbon Dioxide)", "CH4 (Methane)", "H2O (Water)", "O2 (Oxygen)"], "explanation": "Water (H2O) has a bent molecular geometry and polar O-H bonds, leading to an overall net dipole moment.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
04557858-31c8-4d1e-8afe-5015e4d7ac01	c18d6d95-77ed-4b41-a833-dc5cddec74f4	ec48015c-776b-4bc2-9d39-9c2c22ceb2df	multiple_choice	Despite having polar bonds, carbon tetrachloride (CCl4) is a nonpolar molecule. What is the primary reason for this?	{"p_g": 0.25, "p_s": 0.1, "options": ["The electronegativity difference between carbon and chlorine is negligible.", "The molecule's symmetrical tetrahedral shape causes the individual bond dipoles to cancel out.", "Carbon tetrachloride is an ionic compound, not a covalent one.", "The bonds in CCl4 are actually nonpolar."], "explanation": "CCl4 has a symmetrical tetrahedral geometry. Even though each C-Cl bond is polar, the dipoles are oriented symmetrically and cancel each other out, resulting in no net dipole moment.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
db1cd806-423d-44cc-9e44-92196a088d38	c18d6d95-77ed-4b41-a833-dc5cddec74f4	97c705f8-22db-4d00-b6ca-d8778da611dd	multiple_choice	In a chemical reaction, what is the term for a substance that is formed?	{"p_g": 0.25, "p_s": 0.1, "options": ["Reactant", "Catalyst", "Solvent", "Product"], "explanation": "A product is defined as a substance that is formed as a result of a chemical reaction.", "correct_answer": 3}	easy	\N	2025-11-24 08:08:04.009802+00
682127c4-928c-47c6-9bde-2fb52c7f8382	c18d6d95-77ed-4b41-a833-dc5cddec74f4	97c705f8-22db-4d00-b6ca-d8778da611dd	multiple_choice	Which of the following is generally true regarding products in a balanced chemical equation?	{"p_g": 0.25, "p_s": 0.1, "options": ["They are always simple elements.", "Their total mass is less than the total mass of the reactants.", "They are typically found on the right side of the reaction arrow.", "They are consumed during the chemical process."], "explanation": "By convention, products are written on the right side of the reaction arrow, while reactants are on the left. The total mass of products must equal the total mass of reactants due to the law of conservation of mass.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f80dc5b5-a4ec-4900-bad1-f58db2b2d5ac	c18d6d95-77ed-4b41-a833-dc5cddec74f4	de17b869-c87c-431f-8e65-fac239ffd712	multiple_choice	What is the electric charge of a proton?	{"p_g": 0.25, "p_s": 0.1, "options": ["Negative", "Neutral", "Positive", "Variable"], "explanation": "Protons are defined as having a positive (1+) electric charge, which is fundamental to their role in atomic structure.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
c1e114ee-69a4-4104-a08e-380b3cc69c1a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	de17b869-c87c-431f-8e65-fac239ffd712	multiple_choice	Which atomic property is uniquely determined by the number of protons in an atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["Atomic mass", "Isotope", "Atomic number", "Number of neutrons"], "explanation": "The number of protons in an atom's nucleus defines its atomic number, which in turn determines the element it is. For example, all atoms with 6 protons are carbon atoms.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
e98f76d5-84fc-4820-90a0-9ddd728b29a0	c18d6d95-77ed-4b41-a833-dc5cddec74f4	de17b869-c87c-431f-8e65-fac239ffd712	multiple_choice	If an atom gains a proton, which of the following statements is true?	{"p_g": 0.25, "p_s": 0.1, "options": ["It becomes an ion of the same element.", "Its atomic mass decreases significantly.", "It transforms into a different element.", "Its electron configuration remains unchanged."], "explanation": "The number of protons determines an atom's identity as a specific element. Changing the number of protons fundamentally changes the element itself, not just its charge or mass, although those would also change.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
487a155c-1337-4ae7-9398-0f5267dda75c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e704edef-1bbf-4ab8-86df-08cc199575f5	multiple_choice	Which of the following is an example of a qualitative property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Mass", "Volume", "Color", "Temperature"], "explanation": "Qualitative properties are described with words, not numbers. 'Color' describes a quality without a numerical value.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
cd23a6bd-b0df-48e6-86f4-fdd12e623ef9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e704edef-1bbf-4ab8-86df-08cc199575f5	multiple_choice	A scientist observes a substance and notes its 'strong pungent smell'. This observation describes which type of property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Quantitative property", "Physical change", "Qualitative property", "Chemical change"], "explanation": "A 'strong pungent smell' is a description using words and senses, not a numerical measurement, making it a qualitative property.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
3999395d-09ee-4683-b5a6-ad7e5ea4e0f1	c18d6d95-77ed-4b41-a833-dc5cddec74f4	e704edef-1bbf-4ab8-86df-08cc199575f5	multiple_choice	Which statement best distinguishes a qualitative property from a quantitative property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Qualitative properties are always intensive, while quantitative properties are always extensive.", "Qualitative properties can be observed and described without measurement, while quantitative properties require numerical measurement.", "Qualitative properties relate to chemical reactions, whereas quantitative properties relate to physical states.", "Qualitative properties are subjective, while quantitative properties are objective."], "explanation": "The core difference is whether the property is described by observation and words (qualitative) or measured numerically (quantitative).", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
c17eb8a8-13d7-49f6-9284-738c9f6f9e10	c18d6d95-77ed-4b41-a833-dc5cddec74f4	5109e661-34b4-4136-9e88-dbb049e4dd1a	multiple_choice	Which of the following is an example of a quantitative property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Color", "Smell", "Temperature", "Texture"], "explanation": "Quantitative properties are those that can be measured and expressed numerically. Temperature is measured in units like Celsius or Fahrenheit.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
82ab27ff-ddc0-47a5-86fc-265f5378b3b2	c18d6d95-77ed-4b41-a833-dc5cddec74f4	5109e661-34b4-4136-9e88-dbb049e4dd1a	multiple_choice	Why is 'density' considered a quantitative property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Because it describes how an object feels", "Because it can be observed without measurement", "Because it can be measured and expressed with a numerical value and units", "Because it changes based on the observer's perception"], "explanation": "Density is calculated as mass divided by volume, both of which are measurable quantities, resulting in a numerical value (e.g., g/cm³).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
96677e99-4120-478e-a191-cce1560c54a5	c18d6d95-77ed-4b41-a833-dc5cddec74f4	5109e661-34b4-4136-9e88-dbb049e4dd1a	multiple_choice	Which statement best distinguishes a quantitative property from a qualitative property?	{"p_g": 0.25, "p_s": 0.1, "options": ["Quantitative properties are always more important than qualitative properties.", "Quantitative properties are inherent to the substance, while qualitative properties are not.", "Quantitative properties can be precisely measured and assigned a numerical value, unlike qualitative properties.", "Qualitative properties describe physical states, whereas quantitative properties describe chemical reactions."], "explanation": "The key difference is measurability and numerical expression. Qualitative properties are descriptive (e.g., color, shape), while quantitative properties provide numerical data (e.g., mass, length).", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f5840b5b-3c15-40ac-9a48-c286dbbc9263	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d60a6e19-8692-4f5c-9bc8-516308754ae2	multiple_choice	In a chemical reaction, what do we call the substances that are present at the beginning and are consumed during the reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["Products", "Catalysts", "Reactants", "Solvents"], "explanation": "Reactants are the starting materials in a chemical reaction that are consumed to form new substances.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
6870b894-9d6b-42a0-8ed6-e2571ea20d9d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d60a6e19-8692-4f5c-9bc8-516308754ae2	multiple_choice	Consider the reaction: A + B → C. Which of the following represents the reactants?	{"p_g": 0.25, "p_s": 0.1, "options": ["A and C", "B and C", "A and B", "Only C"], "explanation": "In the general form of a chemical equation, substances on the left side of the arrow are the reactants, and substances on the right side are the products.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
d8c2cac6-1d2d-44c8-b9f9-3f7c6ac01aaf	c18d6d95-77ed-4b41-a833-dc5cddec74f4	d60a6e19-8692-4f5c-9bc8-516308754ae2	multiple_choice	Which statement best describes the role of a reactant in a chemical change?	{"p_g": 0.25, "p_s": 0.1, "options": ["It is a substance that speeds up the reaction without being consumed.", "It is a substance that is formed as a result of the chemical reaction.", "It is a substance that is chemically transformed into new substances during the reaction.", "It is an inert substance that provides a medium for the reaction to occur."], "explanation": "Reactants are the substances that undergo transformation, breaking their original bonds and forming new ones to create different substances (products). They are chemically altered during the process.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
9bb19dcb-e596-4f26-8abb-6c4a51455f16	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7fcd7de4-2594-4e15-befb-91776b2cc407	multiple_choice	When multiplying or dividing measurements, the result should be reported with the same number of significant figures as which of the following?	{"p_g": 0.25, "p_s": 0.1, "options": ["The measurement with the most significant figures.", "The measurement with the fewest significant figures.", "The exact number of significant figures in the most precise measurement.", "Always three significant figures."], "explanation": "The rule for multiplication and division states that the answer must be rounded to the same number of significant figures as the measurement with the fewest significant figures.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
80f34816-2a6b-44ca-a97d-6fd2dfbaae1f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7fcd7de4-2594-4e15-befb-91776b2cc407	multiple_choice	Calculate the product of 3.4 cm and 1.25 cm, reporting the answer with the correct number of significant figures.	{"p_g": 0.25, "p_s": 0.1, "options": ["4.25 cm²", "4.3 cm²", "4.2 cm²", "4.250 cm²"], "explanation": "The measurement 3.4 cm has two significant figures, and 1.25 cm has three significant figures. In multiplication, the result must be rounded to the same number of significant figures as the measurement with the fewest significant figures. The product 3.4 * 1.25 = 4.25 cm², which, when rounded to two significant figures, is 4.3 cm².", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
c24c9724-0d1d-4b86-a293-99f0d83a968b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7fcd7de4-2594-4e15-befb-91776b2cc407	multiple_choice	Perform the following calculation and report the answer with the correct number of significant figures: (15.25 - 3.1) / 2.00	{"p_g": 0.25, "p_s": 0.1, "options": ["6.075", "6.08", "6.1", "6"], "explanation": "First, perform the subtraction: 15.25 - 3.1 = 12.15. For addition/subtraction, the result is limited by the number with the fewest decimal places (3.1 has one decimal place). So, the intermediate result 12.15 should be considered to have 3 significant figures (like 12.2). Next, perform the division: 12.15 / 2.00. The number 12.15 effectively has 3 significant figures (from the subtraction rule), and 2.00 has 3 significant figures. In division, the result is limited by the number with the fewest significant figures, which is 3. Therefore, 12.15 / 2.00 = 6.075, rounded to three significant figures is 6.08.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
0c556647-2bbb-48b3-8729-b83bf4c58c88	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7826e10e-5679-467b-8c46-54573873de21	multiple_choice	What do significant digits in a measurement primarily indicate?	{"p_g": 0.25, "p_s": 0.1, "options": ["The accuracy of the measurement.", "The precision of the measurement.", "The absolute value of the measurement.", "The unit of the measurement."], "explanation": "Significant digits reflect how precisely a measurement was made, based on the certainty of the digits.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
c66a5606-e36c-4c91-aaad-0f50079e2e4d	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7826e10e-5679-467b-8c46-54573873de21	multiple_choice	How many significant digits are in the measurement 20.05 meters?	{"p_g": 0.25, "p_s": 0.1, "options": ["2", "3", "4", "5"], "explanation": "All non-zero digits are significant. Zeros between non-zero digits are also significant. Therefore, 2, 0, 0, and 5 are all significant.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
8c2a28bd-463c-44b5-a2fc-17faa578b1f8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	7826e10e-5679-467b-8c46-54573873de21	multiple_choice	How many significant digits are in the number 1200, assuming it's a measurement without an explicit decimal point?	{"p_g": 0.25, "p_s": 0.1, "options": ["1", "2", "3", "4"], "explanation": "When a number ends with zeros but has no decimal point, the trailing zeros are generally considered placeholders and not significant. Only the non-zero digits (1 and 2) are significant, indicating the precision is to the hundreds place. If a decimal point were present (e.g., 1200.), then all four digits would be significant.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
3f874482-491e-4666-9f04-d19145901c38	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0cfbe794-6522-4563-ae78-e6cdb0c540a2	multiple_choice	Which of the following best describes a single displacement reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["Two compounds exchange ions to form two new compounds.", "An element reacts with a compound, displacing another element from it.", "Two or more reactants combine to form a single product.", "A single compound breaks down into two or more simpler substances."], "explanation": "In a single displacement reaction, one element replaces another element in a compound.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
85ac08dc-c2f1-4fff-be62-c8a998c634d8	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0cfbe794-6522-4563-ae78-e6cdb0c540a2	multiple_choice	Which of the following is an example of a single displacement reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["HCl + NaOH → NaCl + H₂O", "2H₂ + O₂ → 2H₂O", "2Na + 2HCl → 2NaCl + H₂", "CaCO₃ → CaO + CO₂"], "explanation": "In the reaction 2Na + 2HCl → 2NaCl + H₂, the element sodium (Na) displaces hydrogen (H) from hydrochloric acid (HCl).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
0fcef26e-126f-4605-9d59-aa39fc93839c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	0cfbe794-6522-4563-ae78-e6cdb0c540a2	multiple_choice	Given the general reaction A + BC → AC + B, what condition must element A satisfy for this reaction to occur spontaneously?	{"p_g": 0.25, "p_s": 0.1, "options": ["Element A must be less reactive than element B.", "Element A must be more reactive than element B.", "Element A and element B must have the same reactivity.", "Element A must be a noble gas."], "explanation": "For a single displacement reaction to occur, the displacing element (A) must be more reactive than the element it is replacing (B).", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
d15bd5f1-b1a1-4ae8-8feb-0b007c357b93	c18d6d95-77ed-4b41-a833-dc5cddec74f4	21d0eba5-717e-4be9-a730-a39707edaafe	multiple_choice	What is the primary characteristic of a skeleton equation?	{"p_g": 0.25, "p_s": 0.1, "options": ["It uses chemical names for all substances.", "It shows the exact number of atoms for each element.", "It represents reactants and products using chemical formulas.", "It only includes the major products of a reaction."], "explanation": "A skeleton equation uses chemical formulas to represent the substances involved in a reaction, along with their physical states.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
4ba1583a-f53f-48c0-8d9a-a11c631960bb	c18d6d95-77ed-4b41-a833-dc5cddec74f4	21d0eba5-717e-4be9-a730-a39707edaafe	multiple_choice	Which of the following correctly represents a skeleton equation for the reaction of hydrogen gas with oxygen gas to form water?	{"p_g": 0.25, "p_s": 0.1, "options": ["H₂(g) + O₂(g) → H₂O(l)", "2H₂(g) + O₂(g) → 2H₂O(l)", "Hydrogen + Oxygen → Water", "H₂O(l) → H₂(g) + O₂(g)"], "explanation": "A skeleton equation uses chemical formulas for reactants and products and shows their physical states, but it is not necessarily balanced. Option A shows the correct reactants and product with chemical formulas.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
8f803213-d9c6-4a53-9e8c-8ce9adb34e0e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	21d0eba5-717e-4be9-a730-a39707edaafe	multiple_choice	A student writes the following equation: Mg(s) + O₂(g) → MgO(s). Why is this considered a skeleton equation rather than a fully balanced chemical equation?	{"p_g": 0.25, "p_s": 0.1, "options": ["It does not include the physical states of the reactants and products.", "The number of oxygen atoms on both sides of the equation is not equal.", "It uses chemical formulas instead of chemical names.", "It only shows the major products, not all possible byproducts."], "explanation": "A skeleton equation uses chemical formulas and indicates physical states, but it does not necessarily have the same number of atoms for each element on both sides of the equation, which is required for a balanced chemical equation. In this specific example, there are two oxygen atoms on the reactant side (O₂) but only one on the product side (MgO).", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
c72fac57-ac85-47be-acb4-47635a0d279f	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2c849279-4241-4d73-82ca-e720dfdb4c1d	multiple_choice	What is the primary characteristic of an atom with a stable octet?	{"p_g": 0.25, "p_s": 0.1, "options": ["It has eight protons in its nucleus.", "It has a completely filled outermost energy level with eight valence electrons.", "It has eight neutrons in its nucleus.", "It is an atom of a transition metal."], "explanation": "A stable octet refers to an atom having eight valence electrons in its outermost energy level, which is a very stable configuration.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
8d942c24-9540-4776-9c0a-50068f201dea	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2c849279-4241-4d73-82ca-e720dfdb4c1d	multiple_choice	Which of the following elements typically achieves a stable octet by gaining one electron?	{"p_g": 0.25, "p_s": 0.1, "options": ["Sodium (Na)", "Carbon (C)", "Chlorine (Cl)", "Helium (He)"], "explanation": "Chlorine (Group 17) has seven valence electrons and will gain one electron to complete its octet, forming a chloride ion (Cl-).", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
9131a80b-24ee-42d5-be89-3d5f8e299e8a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	2c849279-4241-4d73-82ca-e720dfdb4c1d	multiple_choice	Which of the following is an exception to the octet rule where an atom can be stable with fewer than eight valence electrons?	{"p_g": 0.25, "p_s": 0.1, "options": ["Oxygen (O)", "Neon (Ne)", "Boron (B)", "Sulfur (S)"], "explanation": "Boron (B) is known to form stable compounds where it has only six valence electrons, making it an exception to the octet rule.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f5432275-15c2-44d7-9759-fee7b640bb8b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	644b02cf-dc17-4ef5-b996-9ee9f2d826ce	multiple_choice	Which of the following best describes a synthesis reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["A single compound breaks down into two or more simpler substances.", "Two or more substances combine to form a single, more complex substance.", "An element reacts with a compound, displacing another element from the compound.", "The ions of two compounds exchange places to form two new compounds."], "explanation": "A synthesis reaction is defined as two or more simpler substances combining to form a single, more complex substance.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
cd77cf86-52dc-4f08-a3ca-a75c1f21ff5a	c18d6d95-77ed-4b41-a833-dc5cddec74f4	644b02cf-dc17-4ef5-b996-9ee9f2d826ce	multiple_choice	Which of the following chemical equations represents a synthesis reaction?	{"p_g": 0.25, "p_s": 0.1, "options": ["2H₂ + O₂ → 2H₂O", "CaCO₃ → CaO + CO₂", "Zn + 2HCl → ZnCl₂ + H₂", "NaCl + AgNO₃ → AgCl + NaNO₃"], "explanation": "In this reaction, two elements (H₂ and O₂) combine to form a single, more complex compound (H₂O), which fits the definition of a synthesis reaction.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
d5a669c1-5a3d-44db-993c-489a12279efc	c18d6d95-77ed-4b41-a833-dc5cddec74f4	644b02cf-dc17-4ef5-b996-9ee9f2d826ce	multiple_choice	When two elements combine in a synthesis reaction, what is always true about the product?	{"p_g": 0.25, "p_s": 0.1, "options": ["It is an element.", "It is a compound.", "It has a lower molar mass than either reactant.", "It is always in a gaseous state."], "explanation": "By definition, a synthesis reaction forms a single, more complex substance from two or more simpler ones. When elements combine, they form a compound, which is inherently more complex than the individual elements.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
7eefa943-ba33-4104-ba9a-aa5899fe7baf	c18d6d95-77ed-4b41-a833-dc5cddec74f4	92382f9e-f3b4-426f-805a-cee1145787fa	multiple_choice	What is the SI unit for the amount of a substance?	{"p_g": 0.25, "p_s": 0.1, "options": ["Gram", "Liter", "Mole", "Kilogram"], "explanation": "The mole is the fundamental SI unit used to measure the amount of a substance.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
10e25bc5-ab10-4b57-af91-7eda8a6e9a4b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	92382f9e-f3b4-426f-805a-cee1145787fa	multiple_choice	How many elementary entities are contained in one mole of any substance?	{"p_g": 0.25, "p_s": 0.1, "options": ["1.0 x 10^23", "6.022 x 10^23", "6.022 x 10^22", "12.044 x 10^23"], "explanation": "One mole of any substance always contains Avogadro's number of particles, which is approximately 6.022 x 10^23.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
d05d9ae6-7f79-4243-abb5-63cabf4234d9	c18d6d95-77ed-4b41-a833-dc5cddec74f4	92382f9e-f3b4-426f-805a-cee1145787fa	multiple_choice	If you have 0.5 moles of water (H2O) and 0.5 moles of carbon dioxide (CO2), which statement is true regarding the number of molecules?	{"p_g": 0.25, "p_s": 0.1, "options": ["0.5 moles of water contains more molecules.", "0.5 moles of carbon dioxide contains more molecules.", "Both contain the same number of molecules.", "It depends on the molar mass of each substance."], "explanation": "By definition, one mole of any substance contains the same number of elementary entities (molecules in this case). Therefore, 0.5 moles of water will contain the same number of molecules as 0.5 moles of carbon dioxide.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
1861bb94-a83e-4771-b5d2-48be37b45a90	c18d6d95-77ed-4b41-a833-dc5cddec74f4	cdc61a35-0b01-4101-9e41-cdb32510c3a3	multiple_choice	Which groups on the periodic table are generally classified as transition elements?	{"p_g": 0.25, "p_s": 0.1, "options": ["Groups 1 and 2", "Groups 3 through 12", "Groups 13 through 18", "Lanthanides and Actinides only"], "explanation": "The definition of transition elements specifically refers to elements located in Groups 3 through 12 of the periodic table.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
e839bd8a-6684-41a2-8981-6770928a9e6e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	cdc61a35-0b01-4101-9e41-cdb32510c3a3	multiple_choice	Which of the following is a common characteristic property of transition elements?	{"p_g": 0.25, "p_s": 0.1, "options": ["They are all gases at room temperature.", "They typically have low densities.", "They often form colored compounds.", "They only exhibit a single oxidation state."], "explanation": "A defining characteristic of many transition elements is their ability to form ions that produce vibrant colored solutions and compounds due to d-orbital electron transitions.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
7f703360-51d4-4b6f-843f-29500ec55a6b	c18d6d95-77ed-4b41-a833-dc5cddec74f4	cdc61a35-0b01-4101-9e41-cdb32510c3a3	multiple_choice	Which of the following properties is *least* typical for most transition elements?	{"p_g": 0.25, "p_s": 0.1, "options": ["High electrical and thermal conductivity.", "Ability to form compounds with variable oxidation states.", "Generally low melting and boiling points.", "Tendency to form complex ions."], "explanation": "Most transition elements are metals with strong metallic bonding, resulting in generally high melting and boiling points. Low melting and boiling points are more characteristic of non-metals or some main group elements.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
ff82e0c6-1284-4c6f-a3c7-4b007912e396	c18d6d95-77ed-4b41-a833-dc5cddec74f4	080408b6-2e23-42f9-ac8f-ee896f167e44	multiple_choice	What is the fundamental reason that all measurements have some degree of uncertainty?	{"p_g": 0.25, "p_s": 0.1, "options": ["Measuring devices are always broken.", "It is impossible to achieve perfect precision.", "Scientists intentionally make errors.", "The object being measured changes constantly."], "explanation": "Uncertainty is inherent in measurement because no instrument can provide infinite precision, and there are always limits to how accurately a quantity can be determined.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
b94d8820-7900-486b-9bd6-5b439a45c420	c18d6d95-77ed-4b41-a833-dc5cddec74f4	080408b6-2e23-42f9-ac8f-ee896f167e44	multiple_choice	Which of the following factors is LEAST likely to contribute to the uncertainty in a measurement?	{"p_g": 0.25, "p_s": 0.1, "options": ["The limitations of the measuring instrument.", "Environmental conditions (e.g., temperature, humidity).", "The brand name of the measuring device.", "The skill and judgment of the observer."], "explanation": "While the brand of the measuring device might correlate with its quality and therefore its inherent uncertainty, the brand itself is not a direct source of uncertainty in the same way that instrument limitations, environmental conditions, or observer skill are.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
647d35b8-96e9-41ca-9a1e-c4e66e9a993e	c18d6d95-77ed-4b41-a833-dc5cddec74f4	080408b6-2e23-42f9-ac8f-ee896f167e44	multiple_choice	When a measurement is reported as 15.2 ± 0.1 cm, what does the '± 0.1 cm' primarily communicate?	{"p_g": 0.25, "p_s": 0.1, "options": ["The exact margin of error due to human mistakes only.", "The absolute precision of the instrument used.", "The range within which the true value is expected to fall.", "That the measurement was performed incorrectly."], "explanation": "The '±' value represents the estimated uncertainty, indicating the range within which the true value of the measured quantity is believed to lie with a certain level of confidence.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
f96ec0a6-e3f9-4b85-92a6-22b4a09c726c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	321ed919-f6e7-45e7-8e15-70dc04966054	multiple_choice	What does the valence of an element represent?	{"p_g": 0.25, "p_s": 0.1, "options": ["Its atomic number", "Its combining capacity in chemical bonds", "Its melting point", "Its density"], "explanation": "Valence specifically describes an atom's capacity to form chemical bonds by interacting with electrons.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
a57838ff-e10e-42ed-af27-647cb24a7167	c18d6d95-77ed-4b41-a833-dc5cddec74f4	321ed919-f6e7-45e7-8e15-70dc04966054	multiple_choice	An element has a valence of 2. What does this most likely indicate about its electron behavior in bonding?	{"p_g": 0.25, "p_s": 0.1, "options": ["It can only gain one electron.", "It will always lose three electrons.", "It can lose, gain, or share two electrons.", "It has a full outer electron shell."], "explanation": "A valence of 2 means the atom typically loses, gains, or shares two electrons to achieve a stable electron configuration.", "correct_answer": 2}	medium	\N	2025-11-24 08:08:04.009802+00
f2777be7-dbde-40c2-af86-d8e1fce593be	c18d6d95-77ed-4b41-a833-dc5cddec74f4	321ed919-f6e7-45e7-8e15-70dc04966054	multiple_choice	If Element X (valence 1) reacts with Element Y (valence 2), what is the most likely chemical formula for the resulting compound?	{"p_g": 0.25, "p_s": 0.1, "options": ["XY", "X2Y", "XY2", "X2Y2"], "explanation": "To balance the valencies, two atoms of Element X (each contributing 1 combining capacity) are needed for every one atom of Element Y (contributing 2 combining capacity), resulting in X2Y.", "correct_answer": 1}	hard	\N	2025-11-24 08:08:04.009802+00
621b89b5-5e73-4e8b-b344-c0bacac08dca	c18d6d95-77ed-4b41-a833-dc5cddec74f4	818d8a1c-db56-4ca0-a36a-d31e04d330ba	multiple_choice	Where are valence electrons found within an atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["In the nucleus", "In the innermost energy level", "In the outermost energy level", "Distributed evenly throughout the atom"], "explanation": "Valence electrons are defined as the electrons in the outermost energy level of an atom.", "correct_answer": 2}	easy	\N	2025-11-24 08:08:04.009802+00
82a68b7c-dfe3-4436-bace-92b86821b51c	c18d6d95-77ed-4b41-a833-dc5cddec74f4	818d8a1c-db56-4ca0-a36a-d31e04d330ba	multiple_choice	What is the primary role of valence electrons in an atom?	{"p_g": 0.25, "p_s": 0.1, "options": ["Determining the atomic mass", "Participating in chemical bonding and reactions", "Maintaining the atom's neutral charge", "Producing light when excited"], "explanation": "Valence electrons are directly involved in forming chemical bonds with other atoms, determining an atom's reactivity.", "correct_answer": 1}	medium	\N	2025-11-24 08:08:04.009802+00
12b9f504-68e2-44ce-be10-3f2ef0c1e3bf	c18d6d95-77ed-4b41-a833-dc5cddec74f4	818d8a1c-db56-4ca0-a36a-d31e04d330ba	multiple_choice	Which of the following elements typically has 7 valence electrons?	{"p_g": 0.25, "p_s": 0.1, "options": ["Carbon", "Neon", "Fluorine", "Calcium"], "explanation": "Elements in Group 17 of the periodic table, known as halogens, have 7 valence electrons. Fluorine is a halogen.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
00671034-bd9c-4611-9d35-57e743f27007	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4f5767af-a51f-4c9b-ae88-4bfa70a9e090	multiple_choice	Which of the following best describes a word equation?	{"p_g": 0.25, "p_s": 0.1, "options": ["An equation using chemical symbols and numbers.", "A chemical equation that identifies reactants and products by their names.", "A mathematical equation describing energy changes.", "An equation that only shows the products of a reaction."], "explanation": "A word equation uses the full names of substances to represent a chemical reaction, rather than chemical formulas.", "correct_answer": 1}	easy	\N	2025-11-24 08:08:04.009802+00
a6a969c3-3841-4ba3-b7e9-a83f78cde7fd	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4f5767af-a51f-4c9b-ae88-4bfa70a9e090	multiple_choice	Which is the correct word equation for the reaction: H₂ + Cl₂ → 2HCl?	{"p_g": 0.25, "p_s": 0.1, "options": ["Hydrogen plus Chlorine yields Hydrogen Chloride", "Water plus Chlorine yields Hydrochloric acid", "Hydrogen plus Chloride yields Hydrogen Chlorine", "Hydrogen and Chlorine produces Water"], "explanation": "The reactants are hydrogen and chlorine, and they combine to form the product hydrogen chloride.", "correct_answer": 0}	medium	\N	2025-11-24 08:08:04.009802+00
d00ad042-1061-438e-af5d-c874b5992811	c18d6d95-77ed-4b41-a833-dc5cddec74f4	4f5767af-a51f-4c9b-ae88-4bfa70a9e090	multiple_choice	Consider the word equation: 'Sodium + Oxygen → Sodium Oxide'. What information is NOT explicitly conveyed by this word equation?	{"p_g": 0.25, "p_s": 0.1, "options": ["The names of the reactants.", "The name of the product.", "Whether the equation is balanced.", "That a chemical reaction has occurred."], "explanation": "Word equations show the names of reactants and products but do not indicate the exact ratios (stoichiometry) or the physical states of the substances involved. Chemical formulas and balanced equations are needed for that.", "correct_answer": 2}	hard	\N	2025-11-24 08:08:04.009802+00
\.


--
-- Data for Name: quiz_attempts; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.quiz_attempts (attempt_id, user_id, course_id, question_num, status, score, created_at, submitted_at) FROM stdin;
6331ffb2-32a9-4c86-9131-575d42ad73e2	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	0	2025-11-07 02:56:58.416284+00	2025-11-07 02:57:08.36163+00
90c18393-4542-4420-8a94-324aed63d6b5	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	0	2025-11-07 02:57:41.243312+00	2025-11-07 02:57:51.329953+00
5048d92f-4125-496c-8f11-aae8a07763a6	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	0	2025-11-07 02:58:46.502161+00	2025-11-07 02:58:54.294787+00
28fdf002-af47-4c12-8a1a-5fdaadb4552a	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	100	2025-11-07 03:07:30.595196+00	2025-11-07 03:07:52.299013+00
7d30b139-1b0a-49d6-97d3-53a9dae2d63f	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	100	2025-11-07 03:07:58.665278+00	2025-11-07 03:08:09.419752+00
c93d5c74-3156-4a7a-babd-2ce0cd5a63f8	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	100	2025-11-08 00:56:52.463755+00	2025-11-08 00:57:00.749595+00
e1d0d366-aca6-4b81-93d4-6bfde8cc61f5	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	0	2025-11-08 15:18:26.376047+00	2025-11-08 15:18:38.783166+00
5d91f050-5bb8-4847-a13d-ea0f01ac7ebe	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	g10_phys	5	COMPLETED	0	2025-11-08 17:35:13.651809+00	2025-11-08 17:36:44.892113+00
\.


--
-- Data for Name: submission_answers; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.submission_answers (id, user_id, graph_id, question_id, user_answer, is_correct, created_at) FROM stdin;
b4c074e7-f3de-4e33-97cf-31e4f9455de0	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f70d0cb4-a576-441f-b0e7-64cfb4344eb6	{"question_type": "multiple_choice", "selected_option": 0}	f	2025-11-18 23:50:05.141841+00
5c9fd94b-0850-4bfc-8e51-d73c2c733cf1	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	fa44f67f-bb93-4e24-a694-eed01db44f36	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-18 23:50:19.63062+00
c6f33a3f-2ad6-4dfc-9c6f-7898070fd560	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e7e7c705-371c-4616-8e9c-8c4e15f8f9f7	{"question_type": "multiple_choice", "selected_option": 2}	f	2025-11-18 23:50:22.872164+00
56c141ac-a2ad-4ee1-9940-1384d16df4fd	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	33a7fcba-76e9-471a-9704-4a60b2b7315f	{"question_type": "multiple_choice", "selected_option": 3}	f	2025-11-18 23:50:26.098725+00
e83e2fb4-2bc0-440e-84fa-61c590b4f800	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f24b2455-e31d-4b3b-93e1-6656f7df4281	{"question_type": "multiple_choice", "selected_option": 3}	f	2025-11-18 23:52:40.059613+00
5d8db52f-7888-4d3a-8f5e-d92696031028	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a8f8fb69-5e5b-4605-b79f-595d83929acc	{"question_type": "multiple_choice", "selected_option": 0}	f	2025-11-18 23:53:24.231191+00
bda488ec-76c0-4570-b945-b9ca396a91a8	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f2d093c7-a9a4-4f33-a50d-b7227f04301f	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-18 23:59:10.355971+00
360fc23e-dc61-4e90-adb3-e696b3d3c9f2	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	88612425-c0f4-40d4-b849-2dcaad7e8f01	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-18 23:59:14.237708+00
2b7d7101-418a-48b1-8148-3ba925ff1b1b	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b12899cb-e9ca-40cd-b2dd-c968f06799b0	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-18 23:59:45.824331+00
53d06d73-16a4-4490-abfe-3775f19a20c9	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	07ed798c-b374-4859-956f-e950895b6b93	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:14:29.437229+00
d60767c1-25ea-4115-9430-975f182e0046	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a8f8fb69-5e5b-4605-b79f-595d83929acc	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:14:35.386345+00
4348337a-ad8e-4ec3-a3a9-9189d2396723	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bb080873-b3f3-4478-96c0-989e25182203	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:14:40.819963+00
63ddd863-dd09-40fb-9208-41e35ab78828	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	fcbf38ef-1bc0-4cbc-9b13-df1ded2388ba	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:15:19.760922+00
a993799c-1c2d-4558-a30f-267688ae8f9b	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	21bb86b0-05a7-4c5e-a670-583d1bc8fd69	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:15:23.262349+00
0260c0ec-f4ae-49eb-a104-08425e6403b0	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a73a0267-1a14-4afa-8dca-7285d529ed61	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:15:26.422799+00
57a7006f-dc21-4a43-b534-7ab5fb909055	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f8edc315-66b6-4943-a796-fd72a1f6b4de	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:15:29.268903+00
dd334937-31f2-4661-bc6d-9a2ddd377591	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f19019f1-a5ca-4669-92a5-98e1e6473dfb	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:15:32.439927+00
493c973e-9029-4604-a2b2-9f33f52cb782	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	fd274804-7073-4fda-88d2-9f34d2fec55e	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:15:34.703594+00
7113cc10-c3a5-434a-a170-712341ec0413	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	96ff3096-7b9c-4256-90d8-f0ceaba025c6	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:38:43.852378+00
d90423a5-edf0-4b14-8423-35731569fe37	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	600e82cf-d974-4c65-b0cc-533ae2cfd9f4	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:38:48.180902+00
83b6b744-5467-4609-8636-d4af13f69b05	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6c7aa66d-f1c8-4a24-ba94-b4724c3b1247	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:38:50.917978+00
b6b01fba-7632-4909-9c02-40dc7143a784	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9359ca14-6a1a-48e1-b5c0-18fb6fb5bc32	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:38:54.255931+00
7ff2c77e-4bc9-463a-9879-0b394084f588	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a73a0267-1a14-4afa-8dca-7285d529ed61	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:38:56.544557+00
f160fb37-179a-400f-ab0c-f3195a8796ac	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f70d0cb4-a576-441f-b0e7-64cfb4344eb6	{"question_type": "multiple_choice", "selected_option": 3}	f	2025-11-23 03:38:58.410792+00
bf00ad86-3180-4e49-a8cc-114e8dffc204	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	fa44f67f-bb93-4e24-a694-eed01db44f36	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:39:00.360188+00
95f12864-a287-45ba-87bd-7a171c2fa514	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	ea4bb261-92ed-4484-abd6-4fe0c6768e8e	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:02.487386+00
b0938025-e7c3-4084-942c-127a856e1c33	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	f24b2455-e31d-4b3b-93e1-6656f7df4281	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:39:04.744103+00
b584bc1b-c726-4d01-a28c-502826e5565d	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	804dd9d0-1e05-4396-925e-7b99d9c34a3d	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:07.297029+00
83128fd1-06a6-4dc2-b256-1e60ca509415	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	254cf439-699f-4d8d-8b62-b16b1fd10303	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:09.518246+00
ad3819a0-abc5-4b84-98d8-4a3cf15460c6	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	79460e05-b819-4db1-b60a-4e0a16d8b92a	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:11.926893+00
e49dbc0f-782c-47ec-aee6-934a707381a7	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	26302288-5a67-4928-8e0a-d0492a696c3d	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:39:16.339645+00
11d3d58f-2ee2-4b87-ba33-5a337d7e0efb	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	fdaa1be0-270c-45cd-80a8-8cbb11831ba8	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:20.013119+00
d4ddfe53-7782-4e6d-8464-102c9c82f732	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	344c904d-f6d2-4deb-bdf9-51bb942f63e6	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:39:22.956646+00
a721d9ab-730f-494e-a724-5e30ff4507c2	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	8febb4e4-70cb-4b59-8e4c-30951fad590b	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:25.720239+00
57aca5c3-5f24-419f-9f3b-2137241047ab	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e83b775f-e3ea-430a-ad43-38f0cab695aa	{"question_type": "multiple_choice", "selected_option": 2}	f	2025-11-23 03:39:27.760701+00
2dd83202-8e88-4f62-86da-23a60e7723a0	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c0b48249-e3f7-43a5-b75a-3df69dd90d4f	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:39:29.754756+00
0dc60989-1003-41ac-80df-f9d5c9b873fb	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	395debdd-a9d1-4dd6-b4e0-6c4244807dda	{"question_type": "multiple_choice", "selected_option": 1}	f	2025-11-23 03:39:31.840584+00
4228a71e-3a9b-4a3e-a9cb-6003999ac741	f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6b7ce061-7a02-46e9-a5b0-75013efeea42	{"question_type": "multiple_choice", "selected_option": 0}	t	2025-11-23 03:39:33.827962+00
\.


--
-- Data for Name: subtopics; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.subtopics (graph_id, parent_node_id, child_node_id, weight, created_at) FROM stdin;
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	a7fa63f8-cff2-4dcd-8748-d456b669b014	0.1667	2025-11-13 20:06:22.337046+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	43bd532e-c53d-4669-9d44-365ff564c308	0.1667	2025-11-13 20:06:22.33943+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	d0fb6dbc-6b0b-4391-aa92-98b587aca876	0.1667	2025-11-13 20:06:22.340337+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	0.1667	2025-11-13 20:06:22.340997+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	cd52a236-4934-4574-8150-1b5c008d3b9c	0.1667	2025-11-13 20:06:22.341664+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	40a0cce9-df72-4721-b303-aa264a89d0e7	0.1665	2025-11-13 20:06:22.342279+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	bed1e3d1-1c3e-4260-860b-6984b797eafb	0.125	2025-11-13 20:06:22.342898+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	ebdea86b-4b32-4edb-9b93-f13e64300bff	0.125	2025-11-13 20:06:22.343501+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	b7dcf5b7-fd95-4dcc-b0e2-213826327a64	0.125	2025-11-13 20:06:22.344113+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	d622f0b9-3e3a-46ba-85e5-aa06aec310cc	0.125	2025-11-13 20:06:22.344682+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	b341ac8a-5a51-44ea-acaa-d25047d77a5d	0.125	2025-11-13 20:06:22.345307+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	e8fb18ed-8c01-451f-bc63-2567e08769dd	0.125	2025-11-13 20:06:22.346097+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	6675f374-dd03-41c2-8796-7e81999cc075	0.125	2025-11-13 20:06:22.346751+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	20994d2d-564a-48b6-b508-1bc4ca91ba20	0.125	2025-11-13 20:06:22.347414+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	1a161ca5-68e2-4c97-8850-85f7c80aac24	0.125	2025-11-13 20:06:22.348077+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	dec0deaf-d9b0-4823-ac49-811fc893abde	0.125	2025-11-13 20:06:22.34871+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	448fef63-5446-41a9-b188-83a57b2d586f	0.125	2025-11-13 20:06:22.349672+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	6cb12ce7-228f-40f4-87c4-185b110e32b7	0.125	2025-11-13 20:06:22.350332+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	3fe283af-0a1a-4190-95b2-4322066bb104	0.125	2025-11-13 20:06:22.350987+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	0.125	2025-11-13 20:06:22.351648+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	182ddcaa-29bf-4484-8c6c-b18496d59832	0.125	2025-11-13 20:06:22.352363+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	5649bae7-fb7f-436c-a34e-5c085a6a014d	0.125	2025-11-13 20:06:22.353098+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	60d09626-84eb-4770-8ec2-5ae442c65ade	0.1429	2025-11-13 20:06:22.353763+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	273ec2d4-2aa9-47a5-accc-02f852edf5e4	0.1429	2025-11-13 20:06:22.354459+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	1109f07f-9d32-408c-999c-73dbfb2d88cc	0.1429	2025-11-13 20:06:22.355099+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	5779685d-faf6-4d00-a974-9d74c994b0e7	0.1429	2025-11-13 20:06:22.355755+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	b2d3383d-c2ff-4f51-aab4-d2dd4dd22237	0.1429	2025-11-13 20:06:22.35638+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	0.1429	2025-11-13 20:06:22.357008+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	0.1426	2025-11-13 20:06:22.357663+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	a593ae32-e04e-4e0d-be2b-6a440f7f6f64	0.1111	2025-11-13 20:06:22.358278+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	4a48a7a0-a4cb-4d0e-85fc-43836ca316a2	0.1111	2025-11-13 20:06:22.358902+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	bff0139a-f332-433b-b234-d722e796e2a6	0.1111	2025-11-13 20:06:22.359579+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	0.1111	2025-11-13 20:06:22.360343+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	0.1111	2025-11-13 20:06:22.36099+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	e0658139-bb9d-42a0-b2f8-93c63b3b0d98	0.1111	2025-11-13 20:06:22.361675+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	538a4f93-25b2-4b30-8d1e-ece54261d891	0.1111	2025-11-13 20:06:22.362351+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	0.1111	2025-11-13 20:06:22.362941+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	77b28549-ef65-4a72-9f54-8ce4f6cd7439	0.1112	2025-11-13 20:06:22.363573+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	cd52a236-4934-4574-8150-1b5c008d3b9c	80495392-972a-42ec-a6ec-10e777152993	0.3333	2025-11-13 20:06:22.364354+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	cd52a236-4934-4574-8150-1b5c008d3b9c	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	0.3333	2025-11-13 20:06:22.364938+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	cd52a236-4934-4574-8150-1b5c008d3b9c	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	0.3334	2025-11-13 20:06:22.3656+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	8a4f2710-f341-4455-9680-9665e0a584d6	0.1667	2025-11-13 20:06:22.366276+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	d5972321-2d2b-433e-b43b-760522bfd99b	0.1667	2025-11-13 20:06:22.366895+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	20865509-851f-4525-bc9a-fa7111c3c194	0.1667	2025-11-13 20:06:22.367683+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	0.1667	2025-11-13 20:06:22.36834+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	7c217eaf-391d-42b3-983c-2f2ef0b9013c	0.1667	2025-11-13 20:06:22.368957+00
79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	0.1665	2025-11-13 20:06:22.369587+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e9a33c37-4ab9-4e08-99bf-2a99287442d2	c3a0f6ed-5c7e-4c46-b135-555a279f9670	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e9a33c37-4ab9-4e08-99bf-2a99287442d2	b217f16e-51b0-4121-a8e6-8d62ab84cd57	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	e9a33c37-4ab9-4e08-99bf-2a99287442d2	dfec3acf-4e84-4e1f-a5bb-9f5851ace059	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3a0f6ed-5c7e-4c46-b135-555a279f9670	e0247469-39ea-4d8b-8ceb-e56ff8c800e9	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3a0f6ed-5c7e-4c46-b135-555a279f9670	b932e5fc-ef40-4a50-b7f3-f2ea1944cae0	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3a0f6ed-5c7e-4c46-b135-555a279f9670	e704edef-1bbf-4ab8-86df-08cc199575f5	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	c3a0f6ed-5c7e-4c46-b135-555a279f9670	5109e661-34b4-4136-9e88-dbb049e4dd1a	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	b217f16e-51b0-4121-a8e6-8d62ab84cd57	7e801f3f-b8d3-40f9-b251-8b43637ea597	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	b217f16e-51b0-4121-a8e6-8d62ab84cd57	c45425f5-4e5f-4a00-b22d-f4b4f75ffb2a	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	dfec3acf-4e84-4e1f-a5bb-9f5851ace059	228a3e15-0186-487f-b5e9-b8167f2a530f	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	dfec3acf-4e84-4e1f-a5bb-9f5851ace059	bad9a3fc-a0e7-473b-9e77-5973aadd86b4	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	7006ee00-0086-462e-9291-e1dbc4c119f1	23566452-7649-4002-be86-4be63211aa0f	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	7006ee00-0086-462e-9291-e1dbc4c119f1	f4bc3b56-1a4d-4965-9387-55fd28918dd1	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	7c1903dd-7ba0-4293-8ba1-f9d0473ef7b2	be5e4256-5c61-4b43-ace6-2cdef9cd4a17	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	7c1903dd-7ba0-4293-8ba1-f9d0473ef7b2	4f90bd49-8165-431c-bdc9-bf708f56e3d3	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	7c1903dd-7ba0-4293-8ba1-f9d0473ef7b2	b2802bcc-4594-4f29-ac85-6f4543e1ed29	1	2025-11-24 07:34:14.219545+00
c18d6d95-77ed-4b41-a833-dc5cddec74f4	4f90bd49-8165-431c-bdc9-bf708f56e3d3	b2f7d280-4509-46a7-beb4-765a8a857d5c	1	2025-11-24 07:34:14.219545+00
\.


--
-- Data for Name: user_mastery; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.user_mastery (user_id, graph_id, node_id, score, p_l0, p_t, fsrs_state, fsrs_stability, fsrs_difficulty, due_date, last_review, review_log, last_updated) FROM stdin;
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	20865509-851f-4525-bc9a-fa7111c3c194	0.5789473684210527	0.2	0.2	learning	2.3065	2.118103970459016	2025-11-23 03:49:09.524502+00	2025-11-23 03:39:09.524502+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:09.524502+00:00"}]	2025-11-23 03:39:09.524502+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	4e1c060f-f992-4f69-b9af-e8e3cc06ccd6	0.5151828401602274	0.2	0.2	learning	0.7750839828558984	7.394502741279718	2025-11-23 03:40:00.365223+00	2025-11-23 03:39:00.365223+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:15:29.275124+00:00"}, {"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:00.365223+00:00"}]	2025-11-23 03:39:25.720239+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	77b28549-ef65-4a72-9f54-8ce4f6cd7439	0.22994652406417113	0.2	0.2	learning	0.08335671711031604	8.806304468856837	2025-11-23 03:39:48.188326+00	2025-11-23 03:38:48.188326+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:15:19.766564+00:00"}, {"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:38:48.188326+00:00"}]	2025-11-23 03:38:48.188326+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	b9fd2bcd-ef65-4314-b6ff-c38957f7a58e	0.6097560975609756	0.2	0.2	learning	0.24668918777567272	6.402115069296838	2025-11-23 03:48:50.92478+00	2025-11-23 03:38:50.92478+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:14:35.391460+00:00"}, {"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:38:50.924780+00:00"}]	2025-11-23 03:38:50.92478+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	e8fb18ed-8c01-451f-bc63-2567e08769dd	0.22580645161290325	0.2	0.2	learning	0.212	6.4133	2025-11-23 03:40:22.959136+00	2025-11-23 03:39:22.959136+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:22.959136+00:00"}]	2025-11-23 03:39:22.959136+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cea59ff7-fce4-4e75-9b42-3dd42ee38e3f	0.323943661971831	0.2	0.2	learning	0.7750839828558984	7.394502741279718	2025-11-23 03:40:04.75092+00	2025-11-23 03:39:04.75092+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:15:23.268597+00:00"}, {"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:04.750920+00:00"}]	2025-11-23 03:39:04.75092+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	6675f374-dd03-41c2-8796-7e81999cc075	0.22580645161290325	0.2	0.2	learning	0.212	6.4133	2025-11-23 03:40:29.761121+00	2025-11-23 03:39:29.761121+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:29.761121+00:00"}]	2025-11-23 03:39:29.761121+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	dc8d2ccd-60b2-41b8-8b68-fa10f2ce8183	0.6097560975609756	0.2	0.2	learning	0.24668918777567272	6.402115069296838	2025-11-23 03:48:56.554602+00	2025-11-23 03:38:56.554602+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:15:26.429833+00:00"}, {"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:38:56.554602+00:00"}]	2025-11-23 03:38:56.554602+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	538a4f93-25b2-4b30-8d1e-ece54261d891	0.5789473684210527	0.2	0.2	learning	2.3065	2.118103970459016	2025-11-23 03:49:11.934312+00	2025-11-23 03:39:11.934312+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:11.934312+00:00"}]	2025-11-23 03:39:11.934312+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	bed1e3d1-1c3e-4260-860b-6984b797eafb	0.323943661971831	0.2	0.2	learning	0.7750839828558984	7.394502741279718	2025-11-23 03:39:58.417346+00	2025-11-23 03:38:58.417346+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:15:34.710050+00:00"}, {"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:38:58.417346+00:00"}]	2025-11-23 03:38:58.417346+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1109f07f-9d32-408c-999c-73dbfb2d88cc	0.5789473684210527	0.2	0.2	learning	2.3065	2.118103970459016	2025-11-23 03:49:20.018615+00	2025-11-23 03:39:20.018615+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:20.018615+00:00"}]	2025-11-23 03:39:20.018615+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	1255712f-8dd1-4ab8-85b4-1faf7610c1b5	0.5789473684210527	0.2	0.2	learning	2.3065	2.118103970459016	2025-11-23 03:49:07.301571+00	2025-11-23 03:39:07.301571+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:07.301571+00:00"}]	2025-11-23 03:39:07.301571+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	292ffe16-e4f2-49ac-acd9-f1aa726bd35b	0.33985797916053895	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:11.926893+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5ef58b93-a72e-49ba-bf69-4dd5315f56d7	0.9162270906294265	0.2	0.2	learning	2.3065	2.111214235785395	2025-11-23 03:49:02.494158+00	2025-11-23 03:39:02.494158+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:14:29.449905+00:00"}, {"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:02.494158+00:00"}]	2025-11-23 03:39:11.926893+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	c2d4b33a-de36-45c7-8a40-e8db54c4ec0d	0.22580645161290325	0.2	0.2	learning	0.212	6.4133	2025-11-23 03:40:16.345771+00	2025-11-23 03:39:16.345771+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:16.345771+00:00"}]	2025-11-23 03:39:16.345771+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	60d09626-84eb-4770-8ec2-5ae442c65ade	0.22580645161290325	0.2	0.2	learning	0.212	6.4133	2025-11-23 03:40:31.847572+00	2025-11-23 03:39:31.847572+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:31.847572+00:00"}]	2025-11-23 03:39:31.847572+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	5779685d-faf6-4d00-a974-9d74c994b0e7	0.7445006902899218	0.2	0.2	learning	0.24668918777567272	6.402115069296838	2025-11-23 03:48:43.866475+00	2025-11-23 03:38:43.866475+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:15:32.442531+00:00"}, {"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:38:43.866475+00:00"}]	2025-11-23 03:39:20.013119+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3fe283af-0a1a-4190-95b2-4322066bb104	0.5789473684210527	0.2	0.2	learning	2.3065	2.118103970459016	2025-11-23 03:49:25.726532+00	2025-11-23 03:39:25.726532+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:25.726532+00:00"}]	2025-11-23 03:39:25.726532+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	80495392-972a-42ec-a6ec-10e777152993	0.5789473684210527	0.2	0.2	learning	2.3065	2.118103970459016	2025-11-23 03:49:33.834538+00	2025-11-23 03:39:33.834538+00	[{"rating": 3, "state_after": "learning", "review_datetime": "2025-11-23T03:39:33.834538+00:00"}]	2025-11-23 03:39:33.834538+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	43bd532e-c53d-4669-9d44-365ff564c308	0.21176627607266002	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:25.720239+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	a7fa63f8-cff2-4dcd-8748-d456b669b014	0.1594445706497047	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:29.754756+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d0fb6dbc-6b0b-4391-aa92-98b587aca876	0.36918743097296103	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:31.840584+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	324c4f78-f6eb-4ec0-a68a-a71d6f1d8f98	0.6298122049527518	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:33.827962+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	3ceb2e87-78aa-4edc-9f62-013c205c682e	0.31150503799092083	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:33.827962+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	40a0cce9-df72-4721-b303-aa264a89d0e7	0.34789478475621216	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:33.827962+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	9f26f5d3-b1c4-4fb6-896b-e7fd6fda5f97	0.4177812745869394	0.2	0.2	learning	0.212	6.4133	2025-11-23 03:40:27.768545+00	2025-11-23 03:39:27.768545+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:39:27.768545+00:00"}]	2025-11-23 03:39:33.827962+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	cd52a236-4934-4574-8150-1b5c008d3b9c	0.44092284529777354	0.2	0.2	learning	\N	\N	\N	\N	[]	2025-11-23 03:39:33.827962+00
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	79f6869b-a9d1-4965-b864-dafd6a3faa6d	d2d79951-5ba9-48e5-a52e-a4e3180a3b62	0.32607435087945363	0.2	0.2	learning	0.08335671711031604	8.806304468856837	2025-11-23 03:39:54.26273+00	2025-11-23 03:38:54.26273+00	[{"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:14:40.826350+00:00"}, {"rating": 1, "state_after": "learning", "review_datetime": "2025-11-23T03:38:54.262730+00:00"}]	2025-11-23 03:39:33.827962+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: aether_user
--

COPY public.users (id, name, email, hashed_password, is_active, is_admin, oauth_provider, oauth_id, created_at, updated_at, refresh_token, reset_token, reset_token_expires_at) FROM stdin;
18c781b6-83ce-477a-9cd8-d7a83683f96d	Success User	success@example.com	$2b$12$UvbRAGxzEyyzTle3hpQ9q..d78Z8MofHNzbkekMlRGTwohUAuxcDS	t	f	\N	\N	2025-11-12 06:09:09.280715+00	2025-11-12 06:09:09.280715+00	\N	\N	\N
3e6d3fc2-4553-4d15-8faa-b147d43b3c1a	Test User	test2@gmail.com	$2b$12$i0iGACV3XDVEfTvT7ZVLQ.LaJ4Nyv.rJPrBAaYyVQRIqqMaY1RrBy	t	f	\N	\N	2025-11-12 06:09:14.899134+00	2025-11-12 06:09:14.899134+00	\N	\N	\N
39dbb758-eb18-4909-8144-ab819d687a73	Test User	test@gmail.com	$2b$12$dtDm3ERk9sySuEbD4.rd1uEYsqwERwvwXdW5FWcpFErLehqWV.GW.	t	f	\N	\N	2025-11-12 06:10:38.886679+00	2025-11-12 06:31:24.737306+00	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjM1MzM4NzcsInN1YiI6IjM5ZGJiNzU4LWViMTgtNDkwOS04MTQ0LWFiODE5ZDY4N2E3MyIsImlhdCI6MTc2MjkyOTA3NywianRpIjoiNjI3YTgxMmQtOTViNy00MTBiLTgzMTctZjNhYTQ2ZDZkNmE0In0.RkYWdlSwfzYImmbqgwGm75bi3TCUtoFbxBLhfjVtbfA	59623c5970e33ed35d9142dacf98bbaa036a8c6f813f2c3af4b1fa24bb28df73	2025-11-12 07:31:24.738284+00
bc7dd8cd-ec52-4082-bc39-825a7e72b294	Admin User	admin@example.com	dummy_hash	t	t	\N	\N	2025-11-13 20:05:45.979505+00	2025-11-13 20:05:45.979505+00	\N	\N	\N
cb4fb889-7d66-43f5-affb-a232cb50e4d6	Test User	test@test.com	$2b$12$SViQfWc1ex/WQCqrzIxweeY0LoElilZWRbsmDZvHMX76ganKoG.Cu	t	f	\N	\N	2025-11-24 01:36:15.03303+00	2025-11-24 01:36:28.49424+00	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjQ1NTI5ODgsInN1YiI6ImNiNGZiODg5LTdkNjYtNDNmNS1hZmZiLWEyMzJjYjUwZTRkNiIsImlhdCI6MTc2Mzk0ODE4OCwianRpIjoiNWUxMTE0ZmUtZTRjMS00ZTg3LTgyM2ItYmEyNWJlNDIzZTMwIn0.8p3Nljy7bp9nPe5FJvEdeNmYlPZkgiKvz-PCA3Br8RQ	\N	\N
f84bcc2c-ea90-48a3-8ad9-479302bbbdbf	Naicheng Deng	test@example.com	$2b$12$eRg2PKoodCCTL355BtRp3.k53EUvkncNk4F0gmByHRIqLeoPNfw8S	t	f	\N	\N	2025-11-07 02:51:05.455563+00	2025-11-24 09:30:54.488318+00	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjQ1ODE0NTQsInN1YiI6ImY4NGJjYzJjLWVhOTAtNDhhMy04YWQ5LTQ3OTMwMmJiYmRiZiIsImlhdCI6MTc2Mzk3NjY1NCwianRpIjoiZjdkOWU3ZGItOGVlMC00OTIxLWFmYjctMjc2ZmM2MWFmZDI4In0.Ry6brQj8Cmp7kjZfKBe3uXAAIhanT-uRQqr-pQ3OVp4	\N	\N
\.


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- Name: enrollments enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_pkey PRIMARY KEY (id);


--
-- Name: graph_enrollments graph_enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.graph_enrollments
    ADD CONSTRAINT graph_enrollments_pkey PRIMARY KEY (id);


--
-- Name: knowledge_graphs knowledge_graphs_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_graphs
    ADD CONSTRAINT knowledge_graphs_pkey PRIMARY KEY (id);


--
-- Name: knowledge_nodes knowledge_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT knowledge_nodes_pkey PRIMARY KEY (id);


--
-- Name: prerequisites prerequisites_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.prerequisites
    ADD CONSTRAINT prerequisites_pkey PRIMARY KEY (graph_id, from_node_id, to_node_id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_attempts quiz_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_pkey PRIMARY KEY (attempt_id);


--
-- Name: submission_answers submission_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.submission_answers
    ADD CONSTRAINT submission_answers_pkey PRIMARY KEY (id);


--
-- Name: subtopics subtopics_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.subtopics
    ADD CONSTRAINT subtopics_pkey PRIMARY KEY (graph_id, parent_node_id, child_node_id);


--
-- Name: knowledge_nodes uq_graph_node_str; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT uq_graph_node_str UNIQUE (graph_id, node_id_str);


--
-- Name: knowledge_nodes uq_graph_node_uuid; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT uq_graph_node_uuid UNIQUE (graph_id, id);


--
-- Name: knowledge_graphs uq_owner_graph_slug; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_graphs
    ADD CONSTRAINT uq_owner_graph_slug UNIQUE (owner_id, slug);


--
-- Name: graph_enrollments uq_user_graph_enrollment; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.graph_enrollments
    ADD CONSTRAINT uq_user_graph_enrollment UNIQUE (user_id, graph_id);


--
-- Name: user_mastery user_mastery_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.user_mastery
    ADD CONSTRAINT user_mastery_pkey PRIMARY KEY (user_id, graph_id, node_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_enrollment_active; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_enrollment_active ON public.graph_enrollments USING btree (user_id, is_active);


--
-- Name: idx_enrollment_graph; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_enrollment_graph ON public.graph_enrollments USING btree (graph_id);


--
-- Name: idx_enrollment_user; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_enrollment_user ON public.graph_enrollments USING btree (user_id);


--
-- Name: idx_graphs_owner; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_graphs_owner ON public.knowledge_graphs USING btree (owner_id);


--
-- Name: idx_graphs_public_template; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_graphs_public_template ON public.knowledge_graphs USING btree (is_public, is_template);


--
-- Name: idx_graphs_tags; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_graphs_tags ON public.knowledge_graphs USING gin (tags);


--
-- Name: idx_mastery_due; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_mastery_due ON public.user_mastery USING btree (user_id, graph_id, due_date);


--
-- Name: idx_mastery_graph_node; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_mastery_graph_node ON public.user_mastery USING btree (graph_id, node_id);


--
-- Name: idx_mastery_user_graph; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_mastery_user_graph ON public.user_mastery USING btree (user_id, graph_id);


--
-- Name: idx_nodes_graph; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_nodes_graph ON public.knowledge_nodes USING btree (graph_id);


--
-- Name: idx_nodes_graph_id; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_nodes_graph_id ON public.knowledge_nodes USING btree (graph_id, id);


--
-- Name: idx_nodes_graph_str; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_nodes_graph_str ON public.knowledge_nodes USING btree (graph_id, node_id_str);


--
-- Name: idx_nodes_level; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_nodes_level ON public.knowledge_nodes USING btree (graph_id, level);


--
-- Name: idx_prereq_graph_from; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_prereq_graph_from ON public.prerequisites USING btree (graph_id, from_node_id);


--
-- Name: idx_prereq_graph_to; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_prereq_graph_to ON public.prerequisites USING btree (graph_id, to_node_id);


--
-- Name: idx_questions_graph; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_questions_graph ON public.questions USING btree (graph_id);


--
-- Name: idx_questions_graph_node; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_questions_graph_node ON public.questions USING btree (graph_id, node_id);


--
-- Name: idx_subtopic_graph_child; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_subtopic_graph_child ON public.subtopics USING btree (graph_id, child_node_id);


--
-- Name: idx_subtopic_graph_parent; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_subtopic_graph_parent ON public.subtopics USING btree (graph_id, parent_node_id);


--
-- Name: idx_users_reset_token; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX idx_users_reset_token ON public.users USING btree (reset_token);


--
-- Name: ix_courses_name; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_courses_name ON public.courses USING btree (name);


--
-- Name: ix_knowledge_graphs_is_public; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_knowledge_graphs_is_public ON public.knowledge_graphs USING btree (is_public);


--
-- Name: ix_knowledge_graphs_is_template; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_knowledge_graphs_is_template ON public.knowledge_graphs USING btree (is_template);


--
-- Name: ix_knowledge_graphs_slug; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_knowledge_graphs_slug ON public.knowledge_graphs USING btree (slug);


--
-- Name: ix_knowledge_nodes_dependents_count; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_knowledge_nodes_dependents_count ON public.knowledge_nodes USING btree (dependents_count);


--
-- Name: ix_knowledge_nodes_level; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_knowledge_nodes_level ON public.knowledge_nodes USING btree (level);


--
-- Name: ix_knowledge_nodes_node_id_str; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_knowledge_nodes_node_id_str ON public.knowledge_nodes USING btree (node_id_str);


--
-- Name: ix_user_mastery_due_date; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_user_mastery_due_date ON public.user_mastery USING btree (due_date);


--
-- Name: ix_users_refresh_token; Type: INDEX; Schema: public; Owner: aether_user
--

CREATE INDEX ix_users_refresh_token ON public.users USING btree (refresh_token);


--
-- Name: prerequisites trg_prerequisites_delete; Type: TRIGGER; Schema: public; Owner: aether_user
--

CREATE TRIGGER trg_prerequisites_delete AFTER DELETE ON public.prerequisites REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT EXECUTE FUNCTION public.trigger_topology_on_delete();


--
-- Name: prerequisites trg_prerequisites_insert; Type: TRIGGER; Schema: public; Owner: aether_user
--

CREATE TRIGGER trg_prerequisites_insert AFTER INSERT ON public.prerequisites REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT EXECUTE FUNCTION public.trigger_topology_on_insert();


--
-- Name: prerequisites trg_prerequisites_update; Type: TRIGGER; Schema: public; Owner: aether_user
--

CREATE TRIGGER trg_prerequisites_update AFTER UPDATE ON public.prerequisites REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT EXECUTE FUNCTION public.trigger_topology_on_update();


--
-- Name: enrollments enrollments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- Name: enrollments enrollments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: graph_enrollments graph_enrollments_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.graph_enrollments
    ADD CONSTRAINT graph_enrollments_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id) ON DELETE CASCADE;


--
-- Name: graph_enrollments graph_enrollments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.graph_enrollments
    ADD CONSTRAINT graph_enrollments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: knowledge_graphs knowledge_graphs_forked_from_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_graphs
    ADD CONSTRAINT knowledge_graphs_forked_from_id_fkey FOREIGN KEY (forked_from_id) REFERENCES public.knowledge_graphs(id) ON DELETE SET NULL;


--
-- Name: knowledge_graphs knowledge_graphs_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_graphs
    ADD CONSTRAINT knowledge_graphs_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: knowledge_nodes knowledge_nodes_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.knowledge_nodes
    ADD CONSTRAINT knowledge_nodes_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id) ON DELETE CASCADE;


--
-- Name: prerequisites prerequisites_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.prerequisites
    ADD CONSTRAINT prerequisites_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id) ON DELETE CASCADE;


--
-- Name: prerequisites prerequisites_graph_id_from_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.prerequisites
    ADD CONSTRAINT prerequisites_graph_id_from_node_id_fkey FOREIGN KEY (graph_id, from_node_id) REFERENCES public.knowledge_nodes(graph_id, id) ON DELETE CASCADE;


--
-- Name: prerequisites prerequisites_graph_id_to_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.prerequisites
    ADD CONSTRAINT prerequisites_graph_id_to_node_id_fkey FOREIGN KEY (graph_id, to_node_id) REFERENCES public.knowledge_nodes(graph_id, id) ON DELETE CASCADE;


--
-- Name: questions questions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: questions questions_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id) ON DELETE CASCADE;


--
-- Name: questions questions_graph_id_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_graph_id_node_id_fkey FOREIGN KEY (graph_id, node_id) REFERENCES public.knowledge_nodes(graph_id, id) ON DELETE CASCADE;


--
-- Name: quiz_attempts quiz_attempts_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- Name: quiz_attempts quiz_attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: submission_answers submission_answers_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.submission_answers
    ADD CONSTRAINT submission_answers_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id);


--
-- Name: submission_answers submission_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.submission_answers
    ADD CONSTRAINT submission_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id);


--
-- Name: submission_answers submission_answers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.submission_answers
    ADD CONSTRAINT submission_answers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: subtopics subtopics_graph_id_child_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.subtopics
    ADD CONSTRAINT subtopics_graph_id_child_node_id_fkey FOREIGN KEY (graph_id, child_node_id) REFERENCES public.knowledge_nodes(graph_id, id) ON DELETE CASCADE;


--
-- Name: subtopics subtopics_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.subtopics
    ADD CONSTRAINT subtopics_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id) ON DELETE CASCADE;


--
-- Name: subtopics subtopics_graph_id_parent_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.subtopics
    ADD CONSTRAINT subtopics_graph_id_parent_node_id_fkey FOREIGN KEY (graph_id, parent_node_id) REFERENCES public.knowledge_nodes(graph_id, id) ON DELETE CASCADE;


--
-- Name: user_mastery user_mastery_graph_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.user_mastery
    ADD CONSTRAINT user_mastery_graph_id_fkey FOREIGN KEY (graph_id) REFERENCES public.knowledge_graphs(id) ON DELETE CASCADE;


--
-- Name: user_mastery user_mastery_graph_id_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.user_mastery
    ADD CONSTRAINT user_mastery_graph_id_node_id_fkey FOREIGN KEY (graph_id, node_id) REFERENCES public.knowledge_nodes(graph_id, id) ON DELETE CASCADE;


--
-- Name: user_mastery user_mastery_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aether_user
--

ALTER TABLE ONLY public.user_mastery
    ADD CONSTRAINT user_mastery_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict MFKxrne8z3qoPvwfLaro1CsdPNXverztssByckeHXk65SZ8QdX4vebOPYWiNkN6

