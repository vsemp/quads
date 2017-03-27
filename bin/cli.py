import json
import urllib
import os
import sys
import requests


class FailedAPICallException(Exception):
    pass

def check_status_code(response):
    if response.status_code < 200 or response.status_code >= 300:
        sys.stderr.write('Unexpected status code: %d\n' % response.status_code)
        sys.stderr.write('Response text:\n')
        sys.stderr.write(response.text + "\n")
        raise FailedAPICallException()
    else:
        sys.stdout.write(response.text + "\n")

# TODO: This function's name is no longer very accurate.  As soon as it is
# safe, we should change it to something more generic.
def object_url(*args):
    # Prefer an environmental variable for getting the endpoint if available.
    # url = os.environ.get('HAAS_ENDPOINT')
    url = 'http://127.0.0.1:5000' # 528
    if url is None:
        url = cfg.get('client', 'endpoint')
    for arg in args:
        url += '/' + urllib.quote(arg, '')
    return url


# Helper functions for making HTTP requests against the API.
#    Uses the global variable `http_client` to make the request.
#
#    Arguments:
#
#        `url` - The url to make the request to
#        `data` - the body of the request (for PUT, POST and DELETE)
#        `params` - query parameters (for GET)

def do_put(url, data={}):
    check_status_code(requests.request('PUT', url, data=json.dumps(data))) # 528


def do_post(url, data={}):
    check_status_code(requests.request('POST', url, data=json.dumps(data)))


def do_get(url, params=None):
    check_status_code(requests.request('GET', url, params=params))
    return requests.request('GET', url, params=params).json()


def do_delete(url):
    check_status_code(requests.request('DELETE', url))

def serve(port):
    try:
        port = schema.And(
            schema.Use(int),
            lambda n: MIN_PORT_NUMBER <= n <= MAX_PORT_NUMBER).validate(port)
    except schema.SchemaError:
        raise InvalidAPIArgumentsException(
            'Error: Invaid port. Must be in the range 1-65535.'
        )
    except Exception as e:
        sys.exit('Unxpected Error!!! \n %s' % e)

    """Start the HaaS API server"""
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
    else:
        debug = False
    # We need to import api here so that the functions within it get registered
    # (via `rest_call`), though we don't use it directly:
    from haas import model, api, rest
    server.init()
    migrations.check_db_schema()
    server.stop_orphan_consoles()
    rest.serve(port, debug=debug)

def serve_networks():
    """Start the HaaS networking server"""
    from haas import model, deferred
    from time import sleep
    server.init()
    server.register_drivers()
    server.validate_state()
    model.init_db()
    migrations.check_db_schema()
    while True:
        # Empty the journal until it's empty; then delay so we don't tight
        # loop.
        while deferred.apply_networking():
            pass
        sleep(2)

def user_create(username, password, is_admin):
    """Create a user <username> with password <password>.

    <is_admin> may be either "admin" or "regular", and determines whether
    the user has administrative priveledges.
    """
    url = object_url('/auth/basic/user', username)
    if is_admin not in ('admin', 'regular'):
        raise InvalidAPIArgumentsException(
            "is_admin must be either 'admin' or 'regular'"
        )
    do_put(url, data={
        'password': password,
        'is_admin': is_admin == 'admin',
    })


def network_create(network, owner, access, net_id):
    """Create a link-layer <network>.  See docs/networks.md for details"""
    url = object_url('network', network)
    do_put(url, data={'owner': owner,
                      'access': access,
                      'net_id': net_id})


def network_create_simple(network, project):
    """Create <network> owned by project.  Specific case of network_create"""
    url = object_url('network', network)
    do_put(url, data={'owner': project,
                      'access': project,
                      'net_id': ""})


def network_delete(network):
    """Delete a <network>"""
    url = object_url('network', network)
    do_delete(url)


def user_delete(username):
    """Delete the user <username>"""
    url = object_url('/auth/basic/user', username)
    do_delete(url)



def list_projects():
    """List all projects"""
    url = object_url('projects')
    do_get(url)



def user_add_project(user, project):
    """Add <user> to <project>"""
    url = object_url('/auth/basic/user', user, 'add_project')
    do_post(url, data={'project': project})



def user_remove_project(user, project):
    """Remove <user> from <project>"""
    url = object_url('/auth/basic/user', user, 'remove_project')
    do_post(url, data={'project': project})



def network_grant_project_access(project, network):
    """Add <project> to <network> access"""
    url = object_url('network', network, 'access', project)
    do_put(url)



def network_revoke_project_access(project, network):
    """Remove <project> from <network> access"""
    url = object_url('network', network, 'access', project)
    do_delete(url)



def project_create(project):
    """Create a <project>"""
    url = object_url('project', project)
    do_put(url)



def project_delete(project):
    """Delete <project>"""
    url = object_url('project', project)
    do_delete(url)



def headnode_create(headnode, project, base_img):
    """Create a <headnode> in a <project> with <base_img>"""
    url = object_url('headnode', headnode)
    do_put(url, data={'project': project,
                      'base_img': base_img})



def headnode_delete(headnode):
    """Delete <headnode>"""
    url = object_url('headnode', headnode)
    do_delete(url)



