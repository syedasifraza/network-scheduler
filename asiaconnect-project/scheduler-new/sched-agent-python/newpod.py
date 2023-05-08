from createpods_t import createpod

def main():
    nodes = ["203.250.172.1","203.250.172.2","203.250.172.3","203.250.172.4"]
    details = {'name':'testpod','image':'nginx','cpus':'1','gpus':'0','memory':'1024'}
    i = 2
    resp= createpod(nodes,details,i)
    print(resp)

if __name__ == '__main__':
    main()

