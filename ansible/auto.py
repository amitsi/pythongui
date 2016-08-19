#!/usr/bin/python
""" Auto-vLAG"""

import shlex


def pn_cli(module):
    """ Build the cli command """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    cli = '/usr/bin/cli --quiet '
    if username and password:
        cli += '--user %s:%s ' % (username, password)

    return cli


def get_ports(module, localswitch, host1, host2):

    cli = pn_cli(module)
    cli += ' switch %s port-show hostname %s' % (localswitch, host1)
    cli += ' format port no-show-headers '

    cli = shlex.split(cli)
    out = module.run_command(cli)[1]
    h1_ports = out.split()

    cli = pn_cli(module)
    cli += ' switch %s port-show hostname %s' % (localswitch, host2)
    cli += ' format port no-show-headers '

    cli = shlex.split(cli)
    out = module.run_command(cli)[1]
    h2_ports = out.split()

    ports = h1_ports + h2_ports
    ports = ','.join(ports)

    return ports


def cluster(module, name, node1, node2):

    cli = pn_cli(module)

    cli += ' switch-local cluster-create name %s ' % name
    cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)

    cli = shlex.split(cli)

    rc, out, err = module.run_command(cli)

    if out:
        return out
    if err:
        return err
    else:
        return 'Success'


def trunk(module, switch, name, ports):

    cli = pn_cli(module)
    cli += ' switch %s trunk-create name %s ' % (switch, name)
    cli += ' ports %s ' % ports

    cli = shlex.split(cli)

    rc, out, err = module.run_command(cli)
    if out:
        return out
    if err:
        return err
    else:
        return 'Success'


def vlag(module, switch, name, peer, port, peer_port):

    cli = pn_cli(module)
    cli += ' switch %s vlag-create name %s port %s ' % (switch, name, port)
    cli += ' peer-port %s peer-switch %s mode active-active' % (peer_port, peer)

    cli = shlex.split(cli)

    rc, out, err = module.run_command(cli)
    if out:
        return out
    if err:
        return err
    else:
        return 'Success'


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_local_switch=dict(required=True, type='str'),
            pn_peer_switch=dict(required=True, type='str'),
            pn_switch1=dict(required=True, type='str'),
            pn_switch2=dict(required=True, type='str'),
        )
    )

    local_switch = module.params['pn_local_switch']
    peer_switch = module.params['pn_peer_switch']
    switch1 = module.params['pn_switch1']
    switch2 = module.params['pn_switch2']

    scluster = cluster(module, 'spinecluster', local_switch, peer_switch)
    msg1 = scluster.strip()

    lcluster = cluster(module, 'leafcluster', switch1, switch2)
    msg2 = lcluster.strip()

    s1ports = get_ports(module, local_switch, switch1, switch2)
    s2ports = get_ports(module, peer_switch, switch1, switch2)
    s3ports = get_ports(module, switch1, local_switch, peer_switch)
    s4ports = get_ports(module, switch2, local_switch, peer_switch)
    
    trunk1 = trunk(module, local_switch, 'spine1-to-leaf', s1ports)
    msg3 = trunk1.strip()
    trunk2 = trunk(module, peer_switch, 'spine2-to-leaf', s2ports)
    msg4 = trunk2.strip()
    trunk3 = trunk(module, switch1, 'leaf1-to-spine', s3ports)
    msg5 = trunk3.strip()
    trunk4 = trunk(module, switch2, 'leaf2-to-spine', s4ports)
    msg6 = trunk4.strip()
    
    vlag1 = vlag(module, local_switch, 'spine-to-leaf', peer_switch, 'spine1-to-leaf', 'spine2-to-leaf')
    msg7 = vlag1.strip()
    vlag2 = vlag(module, switch1, 'leaf-to-spine', switch2, 'spine1-to-leaf', 'spine2-to-leaf')
    msg8 = vlag2.strip()
    
    message = '%s. %s. %s. %s. %s. %s. %s. %s.' % (msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8)

    msg = msg1 + msg2

    module.exit_json(
        msg=msg
    )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
