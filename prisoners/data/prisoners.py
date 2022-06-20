import json, urllib.request
import psycopg2

def insert_statinstance(status_id):
    cur.execute("INSERT INTO statinstance (prisoner_id, status_id) VALUES (%s, %s);", (prisoner_id, status_id))
    
def insert_source(link, info_id):
    cur.execute("INSERT INTO source (link, info_id, prisoner_id) VALUES (%s, %s, %s);", (link, info_id, prisoner_id))
    
def remove_spaces(obj):
    for key in list(obj):
        new_key = key.strip()
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    return obj

try:
    conn = psycopg2.connect(database='prisoners', 
                            user='postgres', 
                            password='Pnemesis353', 
                            host='localhost', 
                            port='5432')
    print('connected!')
except:
    print("not connected!")
    
cur = conn.cursor()

url = "https://rwc.shtab.net/api/murder/?format=json&limit=1000&offset=0"

prisoner_id = 1

while True:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read(), object_hook=remove_spaces)
    
    for prisoner in data['results']:
        print(prisoner['id'])
        if prisoner['vch']:
            cur.execute("INSERT INTO militarybase (name, longitude, latitude, take_part) SELECT %s, %s, %s, %s WHERE NOT EXISTS (SELECT name FROM militarybase WHERE name = %s);", 
                        (prisoner['vch']['name'], 
                        prisoner['vch']['longitude'], 
                        prisoner['vch']['latitude'], 
                        prisoner['vch']['take_part'],
                        prisoner['vch']['name']))
            
            cur.execute("SELECT id FROM militarybase WHERE name = %s;", (prisoner['vch']['name'],))        
        else: cur.execute("SELECT id FROM militarybase WHERE name = 'Вооружённые силы Российской Федерации';")
        
        cur_value = cur.fetchone()
        base_id = cur_value[0] if cur_value else None
        
        if prisoner['details']!={'': ''}:
            adress = prisoner['details']['Адреса']
            rank = prisoner['details']['Воинское звание']
        else: adress, rank = None, None
                
    
        cur.execute("INSERT INTO prisoner (id, name, date_of_birth, rank, adress, military_base_id) VALUES (%s, %s, %s, %s, %s, %s);", 
                    (prisoner_id, 
                     prisoner['fio'], 
                     prisoner['dob'], 
                     rank, 
                     adress,
                     base_id))
        
        if prisoner['link2'] != '':
            insert_source(prisoner['link2'], 2)
            
        if prisoner['details']!={'': ''}:
                
            rank = prisoner['details']['Воинское звание']

            if prisoner['details']['причетний до війни з Україною'] == "так":
                insert_statinstance(1)
                insert_source(prisoner['details']['посилання на інформацію'], 1)
            
            if prisoner['details']['вбитий'] == "так":
                insert_statinstance(2)
            
            if prisoner['details']['полонений'] == "так":
                insert_statinstance(3)

            if prisoner['details']['розслідування'] != '':
                insert_statinstance(4)
                insert_source(prisoner['details']['розслідування'], 3)
            
        prisoner_id += 1
        conn.commit()
    
    if not data['next']: break
    url = data['next']
        
cur.close()
conn.close()
