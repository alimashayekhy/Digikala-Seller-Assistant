import requests
from datetime import datetime
import json
import time
import netifaces
import subprocess
import os, re
import pymongo
from config import *
mobisha_token = 'ZcSSY0MJc37^r5xDUI4M0Olco!@E*^pSY!#^b6ZNUgW^AJ@z0Pv$z7S2@bChzH80'

def make_connection():
    """
    Discover available network interfaces and sort them by availability.
    Returns:
        connectionList (list): List of tuples (interface name, timestamp).
        connectionName (str): Name of the most recently used connection.
    """
    network_list = os.listdir('/sys/class/net/')
    r = re.compile('(^wlp.*$)|(^eth.*$)|(^ens.*$)')
    network_list = list(filter(r.match, network_list))
    connectionList = [(connection, time.time()) for connection in network_list]
    connectionList = sorted(connectionList, key=lambda item: item[1])
    for connection in connectionList:
        if not is_ip_in_range(connection[0]):
            return connectionList, connection[0]
    raise Exception("No valid network interfaces available")

def make_get_request3(url, cookies, headers={}, data=""):
    try:
        session = requests.session()
        response = ""

        headers['mobisha'] = str(mobisha_token)
        headers['X-Feature-Flag'] = 'enable-buybox-factors'
        headers['User-Agent'] = 'DigikalaTrustedBot/Mobisha Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'
        a = 429
        while a == 429:
            try:
                response = session.get(
                    url, cookies=cookies, headers=headers, data=data, timeout=20)
                a = response.status_code
                print(datetime.now(), url, response.status_code, data)
                print(':::::::::::::::::::::::::::::::::::::')
                print(f'{url} res time:',
                      response.elapsed.total_seconds(), 's')
                print(':::::::::::::::::::::::::::::::::::::')

            except Exception as e:
                print(str(e))
                return False, "DK_Error"

        if a == 200:
            return True, response
        else:
            return False, a

    except Exception as e:
        print(str(e))

def is_ip_in_range(interface, excluded_range="10.0.0."):
    """
    Check if a given network interface has an IP within the excluded range.
    Args:
        interface (str): Name of the network interface.
        excluded_range (str): IP prefix to exclude (e.g., '10.0.0.').
    Returns:
        bool: True if the interface IP is in the excluded range, False otherwise.
    """
    try:
        addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
        for addr_info in addresses:
            ip = addr_info.get('addr')
            if ip.startswith(excluded_range):
                # Add exceptions for specific IPs or interfaces of main server
                if ip == "10.0.0.239":
                    return False
                return True
    except Exception as e:
        print(f"Error checking interface {interface}: {e}")
    return False

def update_in_alist(alist, key, value):
    """
    Update a value in a list of tuples by key.
    Args:
        alist (list): List of tuples (key, value).
        key (str): Key to update.
        value: New value for the key.
    Returns:
        Updated list.
    """
    return [(k, v) if (k != key) else (key, value) for (k, v) in alist]

def get_next_connection(connectionList, currentConnectionName, excluded_range="10.0.0."):
    """
    Rotate to the next valid network connection, excluding those in the excluded IP range.
    Args:
        connectionList (list): List of tuples (interface name, timestamp).
        currentConnectionName (str): Current active connection.
        excluded_range (str): IP prefix to exclude (e.g., '10.0.0.').
    Returns:
        tuple: Updated connectionList and next valid connectionName.
    """
    connectionList = update_in_alist(connectionList, currentConnectionName, time.time())
    connectionList = sorted(connectionList, key=lambda item: item[1])
    for connection in connectionList:
        if not is_ip_in_range(connection[0], excluded_range):
            return connectionList, connection[0]
    raise Exception("No valid network interfaces available")

connection_list, connection_name = make_connection()
print("connection_list: ", connection_list)

