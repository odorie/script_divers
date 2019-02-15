 insert into client(id,client_id,name,user_id,client_secret,redirect_uris,grant_type,is_confidential) values ('1','3db7042c-7bb9-4f9a-8140-d0be443aacd2','test',1,'secret','{http://localhost/authorize}','client_credentials',false);
 insert into client(id,client_id,name,user_id,client_secret,redirect_uris,grant_type,is_confidential) values ('1','3db7042c-7bb9-4f9a-8140-d0be443aacd2','test',1,'secret','{http://localhost/authorize}','client_credentials',false);
insert into session(client_id,contributor_type) values (1,'ign');

insert into municipality(id,version,created_at,created_by_id,modified_at,modified_by_id,name,insee) values ('1',1,'2019-02-06',1,'2019-02-06',1,'COMMUNE 90001','90001');

insert into "group"(id,version,created_at,created_by_id,modified_at,modified_by_id,name,kind,municipality_id) values ('1',1,'2019-02-06',1,'2019-02-06',1,'RUE UN','way',1);

insert into housenumber(id,version,created_at,created_by_id,modified_at,modified_by_id,number,parent_id) values (1,1,'2019-02-06',1,'2019-02-06',1,'1',1);
