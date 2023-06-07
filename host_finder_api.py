import json
from flask import Flask,jsonify,request
import mysql.connector
import re

#Format all MAC Addresses to the Cisco format
def MacAddrCiscoParser(macaddr):

    newMac = re.sub('[.|:|\-| ]', '', str(macaddr)).lower()
    newMac = '.'.join(newMac[i:i+4] for i in range(0,12,4))
    return newMac

def IsIPValid(search):

    ipChunks = search.split(".")
    if int(ipChunks[0])==0 or int(ipChunks[0])==255:
        return 0


    for i in range(len(ipChunks)):
        if int(ipChunks[i]) > 255:
            return 0
   

    return 1

#For generating all the possible patterns regardless what the user puts in. For example if user wants to search for %a029% it could be either %a029%, %a.029%,%a0.29%,%a02.9%
def SearchPatternGenerator(partialMacAddress):
    
    patterns = []

    partialMacAddress = re.sub('[.|:|\-| |%]', '', str(partialMacAddress))

    for i in range(len(partialMacAddress)-1):
        
        if(i<4):

            temp_string = partialMacAddress[:i+1] + '.'
            temp_index = i

            while(temp_index+4<len(partialMacAddress)-1):
                
                if(temp_index+4==len(partialMacAddress)):
                    temp_string=temp_string+partialMacAddress[temp_index+1:temp_index+5]
                else:
                    temp_string=temp_string+partialMacAddress[temp_index+1:temp_index+5] + '.'
                    
                temp_index+=4
                
            temp_string=temp_string+partialMacAddress[temp_index+1:]

            if (temp_string.count('.') <= 2):
                patterns.append('%'+temp_string+'%')

    if(len(partialMacAddress) <= 4):
         patterns.append('%'+partialMacAddress+'%')

    return patterns



def WhatAmI(search):
    
    #Is it an IP?
    if(re.match("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$",search)):
        if(not IsIPValid(search)):
            return "IP is invalid!"
        else:
            return "Found IP:"+search

    #Is it a VLAN?
    if(re.match("^[0-9]{1,3}$",search)):
        if(search[0]=='0'):
            return "VLAN is invalid!"
        else:
            return "Found VLAN:"+search

    #Is it a MAC address?
    if(len(re.sub('[.|:|\-| ]', '', str(search))) == 12 and '%' not in search):
        if(not re.search("[^0-9|a-f|A-F|.|\-| |:]",search)):
            return "Found MAC:"+MacAddrCiscoParser(search)
        else:
            return "MAC address is invalid!"

    #Is it a search for a MAC address?
    if(len(re.sub('[.|:|\-| %]', '', str(search))) < 12 and not re.search("[^0-9|a-f|A-F|.|\-| |:|%|*]",search) and search!="%%"):
        if(search[0] == '%' and search[-1] == '%'):
            return SearchPatternGenerator(search)
        else:
            return "MAC pattern is invalid.Please use * if you are searching for a MAC address.Example: *abcd* or *abcd.efff*"


    return "Parameter invalid! Please search for an IP address, a VLAN (3 digits max), a MAC address (formatting doesn't matter) or a MAC address pattern(such as *0800*)"


def create_app():


    conn = mysql.connector.connect(user='username', 
                                password='pass',
                                host="IP_ADDR",
                                database='db_name',
                                ssl_disabled=True)

    print("Connected to DB:", conn.get_server_info())


    cursor = conn.cursor()

    app = Flask(__name__)


    @app.route('/finder')
    def ArpFinder():
        

        search = request.args.get('search', default = '*', type = str)
        rowcount = 0
        query=''
        queryarr=[]
        results=[]

        if(search=='*' or search==''):
            return jsonify("Error! Please enter search variable. Example: http://127.0.0.1:5000/finder?search=1.1.1.1")


        search=search.replace('*','%')

        variable_parameter = WhatAmI(search)


        #Change the query to reflect your current table structure
        
        if("invalid" in variable_parameter):
            return jsonify(variable_parameter)
        elif("Found" in variable_parameter):
            temp_array = variable_parameter.split(':')
            if("IP" in temp_array[0]):
                query = ("SELECT mac,vlan,ip,description,switch,port FROM table_name WHERE ip="+'"'+search+'"')
            elif("VLAN" in temp_array[0]):
                query = ("SELECT mac,vlan,ip,description,switch,port FROM table_name WHERE vlan="+'"'+search+'"')
            elif("MAC" in temp_array[0]):
                query = ("SELECT mac,vlan,ip,description,switch,port FROM table_name WHERE mac="+'"'+MacAddrCiscoParser(search)+'"')
        elif(isinstance(variable_parameter,list)):
            for pattern in variable_parameter:
                queryarr.append("SELECT mac,vlan,ip,description,switch,port FROM table_name WHERE mac LIKE "+'"'+pattern+'"')


        if(queryarr==[]):
            cursor.execute(query)
            for mac,vlan,ip,description,switch,port in cursor:
                rowcount+=1
                results.append({'MAC Address:':mac,
                        'VLAN:':vlan,
                        'IP Address:':ip,
                        'Port Description:':description,
                        'Switch:':switch,
                        'Switchport:':port
                    })
        elif(query==''):
            for q in queryarr:
                cursor.execute(q)
                for mac,vlan,ip,description,switch,port in cursor:
                    rowcount+=1
                    results.append({'MAC Address:':mac,
                            'VLAN:':vlan,
                            'IP Address:':ip,
                            'Port Description:':description,
                            'Switch:':switch,
                            'Switchport:':port
                        })




        if(rowcount==0):
            return jsonify("No values found!")


        return jsonify(results)


    @app.route('/howto')
    
    #Change IP to whichever address of hostname you are using 
    
    def HowTo():
        
        return """
        <html>
        <head><title>HowTo</title></head>
        <body>
        <h1>How To Use: Quick Guide</h1>
        <p></p>
        <p style="font-size:160%;">Use the correct URL": "http://IP:5000/finder?search=YOUR_SEARCH_HERE</p>
        <p style="font-size:160%;">For searching IP addresses": "http://IP:5000/finder?search=10.0.0.1<br>Format it properly or the script will detect something else instead</p>
        <p style="font-size:160%;">For searching VLANS":"http://IP:5000/finder?search=32<br>Use a 1 to 3 digit number and it will return all hosts in that VLAN. The current network infrastructure has no 4 or more digit VLANS</p>
    <p style="font-size:160%;">For searching MAC addreses":"http://IP:5000/finder?search=abcd.ef12.3456<br>Separators don't matter, it can be abcd.ef12.3456,ab:cd:ef:12:34:56 or just abcdef123456. Make sure the MAC address is whole(12 characters), use partial search only with the pattern</p>
    <p style="font-size:160%;">For searching a MAC address pattern": "http://IP:5000/finder?search=*0080*<br>Use the * character at the beginning and at the end and the script will return all matches</p>	
    </body>		
    </html>
    """


    app.run(host="127.0.0.1", port=5000)

    cursor.close()
    conn.close()



if __name__ == '__main__':
    create_app()


