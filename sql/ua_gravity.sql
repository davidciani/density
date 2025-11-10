-- View: public.ua_gravity

-- DROP VIEW public.ua_gravity;

CREATE OR REPLACE VIEW public.ua_gravity
 AS
 WITH edges AS (
         SELECT a.ua AS ua_from,
            b.ua AS ua_to,
            a.basename AS name_from,
            b.basename AS name_to,
            a.pop100 AS pop_from,
            b.pop100 AS pop_to,
            st_distance(a.geometry::geography, b.geometry::geography) / 1000::double precision AS distance_km,
            st_makeline(a.geometry, b.geometry) AS geometry
           FROM ua_popcenter a
             CROSS JOIN ua_popcenter b
          WHERE a.ua <> b.ua
        )
 SELECT row_number() OVER (ORDER BY ua_from, ua_to) AS id,
    ua_from,
    ua_to,
    name_from,
    name_to,
    pop_from,
    pop_to,
    distance_km,
    (pop_from * pop_to)::double precision / (distance_km ^ 2::double precision) / 1000::double precision AS gravity,
    geometry::geometry(LineString,4269) AS geom
   FROM edges
  WHERE ua_from < ua_to;

ALTER TABLE public.ua_gravity
    OWNER TO david;

