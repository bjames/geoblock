import urllib, netaddr

RIRS = ["afrinic", "apnic", "lacnic", "ripe", "arin"]

def country_select():

    #

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

    # Reads file contents into a nested dictionary
    # The form of the dictionary is {Key_1, {Key_2: Value}}
    # where Key_1 is the Country Code, Key_2 is the IP Address as an integer
    # and the value is the number of IP address in the range
    # ex {'us', {823564: 1024}} Note: Those are just random numbers I typed
    # Worth mentioning is that the number of addresses may not always be a power of 2
    # more info on the file structure here: https://www.apnic.net/publications/media-library/documents/resource-guidelines/rir-statistics-exchange-format

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

                # we want only the ipv4 lines that are for a specific country
                if curr_line[2] == "ipv4" and curr_line[1] != "*":

                    country_code = curr_line[1]
                    ipv4_addr = netaddr.IPAddress(curr_line[3])
                    wildcard = netaddr.IPAddress(int(curr_line[4])-1)

                    # ARIN has some addresses listed as 'reserved' that aren't assigned to any country
                    # it doesn't seem like any of the other RIRs are doing this, but just in case we've handled
                    # it here. I think the explanation is here: https://www.arin.net/policy/nrpm.html#four10
                    if country_code == '':

                        country_code = f.name + " reserved"

                    # case if the country is already in the dict, we do not want to overwrite any keys
                    if country_ip.has_key(country_code):

                        # curr_line[1] is the country code, curr_line[3] is the ip address (network id), curr_line[4]
                        # is the count of address (not always CIDR)
                        country_ip[country_code][ipv4_addr] = wildcard

                    # case if we do not yet have the country code in our nested dict
                    else:

                        # this creates our first key-value pair for the nested dict of the current country, which tells
                        # the Python interpreter that we are creating a dictonary
                        # readability: country_ip[country_code]={1st_ipv4_address:num_addresses_in_range]
                        country_ip[country_code]={ipv4_addr: wildcard}

            except IndexError:

                # some of the lines aren't split into any columns. We don't need data from those anyways.
                pass

    return country_ip


def gen_acl(country_ip):

    print "Generating ACL\nNot yet implemented\n"

    # TODO add a mechanism to select which countries to block (or which countries to not block)
    # Generates Cisco IOS ACL with wildcard bits

    outfile = open('acl.txt', 'w')

    outfile.write('ip access-list extended geoblock\n')
    outfile.write('remark Generated using geoblock.py\nremark\n')

    # Pretty standard, iterate over our dictionary and output the data to acl.txt
    for country, ip_dict in country_ip.iteritems():

        outfile.write('remark Block IP ranges from ' + country + '\nremark\n')

        for ip, wildcard in ip_dict.iteritems():

            # deny ip ip_address wildcard_bits
            outfile.write('deny ip {0} {1}\n'.format(str(ip), str(wildcard)))

        outfile.write('remark\nremark End of IP ranges from ' + country + '\nremark\n')




def main():

    # TODO allow users to set options ex. whether or not to download the latest stats files, or select countries to block

    # download_files()
    country_ip = read_files()
    gen_acl(country_ip)

    print "Finished!\n"


main()