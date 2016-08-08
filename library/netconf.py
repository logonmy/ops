#!/usr/bin/env python
# -*- coding:utf8 -*-

from ncclient import manager
from configs import netconf_config
import xmltodict


class Netconf:
    def __init__(self, host, device):
        device_config = netconf_config.get(device)
        self.connect = manager.connect(host=host,
                                       port=device_config.get('port'),
                                       username=device_config.get('user'),
                                       password=device_config.get('password'),
                                       hostkey_verify=False,
                                       allow_agent=False,
                                       look_for_keys=False,
                                       device_params={'name': '%s' % device})

    @staticmethod
    def find_in_data(query, ele, ns='http://www.h3c.com/netconf/data:1.0'):
        return ele.find('.//{%s}%s' % (ns, query))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connect.connected:
            self.connect.__exit__()
        return False

    def get_all(self):
        return self.connect.get().xml

    def get_running_config(self):
        return self.connect.get_config(source='running').xml


class Nexus(Netconf):
    def __init__(self, host, device='nexus'):
        Netconf.__init__(self, host, device)
        self.exec_conf_prefix = """
                                      <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
                                        <configure xmlns="http://www.cisco.com/nxos:1.0:vlan_mgr_cli">
                                          <__XML__MODE__exec_configure>
                                """
        self.exec_conf_postfix = """
                                          </__XML__MODE__exec_configure>
                                        </configure>
                                      </config>
                                """

    def enable_vlan(self, vlanid, vlanname):
        cmd_vlan_conf_snippet = """
                                        <vlan>
                                          <vlan-id-create-delete>
                                            <__XML__PARAM_value>%s</__XML__PARAM_value>
                                            <__XML__MODE_vlan>
                                              <name>
                                                <vlan-name>%s</vlan-name>
                                              </name>
                                              <state>
                                                <vstate>active</vstate>
                                              </state>
                                              <no>
                                                <shutdown/>
                                              </no>
                                            </__XML__MODE_vlan>
                                          </vlan-id-create-delete>
                                        </vlan>
                                  """
        confstr = cmd_vlan_conf_snippet % (vlanid, vlanname)
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xmltodict.parse(xml_raw.data_xml)

    def enable_vlan_interface(self, interface, vlanid):
        cmd_vlan_int_snippet = """
                                      <interface>
                                        <ethernet>
                                          <interface>%s</interface>
                                          <__XML__MODE_if-ethernet-switch>
                                            <switchport></switchport>
                                            <switchport>
                                              <trunk>
                                                <allowed>
                                                  <vlan>
                                                    <__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
                                                      <allow-vlans>%s</allow-vlans>
                                                    </__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
                                                  </vlan>
                                                </allowed>
                                              </trunk>
                                            </switchport>
                                          </__XML__MODE_if-ethernet-switch>
                                        </ethernet>
                                      </interface>
                                """
        confstr = cmd_vlan_int_snippet % (interface, vlanid)
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xmltodict.parse(xml_raw.data_xml)

    def disable_vlan_interface(self, interface, vlanid):
        cmd_no_vlan_int_snippet = """
                                        <interface>
                                            <ethernet>
                                              <interface>%s</interface>
                                              <__XML__MODE_if-ethernet-switch>
                                                <switchport></switchport>
                                                <switchport>
                                                  <trunk>
                                                    <notallowed>
                                                      <vlan>
                                                        <__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
                                                          <allow-vlans>%s</allow-vlans>
                                                        </__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
                                                      </vlan>
                                                    </notallowed>
                                                  </trunk>
                                                <switchport>
                                              </__XML__MODE_if-ethernet-switch>
                                            </ethernet>
                                          </interface>
                                 """
        confstr = cmd_no_vlan_int_snippet % (interface, vlanid)
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xmltodict.parse(xml_raw.data_xml)

    def get_mac_address_table(self):
        cmd_mac_address_snippt = """
                                  <show>
                                    <mac>
                                      <address-table/>
                                     </mac>
                                  </show>
                                    """
        xml_raw = self.connect.get(("subtree", cmd_mac_address_snippt))
        return xmltodict.parse(xml_raw.data_xml)

    def get_vlan_list(self):
        cmd_show_vlans = """
                                <show>
                                    <vlan/>
                                </show>
                            """
        xml_raw = self.connect.get(("subtree", cmd_show_vlans))
        return xmltodict.parse(str(xml_raw))

    def exec_commond(self, command_list):
        cmd_snippt = """
                        <?xml version="1.0"?>
                            <nf:rpc xmlns="http://www.cisco.com/nxos:1.0:if_manager"
                                        xmlns:nf="urn:ietf:params:xml:ns:netconf:base:1.0"
                                        xmlns:nxos="http://www.cisco.com/nxos:1.0"
                                        message-id="110">
                              <nxos:exec-command>
                                <nxos:cmd>
                                  %s
                                </nxos:cmd>
                              </nxos:exec-command>
                            </nf:rpc>
                            ]]>]]>
                    """
        confstr = cmd_snippt % ';'.join(command_list)
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xmltodict.parse(xml_raw.data_xml)


