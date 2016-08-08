# -*- coding: utf-8 -*-
#
# H3C Technologies Co., Limited Copyright 2003-2015, All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import urllib2
import ssl
from string import Template
from xml.etree import ElementTree
from oslo_log import log as logging
from neutron.plugins.ml2.drivers.hp.common import tools

LOG = logging.getLogger(__name__)

MESSAGE_ID = "404"
LANGUAGE_CH = "zh-cn"
LANGUAGE_EN = "en"

NS_HELLO = "{http://www.%s.com/netconf/base:1.0}"
NS_DATA = "{http://www.%s.com/netconf/data:1.0}"
SESSION = """<env:Envelope
  xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Header>
    <auth:Authentication env:mustUnderstand="1"
    xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
      <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
      <auth:Language>$Language</auth:Language>
    </auth:Authentication>
  </env:Header>
  <env:Body>
    <rpc message-id="$messageid"
    xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
       <get-sessions/>
    </rpc>
   </env:Body>
</env:Envelope>
"""
HELLO = """<env:Envelope
 xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
   <env:Header>
      <auth:Authentication env:mustUnderstand="1"
      xmlns:auth="http://www.%s.com/netconf/base:1.0">
         <auth:UserName>%s</auth:UserName>
         <auth:Password>%s</auth:Password>
      </auth:Authentication>
   </env:Header>
   <env:Body>
      <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
         <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
         </capabilities>
      </hello>
   </env:Body>
</env:Envelope>"""

CLOSE = """<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
   <env:Header>
      <auth:Authentication env:mustUnderstand="1"
      xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
         <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
         <auth:Language>$Language</auth:Language>
      </auth:Authentication>
   </env:Header>
   <env:Body>
     <rpc message-id="$messageid"
          xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
       <close-session/>
     </rpc>
   </env:Body>
</env:Envelope>"""

EDIT_HEAD = """<env:Envelope
xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Header>
    <auth:Authentication env:mustUnderstand="1"
     xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
      <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
      <auth:Language>$Language</auth:Language>
    </auth:Authentication>
  </env:Header>
  <env:Body>
    <rpc message-id="$messageid"
      xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <edit-config>
             <target>
          <running/>
        </target>
            <default-operation>merge</default-operation>
        <test-option>set</test-option>
        <error-option>continue-on-error</error-option>
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.$OEM.com/netconf/config:1.0" >"""

EDIT_TAIL = """ </top>
        </config>
      </edit-config>
    </rpc>
  </env:Body>
</env:Envelope>"""

GET_HEADER = """<env:Envelope
  xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Header>
    <auth:Authentication env:mustUnderstand="1"
     xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
      <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
      <auth:Language>$Language</auth:Language>
    </auth:Authentication>
  </env:Header>
  <env:Body>
    <rpc message-id="$messageid"
    xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <get>
        <filter type="subtree">
          <top xmlns="http://www.$OEM.com/netconf/data:1.0"
          xmlns:h3c="http://www.$OEM.com/netconf/data:1.0"
          xmlns:base="http://www.$OEM.com/netconf/base:1.0"
          xmlns:netconf="urn:ietf:params:xml:ns:netconf:base:1.0">"""

GET_TAIL = """</top></filter>
         </get>
      </rpc>
   </env:Body>
</env:Envelope>"""

GET_BULK_HEADER = """<env:Envelope
xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Header>
    <auth:Authentication env:mustUnderstand="1"
    xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
      <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
      <auth:Language>$Language</auth:Language>
    </auth:Authentication>
  </env:Header>
  <env:Body>
    <rpc message-id="$messageid"
    xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <get-bulk>
        <filter type="subtree">
          <top xmlns="http://www.$OEM.com/netconf/data:1.0"
          xmlns:h3c="http://www.$OEM.com/netconf/data:1.0"
          xmlns:base="http://www.$OEM.com/netconf/base:1.0"
          xmlns:netconf="urn:ietf:params:xml:ns:netconf:base:1.0">"""

GET_BULK_TAIL = """</top></filter>
         </get-bulk>
      </rpc>
   </env:Body>
</env:Envelope>"""

