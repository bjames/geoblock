import urllib2
import netaddr
import csv
import os.path
from sortedcontainers import SortedList

RIRS = [["ftp://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest", "afrinic"],
        ["ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest", "apnic"],
        ["ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest", "lacnic"],
        ["ftp://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest", "ripe"],
        ["ftp://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest", "arin"]]

RIR_NAMES = ["afrinic", "apnic", "lacnic", "ripe", "arin"]

# TODO Implement a method that permits the counties listed and then denies all other networks
# TODO Adjust variable and function names to better represent the purpose of the variable or function


def floor_log2(n):

    # Currently using next_power_of_2 since it's unlikely (possibly not possible) that any IP that we include by
    # rounding up will be routed in any countries that we do not want to block
    # left in place for potential future use

    # Works by clearing the least significant bit until we are just left with the most significant bit
    # ie the next lowest power of 2

    # this function should only receive positive input, raise an assertion error otherwise
    assert n > 0
    last = n
    # clears the least significant bit
    n &= n - 1
    while n:
        last = n
        n &= n - 1
    return last


def next_power_of_2(n):

    # currently in use instead of floor_log2

    # 2^(number of bits required to represent (number - 1))
    return 2**(n-1).bit_length()


def country_select():

    pref = raw_input("List of countries to [b]lock or to [p]ermit? Note that by selecting permit we will output an "
                     "ACL that denies other countries, not one that permits the selected countries followed by a "
                     "deny all statement (although that feature may be added in the future) [p]: ")

    try:
        if pref[0] == 'b':
            permit = False
        elif pref[0] == 'p':
            permit = True
        else:
            print "Invalid input, defaulting to PERMIT\n"
            permit = True

    # if we get an index error then nothing was entered, default to permit
    except IndexError:

        permit = True

    user_input = (raw_input("List countries using two character ISO3166 code, delimited with whitespace: ")
                  .upper()).split()

    return user_input, permit


def download_iana():

    # Downloads the IANA network lists, download speeds are fairly slow, so we give the user the option to not
    # download if the file already exists

    pref = "Y"

    # since downloading the files is often slow, we give the user the option to download if the file exists
    if os.path.isfile("iana"):
        pref = raw_input("IANA RIR network list already exists. Download from source and overwrite, "
                         "[y]es or [n]o? [n]: ").upper()

    try:

        if pref[0] == "Y":

            print "Downloading RIR networks list from IANA"

            inet_file = urllib2.urlopen("http://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv")

            with open("iana", 'w') as output:

                output.write(inet_file.read())

            output.close()

    # since we set pref at the beginning of the function, an index error means that no input was given at the prompt
    # therefore, we don't do anything here
    except IndexError:

        pass


def download_rirs():

    # Downloads the RIR network lists, download speeds are fairly slow, so we give the user the option to not
    # download if the file already exists

    file_exists = True
    pref = "Y"

    for rir in RIR_NAMES:

        if not os.path.isfile(rir):
            file_exists = False
            break

    if file_exists:
        pref = raw_input("RIR network lists already exist. Download from source and overwrite, [y]es or [n]o? [n]: ")\
            .upper()

    try:

        if pref[0] == "Y":

            print "Downloading network lists from RIRs\n"

            for rir in RIRS:

                # open the url and write the contents to our file (RIR[0] is our url
                # RIR[1] is our filename
                inet_file = urllib2.urlopen(rir[0])

                with open(rir[1], 'w') as output:

                    output.write(inet_file.read())

                # this function is surprisingly slow, so we make it verbose
                print rir[1] + " downloaded\n"

                output.close()

    # since we set pref at the beginning of the function, an index error means that no input was given at the prompt
    # therefore, we don't do anything
    except IndexError:

        pass


