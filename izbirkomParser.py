import requests
import json
import sys
import time
import csv

url_base = 'http://www.st-petersburg.vybory.izbirkom.ru/region/st-petersburg'

params = (
    ('action', 'ikTree'),
    ('region', '78'),
    ('vrn', '27820001006425'), #Видимо id группы/участка
    ('id', '#'),
)

#получаем первоночальное дерево изберательных участков
response = requests.get(url_base, params=params, verify=False)
  
if response.ok:
	decoded_json = json.loads(response.text)
else:
	sys.exit(f'-1 Error request can be not executes status code: {response.status_code}')

#головной элемент: Санкт-Петербургская избирательная комиссия
header_element = {'name': decoded_json[0]['text'],'parent':' '} 

#дочерние элементы головной комиссии
children_elements=[]

#основная коллекция элементов для вывода в файл
main_collection =[header_element]

for child in decoded_json[0]['children']:
    children = {'id': child['id'], 'name': child['text'], 'parent': header_element['name']}
    children_elements.append(children)
    main_collection.append({'name': child['text'], 'parent': header_element['name']})

counter = 1
for child in children_elements:
    print(f'{child["name"]}\tParse children tree {counter}/{len(children_elements)}')
    paramsTwo = (
    ('action', 'ikTree'),
    ('region', '78'),
    ('vrn', child['id']),
    ('onlyChildren', 'true'),
    ('id', child['id']))
   
    counter+=1

    #Для того что бы уменьшить шанс бана спим 0.5 секунды а каждый 10 элемент даем передохнуть на 3 секунд
    time.sleep( 0.5 if counter % 10 != 0 else 3)

    #получаем дочернее дерево для ТИКов
    response = requests.get(url_base, params=paramsTwo, verify=False)

    if response.ok:
        decoded_json_2tree = json.loads(response.text)
        for child_tree2 in decoded_json_2tree:
            children_tree2 ={'name': child_tree2['text'],'parent': child['name'],'parent_id': child['id']}
            main_collection.append({'name': child_tree2['text'],'parent': child['name']})

    else:
        sys.exit(f'-1 Error request can be not executes status code: {response.status_code}')

#save
#сделать Rewrite или пересоздавать файл 
with open('output.tsv','wt') as out_file:
    tsv_writer = csv.DictWriter(out_file,fieldnames = ['name', 'parent'],delimiter='\t')
    tsv_writer.writeheader()
    tsv_writer.writerows(main_collection)
        

sys.exit('Done')

