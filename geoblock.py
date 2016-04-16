import urllib




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

    print "Reading files into dictionary\nNot yet implemented\n"

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
            if curr_line[2] == "ipv4" && curr_line[1] != "*":

                # case if the country is already in the dict, we do not want to overwrite any keys
                if country_ip.has_key(curr_line[1]):

                    country_ip[curr_line[1]].append(curr_line[2])




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