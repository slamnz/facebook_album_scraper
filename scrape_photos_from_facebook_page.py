# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 22:15:56 2017

@author: S
"""

import json
import requests
import urllib
import os
import threading

class download_thread(threading.Thread):
    def __init__(self, ID, folder_name, unit):
        threading.Thread.__init__(self)
        self.ID = ID
        self.folder_name = folder_name
        self.unit = unit
    def run(self):
        
        ID = self.ID
        unit = self.unit
        folder_name = self.folder_name
        
        new_file = "./" + folder_name + "/" + unit["id"] + ".jpg"
        
        if not os.path.isfile(new_file):
            try:
                urllib.request.urlretrieve(unit["source"], new_file)
                print("%s: %s downloaded" % (ID, unit["id"]))
            except:
                print("%s: %s failed" % (ID, unit["id"]))
                pass
        else:
            print("%s: %s exists" % (ID, unit["id"]))
            
class download_album_thread(threading.Thread):
    def __init__(self, album, root_folder):
        threading.Thread.__init__(self)
        self.album = album
        self.root_folder = root_folder
    def run(self):
        download_album(self.album,self.root_folder)
    
class download_page_thread(threading.Thread):
    def __init__(self, page, access_token):
        threading.Thread.__init__(self)
        self.page = page
        self.access_token = access_token
    def run(self):
        scrape_photos_from_page(self.page, self.access_token)
    

def remove_illegal_characters(folder_name):
    result = folder_name
    result = ''.join(character for character in folder_name if (character.isalnum() or character in " []") and character != "./\\|<>:?*\"\'")
    result = result.strip()
    return result

    
def download_from_dictionary(dictionary, folder_name):
    
    print("BEGIN DOWNLOAD for %s" % folder_name)
    
    """
    i = 1
    active_threads = []
    
    for unit in dictionary:
        
        thread = download_thread(i, folder_name, unit)
        thread.start()
        active_threads.append(thread)
        
        i += 1
        
    for t in active_threads:
        t.join()
        
    """
    
    i = 0
    active_threads = []
    
    while(i < len(dictionary)):
        
        
        if(threading.active_count() < 50):
            
            unit = dictionary[i]

            thread = download_thread(i, folder_name, unit)
            thread.start()
            active_threads.append(thread)
            i += 1

    for t in active_threads:
        t.join()
    
    print("END DOWNLOAD \n")
        
def download_album(album, root_folder_name):
    
    folder_name = album["name"]
    folder_name = remove_illegal_characters(folder_name)
    new_path = root_folder_name + "/" + folder_name
    number_of_existing_files = 0
    
    if not os.path.isdir(new_path):
        
        try:
            os.makedirs(new_path)
            print("%s folder created." % new_path)
        except:
            print("Error occured when trying to create %s" % new_path)
            
    else:
        
        print("%s folder exists." % new_path)
        
    number_of_existing_files = len([name for name in os.listdir(new_path) if os.path.isfile(os.path.join(new_path, name))])
    
    if number_of_existing_files == album["count"]:
        print("Duplicate detected! Download skipped.")
    else:
        
        print("%s Photo Count: %s \n" % (new_path, album["count"]))
            
        #Acquire list of photo by id/source dictionaries
    
        current_list = []
        photo_set = album["photos"]
    
        while(True):
            
            photos_data = photo_set["data"]
    
            for photo in photos_data:
                
                unit = {"id" : photo["id"], "source" : photo["source"]}
                current_list.append(unit)
                
            print("Photos scraped: %s" % len(current_list))
            
            try:
                
                try:
                    next_url = photo_set["paging"]["next"]
                except:
                    next_url = photo_set["next"]
    
                request = requests.get(next_url).text
                photo_set = json.loads(request)
                
            except KeyError:
                #Reached the end of album
                break
        
        print("Number of photo sources scraped: %s \n" % (len(current_list)))
        download_from_dictionary(current_list, root_folder_name + "/" + folder_name)

def scrape_photos_from_page(pg, access_token_code):
    
    # HTTP Stuff
    
    host = "https://graph.facebook.com/"
    version = "v2.8/"
    page_id = pg
    modifiers = "?fields=name,albums{name,count,photos{id,source}}"
    access_token = "&access_token=%s" % access_token_code
    
    get_json= host + version + page_id + modifiers + access_token
    
    # Page JSON 
    
    page = json.loads(requests.get(get_json).text)
    
    # Albums JSON
    
    albums = page["albums"]
    albums_data = albums["data"]
    page_id = page["id"]
    page_name = remove_illegal_characters(page["name"])
    
    #Create main folder
    
    main_folder_name = ("[%s]%s" % (page_id,page_name)) 
    print(main_folder_name + "\n")
    
    page_folder_exists = os.path.isdir(main_folder_name)
    
    if not page_folder_exists:
        try:
            os.makedirs(main_folder_name)
        except Exception as e:
            print("Something went wrong with the page folder creation.")
            print(e)
        print("\"%s\" folder created!" % main_folder_name)
        
    else:
        print("\"%s\" folder already exists." % main_folder_name)
    
        
    #Iterates album by album
    
    while(True):
        
        #Iterates photo by photo per album
        
        #threads = []

        for alb in albums_data:
            
            if alb["count"] > 0:
                download_album(alb,main_folder_name)
                """
                thread = download_album_thread(alb,main_folder_name)
                thread.start()
                threads.append(thread)
                
        for t in threads:
            t.join()
        """
        
        #Get next album
        
        try:
            next_json =  albums["paging"]["next"]
            albums = json.loads(requests.get(next_json).text)
            albums_data = albums["data"]
        except KeyError:
            print("== END OF ALBUM LIST ==")
            break
        
def scrape_photos_from_pages(pg_list, access_token_code):
    
    for p in pg_list:
        
        scrape_photos_from_page(p, access_token_code)

    """"
    threads = []

    for p in pg_list:
        thread = download_page_thread(p, access_token_code)
        thread.start()
        threads.append(thread)
        
    for t in threads:
        t.join()
    """
    

