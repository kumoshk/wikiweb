# wikiweb
Python3.x modules for creating databases with contexts, nodes, and relations between nodes. This is not actually wiki software, currently, but wikiweb is meant to be a new word with only some of the connotations of wikis. The features related to users logging in are not finished (don't use them).

See documentation.txt.

To discuss this project, you may do so at `http://wikiweb.growspice.com`. (Yes, you have to register, and then become a member by posting in the Support forum that you agree to the rules before posting.)

Dependencies:
* natsort (sudo pip3 install natsort)
* bcrypt (sudo pip3 install bcrypt)
* (optional) dill (sudo apt-get install dill); to use dill instead of pickle, you'll need to edit the import section of wikiweb.py
