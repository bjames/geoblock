import urllib

RIRS = ["afrinic", "apnic", "lacnic", "ripe", "arin"]

urllib.urlretrieve("ftp://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest", "afrinic")
urllib.urlretrieve("ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest", "apnic")
urllib.urlretrieve("ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest", "lacnic")
urllib.urlretrieve("ftp://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest", "ripe") # RIPE doesn't follow the standard..
urllib.urlretrieve("ftp://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest", "arin")      # Neither does ARIN...