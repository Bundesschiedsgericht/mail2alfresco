# mail2alfresco

This is a script that takes a mail via pipe (stdin) and uploads the contents to an alfresco document library. It decrypts OpenPGP messages both PGP/MIME and i
nline. It looks out for cases mentioned in the mail's subject and automatically creates a new folder for the new message.

This script was written by Stefan Thöni for the [Bundesschiedsgericht of Piratenpartei Deutschland](https://bsg.piratenpartei.de).

## Prerequeisites

The following software is needed:
- python 2.x
- postfix (or another MTA the is able to pipe messages)

The following python packages must be installed:
- requests
- python-gnupg

## Installation

Copy the `m2a` bash script to `/usr/bin` and make it executable by everyone. Adapt the variables and path of mail2alfresco in the script.

Edit `/etc/aliases` to add the line `useraddress: | m2a` where useraddress is the user part of the mail address.

Create a new unprivileges user `m2a`. Create a folder `gnupghome/.config/python-gnupg/` in the installation path of mail2alfresco and make it writable by that user. Create a gnupg keyring in that folder and import your secret key. The secret key must be accessible without passphrase.