CLI_EXEC_HEAD = """<env:Envelope
 xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
   <env:Header>
      <auth:Authentication env:mustUnderstand="1"
      xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
         <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
         <auth:Language>$Language</auth:Language>
      </auth:Authentication>
   </env:Header>
   <env:Body>
      <rpc message-id="$messageid"
      xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
         <CLI>
          <Execution>"""

CLI_EXEC_TAIL = """</Execution>
        </CLI>
      </rpc>
   </env:Body>
</env:Envelope>"""

CLI_CONF_HEAD = """<env:Envelope
 xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
   <env:Header>
      <auth:Authentication env:mustUnderstand="1"
       xmlns:auth="http://www.$OEM.com/netconf/base:1.0">
         <auth:AuthInfo>$AuthInfo</auth:AuthInfo>
         <auth:Language>$Language</auth:Language>
      </auth:Authentication>
   </env:Header>
   <env:Body>
      <rpc message-id="$messageid"
       xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
         <CLI>
          <Configuration>"""

CLI_CONF_TAIL = """</Configuration>
        </CLI>
      </rpc>
   </env:Body>
</env:Envelope>"""
NC_VLAN_GROUP = """<VLAN xc:operation='%s'>
                    <VLANs>%s</VLANs>
                 </VLAN>
              """
NC_VLAN = """<VLANID><ID>%s</ID></VLANID>"""

NC_TRUNK_INTERFACE = """<Interface>
                         <IfIndex>%s</IfIndex>
                         <PermitVlanList>%s</PermitVlanList>
                     </Interface>
                  """
NC_VLAN_TRUNK = """<VLAN><TrunkInterfaces>%s</TrunkInterfaces></VLAN>"""
NC_PORT = """<Port><Name>%s</Name><IfIndex></IfIndex></Port>"""
NC_IFINDEX = """<Ifmgr><Ports>%s</Ports></Ifmgr>"""
NC_LINKTYPE_INTERFACE = """<Interface>
                           <IfIndex>%s</IfIndex>
                           <LinkType>%s</LinkType>
                        </Interface>"""
NC_LINKTYPE = """<Ifmgr>
                 <Interfaces>%s</Interfaces>
               </Ifmgr>"""
SOAP_HTTPS_PORT = 832

change_sysname = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <Device>
            <Base>
                <HostName> %s </HostName>
            </Base>
        </Device>
    </top>
</config>
"""
get_vlans = '''
                <top xmlns="http://www.h3c.com/netconf/data:1.0">
                    <VLAN>
                        <VLANs>
                        </VLANs>
                    </VLAN>
                </top>
               '''

add_vlan = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <VLAN>
            <VLANs>
                <VLANID>
                    <ID> %s </ID>
                </VLANID>
            </VLANs>
        </VLAN>
    </top>
</config>
"""

CREATE_AC = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <L2VPN xc:operation="merge">
            <ACs>
                <AC>
                    <IfIndex>{if_index}</IfIndex>
                    <SrvID>{service_id}</SrvID>
                    <VsiName>{vsi_name}</VsiName>
                </AC>
            </ACs>
        </L2VPN>
    </top>
</config>
"""

DELETE_AC = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <L2VPN xc:operation="remove">
            <ACs>
                <AC>
                    <IfIndex>{if_index}</IfIndex>
                    <SrvID>{service_id}</SrvID>
                </AC>
            </ACs>
        </L2VPN>
    </top>
</config>
"""

CREATE_SERVICE = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <L2VPN xc:operation="merge">
            <SRVs>
                <SRV>
                    <IfIndex>{if_index}</IfIndex>
                    <SrvID>{service_id}</SrvID>
                    <Encap>4</Encap>
                    <SVlanRange>{s_vid}</SVlanRange>
                </SRV>
            </SRVs>
        </L2VPN>
    </top>
</config>
"""

DELETE_SERVICE = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <L2VPN xc:operation="remove">
            <SRVs>
                <SRV>
                    <IfIndex>{if_index}</IfIndex>
                    <SrvID>{service_id}</SrvID>
                </SRV>
            </SRVs>
        </L2VPN>
    </top>
</config>
"""

