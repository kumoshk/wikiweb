# wikiweb
Python3.x modules for creating databases with contexts, nodes, and relations between nodes. A wikiweb is used to make database projects with nodes related through contexts (it's not actually a wiki, athough I may adapt it for wiki use in future), and the features related to users logging in are not finished (don't use them).

See documentation.txt for information on wikiweb and how to use it.

To discuss this project, you may do so at `http://wikiweb.growspice.com`.
(Yes, you have to register, and then become a member by posting in the Support forum that you agree to the rules before posting.)

Dependencies:
* natsort (sudo pip3 install natsort)
* bcrypt (sudo pip3 install bcrypt)
* (optional) dill (sudo apt-get install dill); to use dill instead of pickle, you'll need to edit the import section of wikiweb.py