def read_rirs(country_list, permit, rir_list=RIR_NAMES):

    # list containing our file objects
    file_list = []

    # we use a SortedList so that elements are inserted in order. This allows cidr_merge to work
    rir_ips = SortedList()

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

                        # Add network to list, if the number of IPs was not a
                        # power of 2 (wildcard is not valid).
                        # AddrFormatError is thrown
                        rir_ips.add(netaddr.IPNetwork(network_id + "/" + str(netaddr.IPAddress(wildcard))))

                    # Handle case in where our mask is invalid by rounding DOWN
                    except netaddr.AddrFormatError:

                        print "rounded network " + network_id + " with " + str(wildcard) + \
                              " hosts up to nearest power of 2"
                        wildcard = next_power_of_2(wildcard) - 1
                        print wildcard + 1
                        rir_ips.add(netaddr.IPNetwork(network_id + "/" + str(netaddr.IPAddress(wildcard))))

            # IndexErrors only occur when parsing columns we don't need
            except IndexError:

                pass

        f.close()

    # cidr_merge takes our list of IPs and summarizes subnets where possible
    # this greatly decreases the number of ACL entries
    rir_ips = netaddr.cidr_merge(rir_ips)

    return rir_ips


def rir_select():

    print "Select RIRs to BLOCK from list, separated by a space"

    # python doesn't have a do-while loop
    user_input = "invalid"

    while user_input == "invalid":

        user_input = (raw_input("ARIN, RIPE, AFRINIC, APNIC, LACNIC: ").lower()).split()

        # validate user input
        for word in user_input:

            if word != "arin" and word != "ripe" and word != "afrinic" and word != "apnic" and word != "lacnic":

                print "Invalid input, try again"
                user_input = "invalid"

    return user_input


def iana_rir_gen_ip_list(user_rir_list):

    # generates a list of networks that can be blocked by RIR

    # we use a SortedList so that elements are inserted in order. This allows cidr_merge to work
    rir_slash_eight_list = SortedList()

    with open('iana') as iana_file:

        iana_csv = csv.reader(iana_file)

        for line in iana_csv:

            for rir in user_rir_list:

                # case in which the whois line from our csv contains the RIR
                if rir in line[3]:

                    network = line[0].lstrip('0')
                    rir_slash_eight_list.add(netaddr.IPNetwork(network))

                    # if we find a match, there is no reason to see if the other RIRs are on the same line
                    break

        # run cidr_merge to summarize
        rir_slash_eight_list = netaddr.cidr_merge(rir_slash_eight_list)

    return rir_slash_eight_list


def gen_rir_acl(country_ip, file_oper ='w'):

    # output our list of country networks we are blocking to a Cisco ACL

    print "Generating ACL\n"

    with open("acl.txt", file_oper) as outfile:

        if file_oper == 'w':
            outfile.write('ip access-list extended geoblock\n remark Generated using geoblock.py\n')

        outfile.write(' remark networks blocked by country\n')

        # iterate over our dictionary and output the data to acl.txt
        for network in country_ip:

            # deny ip ip_address wildcard_bits
            outfile.write(' deny ip {0} {1} any\n'.format((str(network.ip)), str(network.hostmask)))

        outfile.write(' remark end IPs blocked by country\n')


def iana_rir_gen_acl(rir_slasheight_list):

    # output our list of RIR networks we are blocking to a Cisco ACL

    with open('acl.txt', 'w') as outfile:

        outfile.write('ip access-list extended geoblock\n')
        outfile.write(' remark Generated using geoblock.py\n remark networks blocked by RIR\n')

        for network in rir_slasheight_list:
            outfile.write(' deny ip {0} {1} any\n'.format((str(network.ip)), str(network.hostmask)))

        outfile.write(' remark end IPs blocked by RIR\n')


def write_last_acl_line():

    # writes last line to the ACL

    with open('acl.txt', 'a') as outfile:

        outfile.write(' permit ip any any\n')

