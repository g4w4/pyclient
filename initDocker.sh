

docker network create wsp_1

docker run -d --name <name> --network <network> -v <carpetaLoca>:/media --ip <ip> firefox

docker run --network wsp_1 -dti -e SELENIUM='http://firefox:4444/wd/hub' -v /usr/local/services/wspapi/py_client:/app --name py_client  py_client 

python setup.py install

docker run --network wsp  -p 4000:4000 -dti --name node_server -v /usr/local/services/wspapi:/app --name node_server node_server



docker run -d -p 4444:4444 -p 5900:5900 --name demo_browser --network wsp_1 firefox

docker run --network wsp_1 -dti -e SELENIUM='http://172.18.0.2:4444/wd/hub' -v /usr/local/services/demo_wsp:/app --name py_demo  py

docker run --network wsp_1  -p 4000:4000 -dti --name node_help -v /usr/local/services/demo_wsp:/app --name node_demo node

