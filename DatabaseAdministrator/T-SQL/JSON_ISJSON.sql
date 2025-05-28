declare @json_items nvarchar(max)
set @json_items = '{
   "name":"first_name last_name",
   "job":"business analysis",
   "salary":8117,
   "relocation":[
      {
	   "first_place":"alex",
	   "nickname":"gomora"
	  },
	   {
	   "second_place":"thembisa",
	   "nickname":"iviory park ext 2"
	  }
   ]
}'



select ISJSON(@json_items)

-- scripts syntax

-- select JSON_VALUE(where, '$.what') as allias
select json_value(@json_items, '$.name') as fullname
--SELECT * 
--FROM OPENJSON(source_json, path_to_array)
--WITH (
--    column1 datatype '$.json_path',
--    column2 datatype '$.json_path',
--    ...
--)

SELECT *
FROM OPENJSON(@json_items, '$.relocation')
WITH (
    first_place VARCHAR(100),
    second_place VARCHAR(100),
    nickname VARCHAR(100)
)

DECLARE @json NVARCHAR(MAX) = '{
  "relocation": [
    { "first_place": "alex", "nickname": "gomora" },
    { "second_place": "thembisa", "nickname": "iviory park ext 2" }
  ]
}'

SELECT *
FROM OPENJSON(@json, '$.relocation')
WITH (
    first_place NVARCHAR(100) '$.first_place',
    second_place NVARCHAR(100) '$.second_place',
    nickname NVARCHAR(100) '$.nickname'
)

SELECT JSON_VALUE(@json_items, '$.relocation[1].second_place')
select json_value(@json_items,'strict $.relocation[1].nickname')

set @json_items=  json_modify(@json_items,'strict $.relocation[1].nickname', json_query('{"nickname":"ivory park ext 4"}')) -- this is wrong 
SET @json_items = JSON_MODIFY(@json_items, '$.relocation[1].nickname', 'ivory park ext 3') -- here is the correct version

select json_value(@json_items,'strict $.relocation[1].nickname')