class H3c(Netconf):
    def __init__(self, host, device='h3c'):
        Netconf.__init__(self, host, device)
        self.exec_conf_prefix = """
                                    <config>
                                        <top xmlns="http://www.h3c.com/netconf/config:1.0">
                                """
        self.exec_conf_postfix = """
                                        </top>
                                      </config>
                                """
        self.get_prefix = """<top xmlns="http://www.h3c.com/netconf/data:1.0">"""
        self.get_postfix = """</top>"""

    def enable_vlan(self, vlanid, vlanname):
        vlan_xml = '''
                        <VLAN nc:operation="merge"><VLANs><VLANID><Name>%s</Name><Description>%s</Description><ID>%s</ID></VLANID></VLANs></VLAN>
                    '''
        confstr = vlan_xml % (vlanname, vlanname, vlanid)
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xml_raw

    def modify_vlan_access(self, interface_name, vlanid):
        iface_index = self.get_iface_index(interface_name=interface_name)
        if iface_index is None:
            return
        vlan_xml = '''
                        <Ifmgr><Interfaces><Interface><IfIndex>%s</IfIndex><LinkType>1</LinkType></Interface></Interfaces></Ifmgr>
                        <VLAN><AccessInterfaces><Interface><IfIndex>%s</IfIndex><PVID>%s</PVID></Interface></AccessInterfaces></VLAN>
                        <Ifmgr><Interfaces><Interface><AdminStatus>1</AdminStatus><IfIndex>%s</IfIndex><Description>up</Description></Interface></Interfaces></Ifmgr>
                    '''
        confstr = vlan_xml % (iface_index, iface_index, vlanid, iface_index)
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xml_raw

    def modify_vlan_trunk(self, interface_name, vlanid_str):
        iface_index = self.get_iface_index(interface_name=interface_name)
        if iface_index is None:
            return
        vlan_xml = '''
                        <Ifmgr><Interfaces><Interface><IfIndex>%s</IfIndex><LinkType>2</LinkType></Interface></Interfaces></Ifmgr>
                        <VLAN><TrunkInterfaces><Interface><IfIndex>%s</IfIndex><PermitVlanList>%s</PermitVlanList></Interface></TrunkInterfaces></VLAN>
                        <Ifmgr><Interfaces><Interface><AdminStatus>1</AdminStatus><IfIndex>%s</IfIndex><Description>up</Description></Interface></Interfaces></Ifmgr>
                    '''
        confstr = vlan_xml % (iface_index, iface_index, vlanid_str,
                              iface_index)
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xml_raw

    def get_vlan_info(self, interface_name):
        iface_index = self.get_iface_index(interface_name=interface_name)
        if iface_index is None:
            return
        interface_filter = '''<VLAN><Interfaces><Interface><IfIndex>98</IfIndex></Interface></Interfaces></VLAN>''' % int(
            iface_index)
        xml_raw = self.connect.get(
            ('subtree', self.get_prefix + interface_filter + self.get_postfix))
        return xmltodict.parse(xml_raw.data_xml)

    def get_vlan_list(self):
        vlans_filter = '''
                            <VLAN>
                                <VLANs>
                                </VLANs>
                            </VLAN>
                       '''
        xml_raw = self.connect.get(
            ('subtree', self.get_prefix + vlans_filter + self.get_postfix))
        return xmltodict.parse(xml_raw.data_xml)

    def get_interface_list(self):
        interface_filter = '''
                                    <Ifmgr><Interfaces><Interface><Name/></Interface></Interfaces></Ifmgr>
                            '''
        xml_raw = self.connect.get(
            ('subtree', self.get_prefix + interface_filter + self.get_postfix))
        return xmltodict.parse(xml_raw.data_xml)

    def get_inventory(self):
        inventory_filter = '''
                                    <LLDP><Inventory><SoftwareRev/><SerialNum/><ModelName/></Inventory></LLDP>
                                    <Device><Base><HostName/><LocalTime/><Uptime/></Base></Device>
                            '''
        xml_raw = self.connect.get(
            ('subtree', self.get_prefix + inventory_filter + self.get_postfix))
        return xmltodict.parse(xml_raw.data_xml)

    def get_iface_index(self, interface_name):
        iface_filter = '''<Ifmgr><Interfaces><Interface><Name>%s</Name></Interface></Interfaces></Ifmgr>''' % interface_name
        xml_raw = self.connect.get(
            ('subtree', self.get_prefix + iface_filter + self.get_postfix))
        data = self.find_in_data('IfIndex', xml_raw.data_ele)
        if data is None:
            return None
        return data.text

    def get_interface_info(self, interface_name):
        iface_index = self.get_iface_index(interface_name=interface_name)
        if iface_index is None:
            return
        interface_filter = '''<Ifmgr><Interfaces><Interface><IfIndex>%s</IfIndex></Interface></Interfaces></Ifmgr>''' % int(
            iface_index)
        xml_raw = self.connect.get(
            ('subtree', self.get_prefix + interface_filter + self.get_postfix))
        return xmltodict.parse(xml_raw.data_xml)

    def down(self, interface_name):
        iface_index = self.get_iface_index(interface_name=interface_name)
        if iface_index is None:
            return
        vlan_xml = '''<Ifmgr><Interfaces><Interface><AdminStatus>2</AdminStatus><IfIndex>%s</IfIndex><Description>down</Description></Interface></Interfaces></Ifmgr>'''
        confstr = vlan_xml % iface_index
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xml_raw

    def up(self, interface_name):
        iface_index = self.get_iface_index(interface_name=interface_name)
        if iface_index is None:
            return
        vlan_xml = '''<Ifmgr><Interfaces><Interface><AdminStatus>1</AdminStatus><IfIndex>%s</IfIndex><Description>up</Description></Interface></Interfaces></Ifmgr>'''
        confstr = vlan_xml % iface_index
        confstr = self.exec_conf_prefix + confstr + self.exec_conf_postfix
        xml_raw = self.connect.edit_config(target='running', config=confstr)
        return xml_raw

    def exec_commond(self, command_list):
        display_command = '\n'.join(command_list)
        return self.connect.dispatch(display_command)


if __name__ == '__main__':
    h3c = H3c(host='10.3.128.128')
    print h3c.get_inventory()
