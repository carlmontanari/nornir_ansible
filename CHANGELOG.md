CHANGELOG
=======

# 2021.07.30
- Added support for hosts in inventory that only have an IP address and no "ansible_host" field -- see #47


# 2020.09.26
- Add python3.9 to ci
- Replace os.blah with Pathlib everywhere
- Fix issue where hostsfile being in the same directory as the script was causing inventory to not pick up group/host
 vars (thank you `jpmondet` on ntc slack!)


# 2020.07.20
- Added support for variables defined in directories courtesy of [Dylan Hamel](https://github.com/DylanHamel) 


# 2020.05.03
- Fixing registration via entrypoint
- Fix imports from cleaned up Nornir core (hosts/groups/etc. -- mostly vars for typing purposes)
- Actually serialize/deserialize things now to match the new nornir setup
- Fix directory structure to match traditional x/plugins/inventory paths


# 2020.04.11
- First (very test/alpha) release of nornir_ansible