--
-- PostgreSQL database dump
--

\restrict jIOhIr2aGJ329SUoCgu3d2lIJAC18NxdnQLdV9M2wjCMimxJOGVovRzSiLr3q6i

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

-- Started on 2026-05-07 18:37:37

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- TOC entry 220 (class 1259 OID 16431)
-- Name: forrajeo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forrajeo (
    id integer NOT NULL,
    nombre character varying(100),
    descripcion text,
    ph_min double precision,
    ph_max double precision,
    humedad_min double precision,
    humedad_max double precision,
    altitud_min integer,
    altitud_max integer,
    temp_min integer,
    temp_max integer
);


ALTER TABLE public.forrajeo OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16430)
-- Name: forrajeo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.forrajeo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.forrajeo_id_seq OWNER TO postgres;

--
-- TOC entry 5013 (class 0 OID 0)
-- Dependencies: 219
-- Name: forrajeo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.forrajeo_id_seq OWNED BY public.forrajeo.id;


--
-- TOC entry 4856 (class 2604 OID 16434)
-- Name: forrajeo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forrajeo ALTER COLUMN id SET DEFAULT nextval('public.forrajeo_id_seq'::regclass);


--
-- TOC entry 5007 (class 0 OID 16431)
-- Dependencies: 220
-- Data for Name: forrajeo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forrajeo (id, nombre, descripcion, ph_min, ph_max, humedad_min, humedad_max, altitud_min, altitud_max, temp_min, temp_max) FROM stdin;
1	pasto	curiquitaca	5	4	2	5	2500	1000	25	40
2	Pasto Elefante	Forraje tropical de alta producción	5.5	7	60	80	0	1800	20	35
3	Alfalfa	Leguminosa rica en proteína para ganado	6	7.5	50	70	1000	3200	15	28
4	Brachiaria Decumbens	Pasto resistente a sequías y suelos pobres	4.5	6.5	40	75	0	2000	22	36
5	Brachiaria Brizantha	Forraje tropical para pastoreo intensivo	5	6.8	45	80	0	2200	20	35
6	Pasto Guinea	Pasto tropical de rápido crecimiento	5	7	55	80	0	1800	22	34
7	Pasto Kikuyo	Muy usado en lechería de clima frío	5.5	7	65	90	1800	3200	10	22
8	Ray Grass Inglés	Ideal para zonas frías y húmedas	5.8	7.2	65	85	1800	3200	8	20
9	Ray Grass Italiano	Forraje de alta digestibilidad	5.8	7	60	85	1500	3000	10	22
10	Maíz Forrajero	Utilizado principalmente para ensilaje	5.5	7	55	80	0	2500	18	32
11	Sorgo Forrajero	Alta tolerancia al calor y sequía	5	7	45	70	0	2200	20	38
12	Avena Forrajera	Excelente producción en clima frío	5.8	7.3	60	85	1500	3200	8	20
13	Trébol Blanco	Leguminosa fijadora de nitrógeno	6	7.5	55	75	1200	2800	12	24
14	Trébol Rojo	Forraje de buena calidad nutricional	6	7.2	50	75	1200	3000	10	24
15	Canavalia	Leguminosa usada como cobertura y forraje	5.5	7.5	50	80	0	1800	20	32
16	Leucaena	Árbol forrajero rico en proteína	5.5	7.5	45	75	0	1800	22	35
17	Botón de Oro	Forraje arbustivo de alta proteína	5	7	50	85	0	2500	18	30
18	King Grass	Variedad de pasto de gran rendimiento	5.5	7	60	85	0	1800	22	35
19	Pasto Estrella	Pasto tropical resistente al pastoreo	5	6.8	50	80	0	2000	22	36
20	Pasto Tanner	Pasto adaptado a suelos húmedos	4.8	6.5	70	90	0	1500	22	34
21	Pasto Pangola	Excelente digestibilidad para bovinos	5	7	55	80	0	1800	20	35
22	Moringa	Árbol forrajero con alto contenido nutricional	5	7.5	40	70	0	1500	24	38
23	Cratylia	Leguminosa arbustiva para sistemas silvopastoriles	5	7	50	75	0	2000	20	34
24	Pennisetum Purpureum	Pasto tropical para corte	5.5	7	60	85	0	1800	22	35
25	Maralfalfa	Pasto híbrido de alta producción	5.5	7	60	85	0	2000	20	35
26	Caña Forrajera	Utilizada como suplemento energético	5	7.5	55	80	0	1800	22	36
27	Centrosema	Leguminosa tropical rastrera	5	6.8	55	85	0	1800	20	34
28	Desmodium	Leguminosa de buena digestibilidad	5.5	7	50	80	0	2200	18	32
29	Guandul	Leguminosa arbustiva resistente	5	7.5	45	75	0	2000	20	35
30	Caupí Forrajero	Leguminosa anual tropical	5	7	50	75	0	1800	22	34
31	Pasto Bermuda	Pasto resistente y de rápido crecimiento	5	7	45	80	0	2200	20	36
32	Pasto Alemán	Forraje adaptado a zonas húmedas	5	6.5	70	95	0	1200	22	34
33	Pasto Jaragua	Muy resistente a altas temperaturas	4.8	6.8	40	70	0	1800	24	38
34	Pasto Angleton	Forraje tropical para pastoreo	5	6.8	45	75	0	1800	22	36
35	Pasto Toledo	Variedad mejorada de brachiaria	5	6.8	50	80	0	2200	20	35
36	Pasto Mombasa	Alta producción de biomasa	5	7	55	80	0	1800	22	35
37	Pasto Tanzania	Excelente calidad nutricional	5	7	55	80	0	1800	22	35
38	Pasto Mulato II	Híbrido resistente y nutritivo	5	6.8	50	80	0	2200	20	36
39	Pasto Humidícola	Ideal para terrenos inundables	4.5	6.5	75	95	0	1200	22	34
40	Pasto Rhodes	Muy usado en sistemas ganaderos	5	7	45	75	0	2200	20	36
41	Pasto Buffel	Excelente resistencia a sequía	5	7.5	35	65	0	1800	24	40
42	Soja Forrajera	Fuente rica en proteína vegetal	5.8	7.2	50	75	0	1800	20	32
43	Vicia	Leguminosa usada en mezcla con gramíneas	6	7.5	55	80	1200	3000	10	24
44	Cebada Forrajera	Excelente para climas templados	6	7.5	50	75	1500	3200	8	20
45	Festuca	Gramínea perenne para clima frío	5.5	7	60	85	1800	3200	8	20
46	Dactylis Glomerata	Pasto resistente al frío	5.5	7	55	80	1800	3200	8	20
47	Lotus Corniculatus	Leguminosa adaptada a zonas frías	5.5	7.5	50	75	1500	3200	10	24
48	Pasto Sudan	Híbrido de rápido crecimiento	5	7	45	70	0	1800	22	38
49	Arachis Pintoi	Leguminosa rastrera tropical	5	6.8	55	85	0	1800	20	34
50	Calliandra	Arbusto forrajero rico en proteína	5.5	7.5	50	80	0	2500	18	30
51	Yuca Forrajera	Raíz y follaje utilizados en alimentación animal	5	7	45	75	0	1800	22	36
52	Nacedero	Árbol forrajero usado en sistemas silvopastoriles	5	7	55	85	0	2200	18	32
\.


--
-- TOC entry 5014 (class 0 OID 0)
-- Dependencies: 219
-- Name: forrajeo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.forrajeo_id_seq', 52, true);


--
-- TOC entry 4858 (class 2606 OID 16439)
-- Name: forrajeo forrajeo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forrajeo
    ADD CONSTRAINT forrajeo_pkey PRIMARY KEY (id);


-- Completed on 2026-05-07 18:37:38

--
-- PostgreSQL database dump complete
--

\unrestrict jIOhIr2aGJ329SUoCgu3d2lIJAC18NxdnQLdV9M2wjCMimxJOGVovRzSiLr3q6i