def logRequest(url, response = None):
    try:
        if response is None or (type(response) is str and len(response) == 0):
            response = ''
        elif 'Too Many' in response:
            response = response
        else:
            return

        log = {'url': url, 'response': response, 'time': datetime.now()}
        mydb = pymongo.MongoClient(config['database-server']['local'])["dk-robot"]
        request_logs_model = mydb["request_logs"]
        request_logs_model.insert_one(log)
    except Exception as e:
        print(10*':'+'request loging to db error'+10*':')
        print(e)

def make_put_request(url, data="", headers={}, MSL=""):
    try:
        global connection_list, connection_name
        connection_list, connection_name = get_next_connection(connection_list, connection_name)

        status = False
        digikala_error = 0
        try:
            while not status:
                if digikala_error < 4:
                    token = MSL
                    cookie = 'seller_api_access_token=' + token

                    command = [
                        "curl", "-v", "-s", "-w", "%{http_code}", "--max-time", "30", "--connect-timeout", "10", "-L", "-X", "PUT", str(url),
                        "-H", "content-type: application/x-www-form-urlencoded; charset=UTF-8",
                        "-H", "User-Agent: DigikalaTrustedBot/Mobisha Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
                        "-H", f"cookie: {cookie}",
                        "-H", f"mobisha: {mobisha_token}",
                        "-d", data,
                        "--compressed", "--interface", connection_name
                    ]

                    print('_________connection_name__________')
                    print('connection_name:', connection_name)
                    print('__________________________________')

                    start_time = time.time()
                    try:
                        p = subprocess.run(command, capture_output=True, text=True, check=True)
                        response = p.stdout[:-3]  # Extract response body
                        status_code = p.stdout[-3:]  # Extract status code
                        
                    except subprocess.CalledProcessError as e:
                        p = e
                        response = e.stdout[:-3]
                        status_code = e.stdout[-3:]
                    
                    # TODO: added for debug purpose, remove it later
                    except Exception as e:
                        try:
                            exception_response = json.loads(response)
                        except json.decoder.JSONDecodeError:
                            exception_response = str(response)
                        except Exception as e:
                            exception_response = f"unavailable-exception:{e}"
                            
                        try:
                            exception_p = json.loads(p)
                        except json.decoder.JSONDecodeError:
                            exception_p = str(p)
                        except Exception as e:
                            exception_p = f"unavailable-exception:{e}"
                        return False, "DK_Error"
                        
                    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                    print(f'{url} res time:', (time.time() - start_time), 's')
                    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')

                    print(datetime.now(), url, data, response)
                    logRequest(url, response)

                    if '</html>' in response:
                        print("mamad 15")
                        try:
                            exception_response = json.loads(response)
                        except json.decoder.JSONDecodeError:
                            exception_response = str(response)
                        except Exception as e:
                            exception_response = f"unavailable-exception:{e}"
                        
                        try:
                            exception_p = json.loads(p)
                        except json.decoder.JSONDecodeError:
                            exception_p = str(p)
                        except Exception as e:
                            exception_p = f"unavailable-exception:{e}"
                        return False, "DK_Error"
                    
                    elif not response:
                        try:
                            try:
                                exception_response = json.loads(response)
                            except json.decoder.JSONDecodeError:
                                exception_response = str(response)
                            except Exception as e:
                                exception_response = f"unavailable-exception:{e}"
                            
                            try:
                                if isinstance(p, str):
                                    exception_p = json.loads(p)
                                else:
                                    # If 'p' is not a string, use the serializer to extract useful info
                                    exception_p = serialize_p_object(p)
                            except json.decoder.JSONDecodeError:
                                exception_p = str(p)
                            except Exception as e:
                                exception_p = f"unavailable-exception:{e}"
                                
                            connection_list, connection_name = get_next_connection(connection_list, connection_name)
                            status = False
                            return False, "DK_Error"
                        
                        except Exception as e:
                            try:
                                exception_response = json.loads(response)
                            except json.decoder.JSONDecodeError:
                                exception_response = str(response)
                            except Exception as e:
                                exception_response = f"unavailable-exception:{e}"
                            
                            try:
                                exception_p = json.loads(p)
                            except json.decoder.JSONDecodeError:
                                exception_p = str(p)
                            except Exception as e:
                                exception_p = f"unavailable-exception:{e}"
                    else:
                        try:
                            # TODO: must be removed
                            if "افزودن کالای جدید به لیست تخفیف‌ها" in response:
                                try:
                                    exception_response = json.loads(response)
                                except json.decoder.JSONDecodeError:
                                    exception_response = str(response)
                                except Exception as e:
                                    exception_response = f"unavailable-exception:{e}"
                                
                                try:
                                    exception_p = json.loads(p)
                                except json.decoder.JSONDecodeError:
                                    exception_p = str(p)
                                except Exception as e:
                                    exception_p = f"unavailable-exception:{e}"
                                return True, response
                            
                            else:
                                try:
                                    exception_response = json.loads(response)
                                except json.decoder.JSONDecodeError:
                                    exception_response = str(response)
                                except Exception as e:
                                    exception_response = f"unavailable-exception:{e}"
                                
                                try:
                                    exception_p = json.loads(p)
                                except json.decoder.JSONDecodeError:
                                    exception_p = str(p)
                                except Exception as e:
                                    exception_p = f"unavailable-exception:{e}"
                                a = {'text': response}
                                return True, a
                            
                        except Exception as e:
                            try:
                                exception_response = json.loads(response)
                            except json.decoder.JSONDecodeError:
                                exception_response = str(response)
                            except Exception as e:
                                exception_response = f"unavailable-exception:{e}"
                            
                            try:
                                exception_p = json.loads(p)
                            except json.decoder.JSONDecodeError:
                                exception_p = str(p)
                            except Exception as e:
                                exception_p = f"unavailable-exception:{e}"
                                
                            digikala_error += 1
                            status = False
                            time.sleep(5)
                else:
                    try:
                        exception_response = json.loads(response)
                    except json.decoder.JSONDecodeError:
                        exception_response = str(response)
                    except Exception as e:
                        exception_response = f"unavailable-exception:{e}"
                    
                    try:
                        exception_p = json.loads(p)
                    except json.decoder.JSONDecodeError:
                        exception_p = str(p)
                    except Exception as e:
                        exception_p = f"unavailable-exception:{e}"
                    return False, "DK_Error"
                return False, "DK_Error"
    
        except Exception as e:
            print(
                level="DIGIKALA_REQUEST",
                message=f"make_put_request FAILED: exception: {e}",
                function="make_put_request",
                details={
                    "version": 2,
                    "url": url,
                    "data": data,
                    "status": False,
                    "headers": headers,
                    "dk_status_code": str(e),
                    "response": {
                        "detail": "unavailable",
                        "e": str(e)
                    },
                }
            )  
    
    except Exception as e:
        try:
            exception_response = json.loads(response)
        except json.decoder.JSONDecodeError:
            exception_response = str(response)
        except Exception as e:
            exception_response = f"unavailable-exception:{e}"
        
        try:
            exception_p = json.loads(p)
        except json.decoder.JSONDecodeError:
            exception_p = str(p)
        except Exception as e:
            exception_p = f"unavailable-exception:{e}"

def serialize_p_object(p_obj):
    if isinstance(p_obj, subprocess.CalledProcessError):
        return {
            "cmd": p_obj.cmd,
            "returncode": p_obj.returncode,
            "stdout": p_obj.stdout,
            "stderr": p_obj.stderr,
            "output": getattr(p_obj, "output", None),
        }
    elif isinstance(p_obj, subprocess.CompletedProcess):
        return {
            "args": p_obj.args,
            "returncode": p_obj.returncode,
            "stdout": p_obj.stdout,
            "stderr": p_obj.stderr,
        }
    else:
        return str(p_obj)