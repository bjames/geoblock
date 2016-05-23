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


def read_countryip_files(country_list, permit):

    print "Reading files into dictionary\n"

    # Reads file contents into a nested dictionary
    # The form of the dictionary is {Key_1, {Key_2: Value}}
    # where Key_1 is the Country Code, Key_2 is the IP Address as an integer
    # and the value is the number of IP address in the range
    # ex {'us', {823564: 1024}} Note: Those are just random numbers I typed

    # list containing our file objects
    file_list = []

    # nested dictionary used to store our countries and IP addresses
    country_ip = {}

    # Open the files we downloaded earlier and store the file object
    for rir in RIRS:
        file_list.append(open(rir[1]))

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
                    ipv4_addr = netaddr.IPAddress(curr_line[3])
                    wildcard = netaddr.IPAddress(int(curr_line[4])-1)

                    # ARIN has some addresses listed as 'reserved' that aren't
                    # assigned to any country it doesn't seem like any of the
                    # other RIRs are doing this, but just in case we've handled
                    # it here. explanation is here:
                    # https://www.arin.net/policy/nrpm.html#four10
                    if country_code == '':

                        country_code = f.name + " reserved"

                    # key is already in our dict
                    if(country_code in country_ip):

                        country_ip[country_code][ipv4_addr] = wildcard

                    # key is not in our dict
                    else:

                        country_ip[country_code] = {ipv4_addr: wildcard}

            except IndexError:

                # some of the lines aren't split into any columns
                # those don't have any data we need anyways
                pass

    return country_ip


def gen_countryip_acl(country_ip):

    # Generates Cisco IOS ACL with wildcard bits

    print "Generating ACL\n"

    outfile = open('acl.txt', 'w')

    outfile.write('ip access-list extended geoblock\n')
    outfile.write('remark Generated using geoblock.py\nremark\n')

    # iterate over our dictionary and output the data to acl.txt
    for country, ip_dict in country_ip.iteritems():

        outfile.write('remark Block IP ranges from ' + country + '\nremark\n')

        for ip, wildcard in ip_dict.iteritems():

            # deny ip ip_address wildcard_bits
            outfile.write('deny ip {0} {1} any\n'.format(str(ip),
                          str(wildcard)))

        outfile.write('remark\nremark End of IP ranges from ' +
                      country + '\nremark\n')


def download_slasheight():

    inet_file = urllib2.urlopen("http://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv")

    with open("iana", 'w') as output:

        output.write(inet_file.read())

    output.close()


def rir_select():

    # TODO implement better input validation

    pref = raw_input("List of RIRs to [b]lock or to [p]ermit? [p]: ")

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

    print "Select RIRs from list, separated by a space"
    user_input = (raw_input("ARIN, RIPE, AFRINIC, APNIC, LACNIC: ").lower()).split()

    # validate user input
    for word in user_input:

        if(word != "arin" and word != "ripe" and word != "afrinic" and
            word != "apnic" and word != "lacnic"):
            print "Invalid input"

    return user_input, permit


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
                ip_address = curr_line[0][:3].lstrip('0') + ".0.0.0"
                rir_slasheight_list.add(netaddr.IPAddress(ip_address))
                break

    return rir_slasheight_list

def rir_gen_acl(rir_slasheight_list):

    # TODO take the list of countries we are blocking and see if we can simply
    # block the /8s that are assigned to that RIR. Function will return a list
    # of RIRs

    outfile = open('acl.txt', 'w')

    outfile.write('ip access-list extended geoblock\n')
    outfile.write('remark Generated using geoblock.py\nremark\n')

    for network in rir_slasheight_list:
        outfile.write('deny ip {0} 0.255.255.255 any\n'.format(str(network)))

def block_by_country():

    download_countryip_files()
    country_list, permit = country_select()
    country_ip = read_countryip_files(country_list, permit)
    gen_countryip_acl(country_ip)
    print "Finished! ACL output to acl.txt"


def block_by_RIR():

    download_slasheight()
    user_rir_list, permit = rir_select()
    rir_slasheight_list = rir_gen_ip_list(user_rir_list)
    rir_gen_acl(rir_slasheight_list)
    print "Finished! ACL output to acl.txt"


def block_by_hybrid():

    pass


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
