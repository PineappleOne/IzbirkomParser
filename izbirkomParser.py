#!/usr/bin/python
import argparse
import requests
import json
import sys
import os
import time
import csv
from bs4 import BeautifulSoup


url_base = 'http://www.st-petersburg.vybory.izbirkom.ru/region/st-petersburg'

#главная коллекция из которой генерируется файл
main_collection=[]

#т.к элементы с ФИО и прочими данными невозможно вытянуть через json то прасим HTML
def getAndParseHtml(child):
    
    if not child['id']:
        sys.exit('null id child')
        
    params = (('action', 'ik'),('vrn', child['id']))

    #На всякий случай что бы уменьшить шанс бана спим по 0.5 секунд а каждую 10 итерацию спим 10 (пока работает и без задержки)
    #time.sleep( 0.5 if int(child['id']) % 10 != 0 else 3)

    response = requests.get(url_base,params=params, verify=False)
    soup=BeautifulSoup(response.text,'lxml')
    tables = [[
            [td.get_text(strip=True) for td in tr.find_all('td')] 
            for tr in table.find_all('tr')] 
            for table in soup.find_all('table')]
    
    for fioList in tables[2]:
        if len(fioList)==4:
            main_collection.append({'name':child['name'],'parent':child['parent'],'fio': fioList[1],'post': fioList[2],'whoRec':fioList[3]})

#Функция для получения дерева избирательных участков
def getMainTreeRoot(countLimit):
    params = (
    ('action', 'ikTree'),
    ('region', '78'),
    ('vrn', '27820001006425'), #id группы/участка
    ('id', '#'))               #Root

    response = requests.get(url_base, params=params, verify=False)
  
    if response.ok:
        decoded_json = json.loads(response.text)
    else:
        sys.exit(f'-1 Error request can be not executes status code: {response.status_code}')

    #головной элемент: Санкт-Петербургская избирательная комиссия
    header_element = {'name': decoded_json[0]['text'],'parent':' ', 'id':decoded_json[0]['id']} 
    print('Парсинг головного элемента')
    getAndParseHtml(header_element)

    counter = 0
    
    for child_main in decoded_json[0]['children']:
        main_children = {'id': child_main['id'], 'name': child_main['text'], 'parent': header_element['name']}
        print(f'Парсинг сотрудников :{main_children["name"]}')
        getAndParseHtml(main_children)
        
        paramsTwo = (
        ('action', 'ikTree'),
        ('region', '78'),
        ('vrn', main_children['id']),
        ('onlyChildren', 'true'),
        ('id', main_children['id']))

        #limit
        if countLimit!= -1:
            if counter>=countLimit:
                break
            counter +=1
            
        #получаем дочернее дерево для ТИКов
        response = requests.get(url_base, params=paramsTwo, verify=False)

        if response.ok:
            decoded_json_2tree = json.loads(response.text)
            for child_tree2 in decoded_json_2tree:
            
                children_tree2 ={'name': child_tree2['text'],'parent': main_children['name'], 'id': child_tree2['id']}
                #Парсим HTML для нисших уровнях дерева
                print(f'Парсинг сотрудников :{children_tree2["name"]}')
                getAndParseHtml(children_tree2)
                
        else:
            sys.exit(f'-1 Error request can be not executes status code: {response.status_code}')

#Создаем ТСВ файл
def createTsv(collection,path,fileName):

    if not path:
        filePath=fileName
    else:
        filePath=f'{path}/{fileName}'

        if not os.path.exists(filePath):
            os.makedirs(path)

    with open(f'{filePath}.tsv','w', newline='') as out_file:
        tsv_writer = csv.DictWriter(out_file,fieldnames = ['name', 'parent','fio','post','whoRec'],delimiter='\t')
        tsv_writer.writeheader()
        tsv_writer.writerows(collection)
        
        
if __name__ =="__main__":

    #Лимит парса пунктов главного дерева (ТИК)
    countLimitParse = -1
    path=''
    fileName='output'

    parser = argparse.ArgumentParser(description= "Parser SPB izbirkom")
    parser.add_argument('-l','--limit', action='store', dest='limit', help='limit max parse TIKs')
    parser.add_argument('-p','--path', action='store', dest='path', help='path output file')
    parser.add_argument('-f','--file', action='store', dest='fileName', help='file name')
    
    args = parser.parse_args()
 
    if args.limit!= None:
        countLimitParse = int(args.limit)
    
    if args.path!=None:
        path = args.path
    
    if args.fileName!= None:
        fileName= args.fileName

    print('Старт парсера')
    getMainTreeRoot(countLimitParse)
    
    print('Генерация файла')
    print(f'{path}/{fileName}.tsv')
    createTsv(main_collection,path,fileName)
    
sys.exit('Завершено успешно.')

