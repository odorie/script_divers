\set ON_ERROR_STOP 1
DROP TABLE IF EXISTS municipality_90;
CREATE TABLE municipality_90 AS (SELECT pk, name, insee FROM municipality WHERE insee LIKE '90%');
DROP TABLE IF EXISTS postcode_90;
CREATE TABLE postcode_90 AS (SELECT p.pk, p.code, p.complement, p.municipality_id FROM postcode p, municipality_90 m WHERE p.municipality_id=m.pk);
DROP TABLE IF EXISTS group_90;
CREATE TABLE group_90 AS (SELECT g.pk, g.name, g.municipality_id FROM "group" g, municipality_90 m WHERE g.municipality_id=m.pk AND g.name IS NOT NULL);
DROP TABLE IF EXISTS housenumber_90;
CREATE TABLE housenumber_90 AS (SELECT h.pk, h.number, h.ordinal, h.parent_id FROM housenumber h, group_90 g WHERE h.parent_id=g.pk AND h.number IS NOT NULL);
UPDATE housenumber_90 SET ordinal='' WHERE ordinal is null;
DROP TABLE IF EXISTS position_90;
CREATE TABLE position_90 AS 
(SELECT st_x(p.center) as X, st_y(p.center) as Y, p.housenumber_id  FROM position p, housenumber_90 h WHERE p.housenumber_id=h.pk and st_x(p.center)=
(select min(st_x(p2.center)) from position p2 where p2.housenumber_id=h.pk group by p2.housenumber_id));
DROP TABLE IF EXISTS level2point_90;
CREATE TABLE level2point_90 (streetName text, streetAttribute text, endNumberL text, startNumberL text, endNumberR text, startNumberR text, cityName text, cityAttribute text, cityUniqueId text, X1 text, Y1 text, X2 text, Y2 text, geom text);
INSERT INTO level2point_90 (streetName, cityName, cityUniqueId, X2, Y2) SELECT h.number||''||h.ordinal||' '||g.name, m.name, m.insee, p.X, p.Y FROM municipality_90 m, group_90 g, housenumber_90 h, position_90 p WHERE p.housenumber_id=h.pk and h.parent_id=g.pk and g.municipality_id=m.pk and g.name is not null and h.number is not null;
\COPY level2point_90 TO './level2point_90.txt';
