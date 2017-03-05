#!/usr/bin/env python3

import pandas as pd
import re
import math
from http.server import BaseHTTPRequestHandler, HTTPServer


class MiningPropertiesSNL(object):
    """Read Gold spreadsheet from SNL.

    Fields in the source file:

    KeyMineProject
    Property Name
    Primary Commodity
    Commodity Group
    List of Owners
    List of Royalty Holders
    Development Stage
    Activity Status
    Latitude (degrees)
    Longitude (degrees)
    Coordinate Accuracy
    """
    def __init__(self, fname):
        print(fname)
        xl = pd.ExcelFile(fname)
        self.df = xl.parse("Sheet One")

        # rename the fields for ease of programming
        self.df.columns = ["prj", "property_name", "prim_comm", "cgroup", "owners", "royalty", "dev_stage", "act_status", "lat", "lng", "coord_acc"]
        del self.df["prim_comm"]
        del self.df["cgroup"]
        self.low_names = [s.lower() for s in list(self.df['property_name'])]

    def property_names(self):
        return list(self.df['property_name'])

    def property_lc_names(self):
        return self.low_names

    def owners(self):
        return list(self.df['owners'])

    def royalty_holders(self):
        return list(self.df['royalty'])


name_type_share_patt = re.compile(' *([^(]*?) *\((.*)\) *([^%]*)')

class OwnerRoyaltyHolder(object):
    """Owner/Royalty holder.

    """
    def __init__(self, s):
        print(s, name_type_share_patt.match(s).groups())
        (self.name, self._type, self.share) = name_type_share_patt.match(s).groups()

def owner_royalty_split(s):
    if type(s) == str:
        or_list = [s.strip() for s in s.split(';')]
    else:
        or_list = []
    return or_list

class PropertyNotFoundException(Exception):
    pass

def get_property(sa):
    print(sa)
    for p in sa:
        splitted = p.split('=')
        if splitted[0] == 'property_name':
            return splitted[1].replace('+', ' ')  # there is a better way...
    return None
 
def get_radius(sa):
    for p in sa:
        splitted = p.split('=')
        if splitted[0] == 'radius':
            try:
                return float(splitted[1])
            except ValueError:
                return 100.0
    return None

def format_properties(df):
    return df.to_html(index=False)
    
 
# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    def write_file(self, fname):
        with open(fname) as fd:
            self.wfile.write(fd.read().encode('utf-8'))
 
    def read_file(self, fname):
        with open(fname) as fd:
            contents = fd.read()
        return contents

    def send_hdrs(self, resp_code, mime_type):
        self.send_response(resp_code)
        self.send_header('Content-type', mime_type)
        self.end_headers()

    # GET
    def do_GET(self):

        print(self.path)

        if self.path.endswith(".css"):
             p = self.path[1:]
             self.send_hdrs(200, 'text/css')
             self.write_file(p)
             return
        elif self.path.endswith(".js"):
             p = self.path[1:]
             self.send_hdrs(200, 'text/javascript')
             self.write_file(p)
             return
             

        self.send_hdrs(200, 'text/html')
 
        p = self.path
        if p == "/" or p == "/index.html":
            self.write_file("index.html")
            return

        if p.startswith("/prop_search.html"):
            sq = p.split("?", 1)
            p = "" if len(sq) == 1 else sq[1]
            print(p)
            path_els = p.split('&')
    
            if len(path_els) == 0:
                self.write_file("prop_search.html")
                return
    
            prop = None
            if any([p.startswith("property_name=") for p in path_els]):
                prop = get_property(path_els)
    
            radius = 100.0  # km
            if any([p.startswith("radius=") for p in path_els]):
                radius = get_radius(path_els)
            
            print("property={} radius={}".format(prop, radius))
            if not prop:
                self.write_file("prop_search.html")
            else:
                try:
                    property_list = find_properties_in_range(prop, radius)
                    property_table = format_properties(property_list)
                    message = self.read_file("proptable.html").replace("@TABLE@", property_table)
                except PropertyNotFoundException:
                    message = "property %s not found" % prop
                self.wfile.write(bytes(message, "utf8"))
            

def run():
    print('starting server...')
 
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    server_address = ('0.0.0.0', 8081)
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('running server...')
    httpd.serve_forever()
 
def find_properties_in_range(prop, radius):
    print(prop, radius)
    pnames = mp.property_lc_names()
    lprop = prop.lower()
    if lprop not in pnames:
        raise PropertyNotFoundException(prop)
    ix = pnames.index(lprop)
    df = mp.df
    lats = df['lat']
    lngs = df['lng']
    dlat = radius / (111.0 * 0.5)  # latitude: from km to degrees (approx)
    dlng = radius / (111.0 * 0.5 * math.cos(-0.5)) # assume lat is 0.5 rdians South
    row = df.iloc[ix,:]
    center_lat = row['lat']
    center_lng = row['lng']
    print(center_lat, center_lng)
    nearby = df[(center_lat-dlat < lats) & (lats < center_lat+dlat) &
                (center_lng-dlng < lngs) & (lngs < center_lng+dlng)] 
                ##(prop != df['property_name'])]
    nearby['is_target'] = prop == df['property_name']
    #nearby['is_target'] = False
    print(nearby)
    return nearby
    
 
if __name__ == '__main__':
    import re
    import sys
    import getopt

    fname_SNL = "MiningProperties_SNL_Americas.xlsx"

    opts, args = getopt.getopt(sys.argv[1:], "S:")
    for opt, value in opts:
        if opt == '-S':
            fname_SNL = value

    owners = {}
    rholders = {}

    def visit_all(meth, d):
        for owner_list in meth():
            ol = owner_royalty_split(owner_list)
            for h in ol:
                d[OwnerRoyaltyHolder(s).name] += 1

    mp = MiningPropertiesSNL(fname_SNL)
    print(mp.df.head())
    #print(len(mp.property_names()))

    
#    for owner_list in mp.owners():
#    #or owner_list in mp.royalty_holders():
#        ol = owner_royalty_split(owner_list)
#        if len(ol) > 0:
#            print([OwnerRoyaltyHolder(s).name for s in ol])

# Pascua Lama neighbourhood
# nearby = df[(-29.8 < df['Latitude (degrees)']) & (df['Latitude (degrees)'] < -28.8) & (df['Longitude (degrees)'] < -69.5) & (df['Longitude (degrees)'] > -70.2) ]

    run()