INTERFACE_VLAN_TRUNK_ACCESS = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <Ifmgr xc:operation="merge">
            <Interfaces>
                <Interface>
                    <IfIndex>{if_index}</IfIndex>
                    <LinkType>{link_type}</LinkType>
                </Interface>
            </Interfaces>
        </Ifmgr>
    </top>
</config>
"""

INTERFACE_TRUNK_PERMIT_VLAN = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <VLAN xc:operation="merge">
            <TrunkInterfaces>
                <Interface>
                    <IfIndex>{if_index}</IfIndex>
                    <PermitVlanList>{vlan_list}</PermitVlanList>
                </Interface>
            </TrunkInterfaces>
        </VLAN>
    </top>
</config>
"""

CREATE_VXLAN_VSI = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <VXLAN xc:operation="merge">
          <VXLANs>
              <Vxlan>
                  <VxlanID>{vxlanid}</VxlanID>
                  <VsiName>{vsiname}</VsiName>
              </Vxlan>
          </VXLANs>
        </VXLAN>
      </top>
    </config>
"""

DELETE_VXLAN = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <VXLAN xc:operation="remove">
          <VXLANs>
              <Vxlan>
                  <VxlanID>{vxlanid}</VxlanID>
              </Vxlan>
          </VXLANs>
        </VXLAN>
      </top>
    </config>
"""

CREATE_TUNNEL = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <TUNNEL xc:operation="merge">
          <Tunnels>
              <Tunnel>
                  <ID>{tunnel_id}</ID>
                  <Mode>24</Mode>
                  <IPv4Addr>
                      <SrcAddr>{src_addr}</SrcAddr>
                      <DstAddr>{dst_addr}</DstAddr>
                  </IPv4Addr>
              </Tunnel>
          </Tunnels>
        </TUNNEL>
      </top>
    </config>
"""

DELETE_TUNNEL = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <TUNNEL xc:operation="remove">
          <Tunnels>
              <Tunnel>
                  <ID>{tunnel_id}</ID>
              </Tunnel>
          </Tunnels>
        </TUNNEL>
      </top>
    </config>
"""

RETRIEVE_AVAILABLE_TUNNEL_ID = """
    <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <TUNNEL xmlns:web="http://www.h3c.com/netconf/base:1.0">
                <AvailableTunnelID>
                </AvailableTunnelID>
        </TUNNEL>
    </top>
"""

EDIT_VXLAN_TUNNEL = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <VXLAN xc:operation="merge">
          <Tunnels>
              <Tunnel>
                  <VxlanID>{vxlanid}</VxlanID>
                  <TunnelID>{tunnelid}</TunnelID>
              </Tunnel>
          </Tunnels>
        </VXLAN>
      </top>
    </config>
"""

VSI_OPERATION = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
 xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <top xmlns="http://www.h3c.com/netconf/config:1.0">
    <L2VPN xc:operation="{operation}">
      <VSIs>
        <VSI>
          <VsiName>{vsiname}</VsiName>
        </VSI>
      </VSIs>
    </L2VPN>
  </top>
</config>
"""

RETRIEVE_ALL_INTERFACES = """
    <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Ifmgr xmlns:web="http://www.h3c.com/netconf/base:1.0">
            <Interfaces>
            </Interfaces>
        </Ifmgr>
    </top>
"""

RETRIEVE_SPECIAL_INTERFACES = """
    <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Ifmgr xmlns:web="http://www.h3c.com/netconf/base:1.0">
            <Interfaces>
                <Interface>
                    <IfIndex>{if_index}</IfIndex>
                </Interface>
            </Interfaces>
        </Ifmgr>
    </top>
"""

RETRIEVE_TUNNELS = """
    <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <TUNNEL xmlns:web="http://www.h3c.com/netconf/base:1.0">
                <Tunnels>
                </Tunnels>
        </TUNNEL>
    </top>
"""

CREATE_ACL = """
            <config>
                <top xmlns="http://www.h3c.com/netconf/config:1.0">
                    <ACL>
                        <Groups>
                            <Group>
                                <GroupType>1</GroupType>
                                <GroupID>{acl_num}</GroupID>
                            </Group>
                        </Groups>
                    </ACL>
                </top>
            </config>
        """

display_command = """
                <rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                    <CLI>
                        <Execution> %s </Execution>
                    </CLI>
                </rpc>
                """