def project_connect_node(project, node):
    """Connect <node> to <project>"""
    url = object_url('project', project, 'connect_node')
    do_post(url, data={'node': node})



def project_detach_node(project, node):
    """Detach <node> from <project>"""
    url = object_url('project', project, 'detach_node')
    do_post(url, data={'node': node})



def headnode_start(headnode):
    """Start <headnode>"""
    url = object_url('headnode', headnode, 'start')
    do_post(url)



def headnode_stop(headnode):
    """Stop <headnode>"""
    url = object_url('headnode', headnode, 'stop')
    do_post(url)



def node_register(node, subtype, *args):
    """Register a node named <node>, with the given type
        if obm is of type: ipmi then provide arguments
        "ipmi", <hostname>, <ipmi-username>, <ipmi-password>
    """
    obm_api = "http://schema.massopencloud.org/haas/v0/obm/"
    obm_types = ["ipmi", "mock"]
    # Currently the classes are hardcoded
    # In principle this should come from api.py
    # In future an api call to list which plugins are active will be added.

    if subtype in obm_types:
        if len(args) == 3:
            obminfo = {"type": obm_api + subtype, "host": args[0],
                       "user": args[1], "password": args[2]
                       }
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 3 arguments\n')
            sys.stderr.write('<hostname> <ipmi-username> <ipmi-password>\n')
            return
    else:
        sys.stderr.write('ERROR: Wrong OBM subtype supplied\n')
        sys.stderr.write('Supported OBM sub-types: ipmi, mock\n')
        return

    url = object_url('node', node)
    do_put(url, data={"obm": obminfo})



def node_delete(node):
    """Delete <node>"""
    url = object_url('node', node)
    do_delete(url)



def node_power_cycle(node):
    """Power cycle <node>"""
    url = object_url('node', node, 'power_cycle')
    do_post(url)



def node_power_off(node):
    """Power off <node>"""
    url = object_url('node', node, 'power_off')
    do_post(url)



def node_set_bootdev(node, dev):
    """
    Sets <node> to boot from <dev> persistenly

    eg; haas node_set_bootdev dell-23 pxe
    for IPMI, dev can be set to disk, pxe, or none
    """
    url = object_url('node', node, 'boot_device')
    do_put(url, data={'bootdev': dev})



def node_register_nic(node, nic, macaddr):
    """
    Register existence of a <nic> with the given <macaddr> on the given <node>
    """
    url = object_url('node', node, 'nic', nic)
    do_put(url, data={'macaddr': macaddr})



def node_delete_nic(node, nic):
    """Delete a <nic> on a <node>"""
    url = object_url('node', node, 'nic', nic)
    do_delete(url)



def headnode_create_hnic(headnode, nic):
    """Create a <nic> on the given <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_put(url)



def headnode_delete_hnic(headnode, nic):
    """Delete a <nic> on a <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_delete(url)



def node_connect_network(node, nic, network, channel):
    """Connect <node> to <network> on given <nic> and <channel>"""
    url = object_url('node', node, 'nic', nic, 'connect_network')
    do_post(url, data={'network': network,
                       'channel': channel})



def node_detach_network(node, nic, network):
    """Detach <node> from the given <network> on the given <nic>"""
    url = object_url('node', node, 'nic', nic, 'detach_network')
    do_post(url, data={'network': network})



def headnode_connect_network(headnode, nic, network):
    """Connect <headnode> to <network> on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', nic, 'connect_network')
    do_post(url, data={'network': network})



def headnode_detach_network(headnode, hnic):
    """Detach <headnode> from the network on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', hnic, 'detach_network')
    do_post(url)



def metadata_set(node, label, value):
    """Register metadata with <label> and <value> with <node> """
    url = object_url('node', node, 'metadata', label)
    do_put(url, data={'value': value})



def metadata_delete(node, label):
    """Delete metadata with <label> from a <node>"""
    url = object_url('node', node, 'metadata', label)
    do_delete(url)