def find_matching_rirs(country_list, permit):

    # function takes a list of countries that we are either permitting or denying and outputs a list of RIRs
    # csv file is from https://www.nro.net/about-the-nro/list-of-country-codes-and-rirs-ordered-by-country-code

    # not crazy about the way I hardcoded these sets, may try and find a better solution down the road
    arin = set()
    afrinic = set()
    apnic = set()
    lacnic = set()
    ripe = set()
    country_set = set(country_list)
    rir_list = []

    with open("country_codes.csv", 'r') as country_code_rir_file:

        country_code_rir_csv = csv.reader(country_code_rir_file)

        for line in country_code_rir_csv:

            # read each country in the country_codes.csv into the array for the RIR it falls under
            if line[3] == "ARIN":
                arin.add(line[1])
            elif line[3] == "AFRINIC":
                afrinic.add(line[1])
            elif line[3] == "APNIC":
                apnic.add(line[1])
            elif line[3] == "LACNIC":
                lacnic.add(line[1])
            elif line[3] == "RIPE NCC":
                ripe.add(line[1])

        # if we listed the countries we would like to PERMIT,
        # then we block the RIRs in which our country_list and the RIR set are disjoint
        if permit:
            if not country_set & arin:
                rir_list.append("arin")
            if not country_set & afrinic:
                rir_list.append("afrinic")
            if not country_set & apnic:
                rir_list.append("apnic")
            if not country_set & lacnic:
                rir_list.append("lacnic")
            if not country_set & ripe:
                rir_list.append("ripe")
        # otherwise, we block the RIRs that are subsets of the country set(definitely an edge case)
        else:
            if country_set >= arin:
                rir_list.append("arin")
            if country_set >= afrinic:
                rir_list.append("afrinic")
            if country_set >= apnic:
                rir_list.append("apnic")
            if country_set >= lacnic:
                rir_list.append("lacnic")
            if country_set >= ripe:
                rir_list.append("ripe")

    return rir_list


def gen_hybrid_acl(rir_list, country_list, permit):

    # to generate our hybrid acl we must:
    # generate a list of IPs for the RIRs that we blocking, then generate our ACLs
    rir_slasheight_list = iana_rir_gen_ip_list(rir_list)
    iana_rir_gen_acl(rir_slasheight_list)

    # works by only opening the RIR files that we did not block outright
    # we still iterate over our complete list of countries
    country_ip = read_rirs(country_list, permit, set(RIR_NAMES) - set(rir_list))

    # append the acl we created earlier with our country specific blocks
    gen_rir_acl(country_ip, 'a')


def block_by_country():

    # Blocks only by country - attempts to summarize
    # downloads the RIR country IP lists, gets user input and generates acls

    download_rirs()
    country_list, permit = country_select()
    country_ip = read_rirs(country_list, permit)
    gen_rir_acl(country_ip)
    write_last_acl_line()


def block_by_rir():

    # Blocks only complete RIRs - use this to generate short ACLs
    # Downloads IANA IP list, gets user input, generates the ACL

    download_iana()
    user_rir_list = rir_select()
    rir_slasheight_list = iana_rir_gen_ip_list(user_rir_list)
    iana_rir_gen_acl(rir_slasheight_list)
    write_last_acl_line()


def block_by_hybrid():

    # Generates a short ACL by blocking by IANA's RIR allocations where possible, then by country where required
    # An example of when NOT to use this:
    # You want to allow all IPs owned by US companies
    # even if those IPs are destined from a country that you want to block

    # downloads IANA and RIR files, asks user for countries, finds the set of RIRs that contain either all or none
    # of the countries entered by the user (depending on whether the user entered countries to block or allow)
    # then generates the ACL

    download_iana()
    download_rirs()
    country_list, permit = country_select()
    rir_block_list = find_matching_rirs(country_list, permit)
    gen_hybrid_acl(rir_block_list, country_list, permit)
    write_last_acl_line()


def main():

    finished = False

    while not finished:

        print "1. Block by country - Generate an ACL that blocks by country"
        print "2. Block by RIR - Generate an ACL that blocks RIRs"
        print "3. Hybrid - Greatly decreases the size of the ACL by blocking (or permitting) RIRs based on the " \
              "countries that you select. Recommend using this method unless you need to permit IPs owned by a " \
              "country (or company based in a country) that you permit that is being used in a country you want to " \
              "block"
        print "4. Quit"

        selection = raw_input("Input Selection: ")
        if selection == '1':
            block_by_country()
        elif selection == '2':
            block_by_rir()
        elif selection == '3':
            block_by_hybrid()
        elif selection == '4':
            finished = True
        else:
            print "Invalid input, please enter an int 1-4"

    print "Goodbye!"


main()
