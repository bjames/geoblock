import urllib2
import netaddr
from sortedcontainers import SortedList

# TODO Add a function to take data from http://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv
# and use it to create simple aggregate routes. This is being done in an attempt
# to decrease ACL size

RIRS = [["ftp://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest", "afrinic"],
        ["ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest", "apnic"],
        ["ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest", "lacnic"],
        ["ftp://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest", "ripe"],
        ["ftp://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest", "arin"]]

RIR_NAMES = rir_list = ["afrinic", "apnic", "lacnic", "ripe", "arin"]

def floor_log2(n):
    assert n > 0
    last = n
    n &= n - 1
    while n:
        last = n
        n &= n - 1
    return last


def country_select():

    # TODO implement better input validation

    pref = raw_input("List of countries to [b]lock or to [p]ermit? [p]: ")

    try:
        if pref[0] == 'b':
            permit = False
        elif pref[0] == 'p':
            permit = True
        else:
            print "Invalid input\n"
            return

    # if we get an index error then nothing was entered
    except IndexError:

        permit = True

    user_input = (raw_input("List countries using two character ISO3166 code, \
                            delimited with whitespace: ").upper()).split()

    return user_input, permit


def download_countryip_files():

    print "Downloading data from RIRs\n"

    for rir in RIRS:

        # open the url and write the contents to our file (RIR[0] is our url
        # RIR[1] is our filename
        inet_file = urllib2.urlopen(rir[0])

        with open(rir[1], 'w') as output:

            output.write(inet_file.read())

        output.close()


def read_countryip_files(country_list, permit, rir_list = RIR_NAMES):

    # list containing our file objects
    file_list = []

    country_ip = SortedList()

    # Open the files we downloaded earlier and store the file object
    for rir in rir_list:
        file_list.append(open(rir))

    for f in file_list:

        for line in f:

            curr_line = line.split('|')

            try:

                # we want only the ipv4 lines that are for a specific country
                # also only want countries that we are going to block
                if (curr_line[2] == "ipv4" and curr_line[1] != "*") and \
                    ((permit and curr_line[1] not in country_list) or
                     (not permit and curr_line[1] in country_list)):

                    country_code = curr_line[1]
                    network_id = curr_line[3]
                    wildcard = int(curr_line[4])-1


                    try:

                        country_ip.add(netaddr.IPNetwork((network_id) + "/" + str(netaddr.IPAddress(wildcard))))

                    except netaddr.AddrFormatError:

                        print "rounded network " + network_id + " with " + str(wildcard) + " hosts down to nearest power of 2"
                        wildcard = floor_log2(wildcard) - 1
                        print wildcard
                        country_ip.add(netaddr.IPNetwork((network_id) + "/" + str(netaddr.IPAddress(wildcard))))


            except IndexError:

                # some of the lines aren't split into any columns
                # those don't have any data we need anyways
                pass

    country_ip = netaddr.cidr_merge(country_ip)

    return country_ip


def gen_countryip_acl(country_ip, file_oper = 'w'):

    # Generates Cisco IOS ACL with wildcard bits

    print "Generating ACL\n"

    outfile = open('acl.txt', file_oper)

    if(file_oper == 'w'):
        outfile.write('ip access-list extended geoblock\n')
        outfile.write('remark Generated using geoblock.py\nremark\n')

    # iterate over our dictionary and output the data to acl.txt
    for network in country_ip:

        # deny ip ip_address wildcard_bits
        outfile.write(' deny ip {0} {1} any\n'.format((str(network.ip)), str(network.hostmask)))

    outfile.write(' remark IPs blocked by country\n')
    outfile.close()


def download_slasheight():

    inet_file = urllib2.urlopen("http://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv")

    with open("iana", 'w') as output:

        output.write(inet_file.read())

    output.close()


def rir_select():

    # TODO implement better input validation

    print "Select RIRs to BLOCK from list, separated by a space"
    user_input = (raw_input("ARIN, RIPE, AFRINIC, APNIC, LACNIC: ").lower()).split()

    # validate user input
    for word in user_input:

        if(word != "arin" and word != "ripe" and word != "afrinic" and
            word != "apnic" and word != "lacnic"):
            print "Invalid input"

    return user_input


def rir_gen_ip_list(user_rir_list):

    # TODO take the list of RIRs that we are blocking and create a list of /8s
    # to block

    rir_slasheight_list = SortedList()

    iana_file = open("iana")

    for line in iana_file:

        curr_line = line.split(',')

        for rir in user_rir_list:

            # case in which the whois line from our csv contains the RIR
            if rir in curr_line[3]:
                network = curr_line[0].lstrip('0')
                rir_slasheight_list.add(netaddr.IPNetwork(network))
                break

    rir_slasheight_list = netaddr.cidr_merge(rir_slasheight_list)

    return rir_slasheight_list


def rir_gen_acl(rir_slasheight_list):

    # TODO take the list of countries we are blocking and see if we can simply
    # block the /8s that are assigned to that RIR. Function will return a list
    # of RIRs

    outfile = open('acl.txt', 'w')

    outfile.write('ip access-list extended geoblock\n')
    outfile.write(' remark Generated using geoblock.py\n remark\n')

    for network in rir_slasheight_list:
        outfile.write(' deny ip {0} {1} any\n'.format((str(network.ip)), str(network.hostmask)))

    outfile.write(' remark IPs blocked by RIR\n')

    outfile.close()

def find_matching_rirs(country_list, permit):

    rir_list = []
    file_list = []

    for rir in RIRS:

        file_list.append(open(rir[1]))

    for f in file_list:

        countries_in_file = []

        for line in f:

            curr_line = line.split('|')

            try:

                country = curr_line[1]

                if(curr_line[0][0] != '2' and country != '*' and country not in countries_in_file):

                    countries_in_file.append(country)

            except IndexError:

                pass

        if(not permit and (set(countries_in_file) <= set(country_list))):

            rir_list.append(f.name)

        elif(permit and not set(countries_in_file) >= set(country_list)):

            print f.name
            rir_list.append(f.name)

    return rir_list


def gen_hybrid_acl(rir_list, country_list, permit):

    rir_slasheight_list = rir_gen_ip_list(rir_list)
    rir_gen_acl(rir_slasheight_list)
    country_ip = read_countryip_files(country_list, permit, set(RIR_NAMES) - set(rir_list))
    gen_countryip_acl(country_ip, 'a')


def block_by_country():

    #download_countryip_files()
    country_list, permit = country_select()
    country_ip = read_countryip_files(country_list, permit)
    gen_countryip_acl(country_ip)


def block_by_RIR():

    #download_slasheight()
    user_rir_list = rir_select()
    rir_slasheight_list = rir_gen_ip_list(user_rir_list)
    rir_gen_acl(rir_slasheight_list)


def block_by_hybrid():

    #download_slasheight()
    #download_countryip_files()
    country_list, permit = country_select()
    rir_block_list = find_matching_rirs(country_list, permit)
    gen_hybrid_acl(rir_block_list, country_list, permit)


def main():

    finished = False

    while(not finished):

        print "1. Block by country"
        print "2. Block by RIR /8"
        print "3. Hybrid"
        print "4. Quit"

        selection = raw_input("Input Selection: ")
        if(selection == '1'):
            block_by_country()
        elif(selection == '2'):
            block_by_RIR()
        elif(selection == '3'):
            block_by_hybrid()
        elif(selection == '4'):
            finished = True
        else:
            print "Invalid input, please enter an int 1-4"

    print "Goodbye!"


main()
