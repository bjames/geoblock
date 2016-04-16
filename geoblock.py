import urllib, netaddr

RIRS = ["afrinic", "apnic", "lacnic", "ripe", "arin"]


def download_files():

    print "Downloading data from RIRs\n"

    urllib.urlretrieve("ftp://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest", "afrinic")
    urllib.urlretrieve("ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest", "apnic")
    urllib.urlretrieve("ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest", "lacnic")

    # RIPE and ARIN don't follow the standard format so we had to hardcode the URLs
    urllib.urlretrieve("ftp://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest", "ripe")
    urllib.urlretrieve("ftp://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest", "arin")

def read_files():

    print "Reading files into dictionary\n"

    # TODO
    # Read files into a datastructure, maybe a dictonary?

    # list containing our file objects
    file_list = []

    # nested dictionary used to store our countries and IP addresses
    country_ip = {}

    # Open the files we downloaded earlier and store the file object in our list
    for rir in RIRS:
        file_list.append(open(rir))

    for f in file_list:
        for line in f:
            curr_line = line.split('|')

            try:
                if curr_line[2] == "ipv4" and curr_line[1] != "*":

                    # case if the country is already in the dict, we do not want to overwrite any keys
                    if country_ip.has_key(curr_line[1]):

                        # curr_line[1] is the country code, curr_line[3] is the ip address (network id), curr_line[4] is the count of address (not always CIDR) see: https://www.apnic.net/publications/media-library/documents/resource-guidelines/rir-statistics-exchange-format
                        # readability: country_ip[country_code][1st_ipv4_address]=[num_addresses_in_range]
                        country_ip[curr_line[1]][int(netaddr.IPAddress(curr_line[3]))] = int(curr_line[4])

                    # case if we do not yet have the country code in our nested dict
                    else:

                        # this creates our first key-value pair for the nested dict of the current country, which tells
                        # the Python interpreter that we are creating a dictonary
                        # readability: country_ip[country_code]={1st_ipv4_address:num_addresses_in_range]
                        country_ip[curr_line[1]]={int(netaddr.IPAddress(curr_line[3])):int(curr_line[4])}

            except IndexError:

                print "We are in a region of the file we don't need data from anyways, proceed\n"

    print "Finished reading files"




def sort_ranges():

    print "Sorting IP address\nNot yet implemented\n"

    # TODO
    # Sort the IP ranges for each key, that way it's easier to aggregate


def aggregate():

    print "Calculating aggregates\nNot yet implemented\n"

    # Aggregate IP ranges where possible


def gen_acl():

    print "Generating ACL\nNot yet implemented\n"

    # TODO
    # Generate Cisco IOS ACL


def main():

    # download_files()
    read_files()
    sort_ranges()
    aggregate()
    gen_acl()

    print "Finished!\n"


main()