def switch_register(switch, subtype, *args):
    """Register a switch with name <switch> and
    <subtype>, <hostname>, <username>,  <password>
    eg. haas switch_register mock03 mock mockhost01 mockuser01 mockpass01

    FIXME: current design needs to change. CLI should not know about every
    backend. Ideally, this should be taken care of in the driver itself or
    client library (work-in-progress) should manage it.
    """
    switch_api = "http://schema.massopencloud.org/haas/v0/switches/"
    if subtype == "nexus":
        if len(args) == 4:
            switchinfo = {
                "type": switch_api + subtype,
                "hostname": args[0],
                "username": args[1],
                "password": args[2],
                "dummy_vlan": args[3]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 4 arguments\n'
                             '<hostname> <username> <password>'
                             '<dummy_vlan_no>\n')
            return
    elif subtype == "mock":
        if len(args) == 3:
            switchinfo = {"type": switch_api + subtype, "hostname": args[0],
                          "username": args[1], "password": args[2]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 3 arguments\n')
            sys.stderr.write('<hostname> <username> <password>\n')
            return
    elif subtype == "powerconnect55xx":
        if len(args) == 3:
            switchinfo = {"type": switch_api + subtype, "hostname": args[0],
                          "username": args[1], "password": args[2]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 3 arguments\n'
                             '<hostname> <username> <password>\n')
            return
    elif subtype == "brocade":
        if len(args) == 4:
            switchinfo = {"type": switch_api + subtype, "hostname": args[0],
                          "username": args[1], "password": args[2],
                          "interface_type": args[3]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 4 arguments\n'
                             '<hostname> <username> <password> '
                             '<interface_type>\n'
                             'NOTE: interface_type refers '
                             'to the speed of the switchports\n '
                             'ex. TenGigabitEthernet, FortyGigabitEthernet, '
                             'etc.\n')
            return
    else:
        sys.stderr.write('ERROR: Invalid subtype supplied\n')
        return
    url = object_url('switch', switch)
    do_put(url, data=switchinfo)



def switch_delete(switch):
    """Delete a <switch> """
    url = object_url('switch', switch)
    do_delete(url)



def list_switches():
    """List all switches"""
    url = object_url('switches')
    do_get(url)



def port_register(switch, port):
    """Register a <port> with <switch> """
    url = object_url('switch', switch, 'port', port)
    do_put(url)



def port_delete(switch, port):
    """Delete a <port> from a <switch>"""
    url = object_url('switch', switch, 'port', port)
    do_delete(url)



def port_connect_nic(switch, port, node, nic):
    """Connect a <port> on a <switch> to a <nic> on a <node>"""
    url = object_url('switch', switch, 'port', port, 'connect_nic')
    do_post(url, data={'node': node, 'nic': nic})



def port_detach_nic(switch, port):
    """Detach a <port> on a <switch> from whatever's connected to it"""
    url = object_url('switch', switch, 'port', port, 'detach_nic')
    do_post(url)



def list_network_attachments(network, project):
    """List nodes connected to a network
    <project> may be either "all" or a specific project name.
    """
    url = object_url('network', network, 'attachments')

    if project == "all":
        do_get(url)
    else:
        do_get(url, params={'project': project})



def list_nodes(is_free):
    """List all nodes or all free nodes

    <is_free> may be either "all" or "free", and determines whether
        to list all nodes or all free nodes.
    """
    if is_free not in ('all', 'free'):
        raise InvalidAPIArgumentsException(
            "is_free must be either 'all' or 'free'"
        )
    url = object_url('nodes', is_free)
    do_get(url)



def list_project_nodes(project):
    """List all nodes attached to a <project>"""
    url = object_url('project', project, 'nodes')
    do_get(url)


def list_project_networks(project):
    """List all networks attached to a <project>"""
    url = object_url('project', project, 'networks')
    do_get(url)


def show_switch(switch):
    """Display information about <switch>"""
    url = object_url('switch', switch)
    do_get(url)



def list_networks():
    """List all networks"""
    url = object_url('networks')
    do_get(url)



def show_network(network):
    """Display information about <network>"""
    url = object_url('network', network)
    do_get(url)



def show_node(node):
    """Display information about a <node>"""
    url = object_url('node', node)
    do_get(url)



def list_project_headnodes(project):
    """List all headnodes attached to a <project>"""
    url = object_url('project', project, 'headnodes')
    do_get(url)



def show_headnode(headnode):
    """Display information about a <headnode>"""
    url = object_url('headnode', headnode)
    do_get(url)



def list_headnode_images():
    """Display registered headnode images"""
    url = object_url('headnode_images')
    do_get(url)



def show_console(node):
    """Display console log for <node>"""
    url = object_url('node', node, 'console')
    do_get(url)



def start_console(node):
    """Start logging console output from <node>"""
    url = object_url('node', node, 'console')
    do_put(url)



def stop_console(node):
    """Stop logging console output from <node> and delete the log"""
    url = object_url('node', node, 'console')
    do_delete(url)



def create_admin_user(username, password):
    """Create an admin user. Only valid for the database auth backend.

    This must be run on the HaaS API server, with access to haas.cfg and the
    database. It will create an user named <username> with password
    <password>, who will have administrator priviledges.

    This command should only be used for bootstrapping the system; once you
    have an initial admin, you can (and should) create additional users via
    the API.
    """
    if not config.cfg.has_option('extensions', 'haas.ext.auth.database'):
        sys.exit("'make_inital_admin' is only valid with the database auth"
                 " backend.")
    from haas import model
    from haas.model import db
    from haas.ext.auth.database import User
    model.init_db()
    db.session.add(User(label=username, password=password, is_admin=True))
    db.session.commit()



def help(*commands):
    """Display usage of all following <commands>, or of all commands if none
    are given
    """
    if not commands:
        sys.stdout.write('Usage: %s <command> <arguments...> \n' % sys.argv[0])
        sys.stdout.write('Where <command> is one of:\n')
        commands = sorted(command_dict.keys())
    for name in commands:
        # For each command, print out a summary including the name, arguments,
        # and the docstring (as a #comment).
        sys.stdout.write('  %s\n' % usage_dict[name])
        sys.stdout.write('      %s\n' % command_dict[name].__doc__)
