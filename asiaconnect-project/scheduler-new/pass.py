import sys
from networkpass import networkpass

# python pass.py 203.250.172.1 203.250.172.2 203.250.172.3 203.250.172.4 2
# ['pass.py', '203.250.172.1', '203.250.172.2', '203.250.172.3', '203.250.172.4', '2']
# print(sys.argv)

#test = networkpass(sys.argv)

arraytest = ['203.250.172.1', '203.250.172.2', '203.250.172.3', '203.250.172.30', '3']

test = networkpass(arraytest)

