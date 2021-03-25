#################################
##### Name: Yucan Ding
##### Uniqname: ycding
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
API_KEY = secrets.API_KEY


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, name, category = None, address = None, zipcode = None, phone = None):
        self.name = name
        self.category = category
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return self.name + " (" + self.category + ")" + ": " + self.address + " " + self.zipcode


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    base_url = "https://www.nps.gov"
    return_dict = {}
    response = make_url_request_using_cache(base_url)
    soup = BeautifulSoup(response, 'html.parser')
    dropdown_menu = soup.find(class_ = "dropdown-menu SearchBar-keywordSearch")
    li = dropdown_menu.find_all('li')
    for ele in li:
        a = ele.find('a')
        return_dict[a.text.lower()] = "https://www.nps.gov" + a['href']
    return return_dict
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    soup = BeautifulSoup(make_url_request_using_cache(site_url), 'html.parser')
    title = soup.find(class_ = "Hero-titleContainer clearfix")
    designation = soup.find(class_ = "Hero-designationContainer")

    name = title.find('a').text
    category = designation.find('span', class_ = 'Hero-designation').text
    address = soup.find('span', itemprop = "addressLocality").text + ", " + soup.find(itemprop = 'addressRegion').text
    zipcode = soup.find(itemprop = "postalCode").text.replace(" ","")
    phone = soup.find(class_ = "tel").text.replace("\n", "")
    return NationalSite(name, category, address, zipcode, phone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    return_list = []
    soup = BeautifulSoup(make_url_request_using_cache(state_url), 'html.parser')
    park_result_area = soup.find(id = "parkListResultsArea")
    park_list = park_result_area.find_all('li', class_ = 'clearfix')  
    for park in park_list:
        park_name = park.find('h3')
        park_url = "http://www.nps.gov/" + park_name.find('a')['href'] + "index.htm"
        return_list.append(get_site_instance(park_url))
    return return_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    dictionary = {"key": API_KEY, "origin": site_object.zipcode, "radius": 10.0, "maxMatches": 10, "ambiguities": "ignore", "outFormat": "json"}
    base_url = "http://www.mapquestapi.com/search/v2/radius"
    request_key = construct_key(base_url, dictionary)
    CACHE_DICT = use_cache()
    if request_key in CACHE_DICT:
        print("Using Cache")
    else:
        print("Fetching")
        CACHE_DICT[request_key] = requests.get(url = base_url, params = dictionary).json()
        save_cache(CACHE_DICT)
    return CACHE_DICT[request_key]


def make_url_request_using_cache(url):
    '''Use cache to make url request
    
    Parameters
    ----------
    url: str
        An url that may or may not contained in cache
    
    Returns
    -------
    CACHE_DICT[url]: str
        The text of the response of this url
    '''
    CACHE_DICT = use_cache()
    if url in CACHE_DICT.keys(): # the url is also the unique key
        print("Using Cache")
    else:
        print("Fetching")
        response = requests.get(url)
        CACHE_DICT[url] = response.text
        save_cache(CACHE_DICT)
    return CACHE_DICT[url]


def use_cache():
    ''' If there is a cache file, open it and loads the JSON into
    the CACHE_DICT dictionary. If not, create a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    cache_dict: dict
    '''
    try:
        cache_file = open("cache.json", 'r')
        cache_read = cache_file.read()
        cache_dict = json.loads(cache_read)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current cache
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dump_cache = json.dumps(cache_dict)
    temp = open("cache.json","w")
    temp.write(dump_cache)
    temp.close()


def construct_key(baseurl, dictionary):
    ''' Construct a key using baseurl and a given dictionary
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    dictionary: dict
        A dictionary of the param-value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    lis = []
    for key in dictionary.keys():
        lis.append(f'{key}_{dictionary[key]}')
    lis = sorted(lis)
    return baseurl + '_' + '_'.join(lis)


def print_site_in_state(state_list, park_list, input_value):
    '''Print the site in one user-selected state
    
    Parameters
    ----------
    state_list: list
        a list contains names of all states
    park_list: list
        a list contains names of all parks in the selected state
    input_value: string
        user input state
    
    Returns
    -------
    list
        a list of names of all parks in the selected state
    '''
    while(True):
        if input_value in state_list:
            park_list = []
            i = 1
            park_list = get_sites_for_state(state_dictionary[input_value])
            print("-----------------------------------")
            print("List of national sites in", input_value)
            print("-----------------------------------")
            for park in park_list:
                print("[", str(i).strip(), "]", park.info())
                i += 1
            return park_list
        elif input_value == "exit":
            exit()
        else:
            print("[Error] Enter proper state name\n")
            print('Enter a state name(e.g. Michigan, michigan) or "exit"')
            input_value = input(": ").lower()


def print_nearby_places(site_object):
    '''Print nearby places of the site.
    
    Parameters
    ----------
    site_object: object
        A particular national site
    
    Returns
    -------
    None
    '''
    near_place_list = get_nearby_places(site_object)
    print("-------------------------------------")
    print("Places near", site_object.name)
    print("-------------------------------------") 
    i = 0 
    for near_park in near_place_list["searchResults"]:
        near_fields = near_park["fields"]
        near_name = near_fields["name"]
        if(near_fields["group_sic_code_name_ext"] != ""):
            near_category = near_fields["group_sic_code_name_ext"]
        else:
            near_category = "no category"
        if(near_fields["address"] != ""):
            near_address = near_fields["address"]
        else:
            near_address = "no address"
        if(near_fields["city"] != ""):
            near_city = near_fields["city"]
        else:
            near_city = "no city"
        i += 1
        print("- " + near_name + " (" + near_category + "): " + near_address + ", " + near_city)
        if (i == 10):
            break


def print_near(state_list, park_list):
    '''Print the the near site
    
    Parameters
    ----------
    state_list: list
        a list contains names of all states
    park_list: list
        a list contains names of all parks in the selected state
    
    Returns
    -------
    None
    '''
    while(True):
        print('Choose the number for detail search or "exit" or "back" ')
        next_input = input(": ")
        if(next_input.isdigit()):
            next_input = int(next_input)
            if(next_input > 0 and next_input <= len(park_list)):
                print_nearby_places(park_list[next_input - 1])
                print("-------------------------------------")
            else:
                print("[Error] Invalid input\n")
                print("-------------------------------------")
        elif(next_input == 'exit'):
            exit()
        elif(next_input == 'back'):
            print('Enter a state name(e.g. Michigan, michigan) or "exit"')
            input_value = input(": ").lower()
            park_list = print_site_in_state(state_list, park_list, input_value)
        else:
            print("[Error] Invalid input\n")


if __name__ == "__main__":
    base_url = "https://www.nps.gov/index.htm"
    state_dictionary = build_state_url_dict()
    print('Enter a state name(e.g. Michigan, michigan) or "exit"')
    input_value = input(": ").lower()
    state_list = []
    park_list = []
    for state in state_dictionary.keys():
        state_list.append(state)
    park_list = print_site_in_state(state_list, park_list, input_value)
    print_near(state_list, park_list)