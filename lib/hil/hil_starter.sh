#!/bin/sh

hil_dir=$1

if [ "$#" -ne 1 ] || ! [ -d "$1" ]; then
    echo "Usage: $0 path_to_HIL_directory" >&2
    exit 1
fi

start_hil_server(){
    cd $hil_dir
    rm haas/haas.db
    ps aux | grep '[h]aas' | awk '{print $2}' | xargs kill -9
    source .venv/bin/activate
    haas-admin db create
    haas serve 5000
}
start_hil_server &
sleep 1
echo HIL server was started in a child process.
sleep 1

start_hil_networks(){
    cd $hil_dir
    source .venv/bin/activate
    haas serve_networks
}
start_hil_networks &
sleep 1
echo HIL networks server was started in a child process.
sleep 1

start_hil_data(){
    cd $hil_dir
    source .venv/bin/activate
    haas node_register host01.com mock host user password
    haas node_register_nic host01.com nic mac_address
    haas switch_register switch mock host user password
    haas port_register switch port
    haas port_connect_nic switch port host01.com nic
    haas project_create cloud01
    haas project_create cloud02
    haas network_create_simple cloud01 cloud01
    haas network_create_simple cloud02 cloud02
    haas project_connect_node cloud01 host01.com
    haas node_connect_network host01.com nic cloud01 null
}
start_hil_data &
sleep 1
echo HIL data was added.
sleep 1
