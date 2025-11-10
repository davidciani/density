-- View: public.cbsa_gravity

-- DROP VIEW public.cbsa_gravity;

CREATE OR REPLACE VIEW public.cbsa_gravity
 AS
 WITH edges AS (
         SELECT a.cbsa AS cbsa_from,
            b.cbsa AS cbsa_to,
            a.basename AS name_from,
            b.basename AS name_to,
            a.pop100 AS pop_from,
            b.pop100 AS pop_to,
            st_distance(a.geometry::geography, b.geometry::geography) / 1000::double precision AS distance_km,
            st_makeline(a.geometry, b.geometry) AS geometry
           FROM cbsa_w_popcenter a
             CROSS JOIN cbsa_w_popcenter b
          WHERE a.cbsa <> b.cbsa
        )
 SELECT row_number() OVER (ORDER BY cbsa_from, cbsa_to) AS id,
    cbsa_from,
    cbsa_to,
    name_from,
    name_to,
    pop_from,
    pop_to,
    distance_km,
    (pop_from * pop_to)::double precision / (distance_km ^ 2::double precision) / 1000::double precision AS gravity,
    geometry::geometry(LineString,4269) AS geom
   FROM edges;

ALTER TABLE public.cbsa_gravity
    OWNER TO david;

