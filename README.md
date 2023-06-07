# host_finder_api
An API that searches inside a MySQL database for a network host and returns information about it

In my implementation I have the ARP table and interface information from Cisco access switches stored inside a mysql database.This is done using Ansible and is not included in this repository. The database has a table that contains the mac address, IP address, VLAN and port description. It can search by IP address, VLAN and the MAC address pattern. The IP address must be an exact match and the VLAN can not be more than 3 digits.

Useful tool to give to first level support to find information on hosts.

