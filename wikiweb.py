import os, re, inspect, fractions, ast, datetime;
import sys, os, random, hashlib, tempfile, shutil;
import bcrypt, natsort;
#import dill as pickle; #We use dill so we can pickle functions and such (they need to be pickled so triggers can be stored). If you don’t want to pickle methods, you can use pickle instead.
import pickle;

"""
This contains the base classes for our data structure.

Wikiweb provides a data structure for relating nodes to each other through relations. Each relation is comprised of a node and a context. A context is the context in which they are related. For instance:
    
Idahoans include me. Idahoans and me are nodes. Include is the context. Each context has a crossed context so you can see how me is related to Idahoans (instead of just the other way around).

This is a client-side prototype that doesn’t particularly do anything special to support big data; it’s not as efficient as it could be (especially with deleting nodes/contexts). It’s not set up in the database fashion that it is intended to be. Nevertheless, it’s still useful as is for a variety of purposes.
"""

class Error(Exception):
    pass;

class NodeExistsError(Error):
    pass;

class UnrelatedError(Error):
    pass;

class ValueError2(Error):
    pass; #This is just used when you’re already catching a ValueError for a different purpose.

class Group(dict):
    #This is a dictionary that can be used a lot like a set, where desired. Adding items (as with a set) makes the added items keys, and the default value the value.
    def __init__(self, default_value=None):
        #If default_value is a class, a new instance of it for each key will be its default value. You might want the default value to be dict or Group, for instance.
        #If default_value is a method, it will be executed for each key upon its creation time and what it returns will be the value.
        dict.__init__(self);
        self.default_value=default_value; #This is the default value when using this as a set or such.
    def __iadd__(self, g):
        self.update(g);
    def __isub__(self, g):
        self.remove(*g);
    def add(self, *args, **kwargs):
        for x in args:
            try:
                val=self.default_value();
            except TypeError:
                val=self.default_value;
            self[x]=val; #If it is already there and has a different value, the value will be reset to the default here.
        for k,v in kwargs.items():
            self[k]=v;
    def remove(self, *args):
        for x in args:
            del self[x];
    def update(self, g):
        try:
            for k,v in g.items():
                self[k]=v;
        except AttributeError:
            for x in g:
                try:
                    val=self.default_value();
                except TypeError:
                    val=self.default_value;
                self[x]=val;

class CrossDict: #This makes it so we don’t have to make another dictionary of all the context names (or delete/add items to it).
    def __init__(self, cnco):
        self.cnco=cnco;
    def __getitem__(self, key):
        if key not in self.cnco:
            raise KeyError("‘"+str(key)+"’");
        else:
            return self.cnco[key].cross.name;
    def __contains__(self, key):
        return key in self.cnco;
    def __setitem__(self, key, value):
        raise ValueError("You cannot change this pretend dictionary, as it’s just for getting.");

class nidDict:
    def __init__(self, objectDict):
        self.od=objectDict;
    def __getitem__(self, key):
        if key not in self.od:
            raise KeyError("‘"+str(key)+"’");
        else:
            return self.od[key].id;
    def __contains__(self, key):
        return key in self.od;
    def __setitem__(self, key, value):
        raise ValueError("You cannot change this pretend dictionary, as it’s just for getting.");

class idnDict:
    def __init__(self, objectDict):
        self.od=objectDict;
    def __getitem__(self, key):
        for k,v in self.od.items():
            if v.id==key:
                return k;
        raise KeyError("‘"+str(key)+"’");
    def __contains__(self, key):
        for k,v in self.od.items():
            if v.id==key:
                return True;
        return False;
    def __setitem__(self, key, value):
        raise ValueError("You cannot change this pretend dictionary, as it’s just for getting.");

class idoDict:
    def __init__(self, objectDict):
        self.od=objectDict;
    def __getitem__(self, key):
        for k,v in self.od.items():
            if v.id==key:
                return v;
        raise KeyError("‘"+str(key)+"’");
    def __contains__(self, key):
        for k,v in self.od.items():
            if v.id==key:
                return True;
        return False;
    def __setitem__(self, key, value):
        raise ValueError("You cannot change this pretend dictionary, as it’s just for getting.");

class DictRequireExistence(dict):
    #This is a dictionary with pins as keys; if the node or context of the pin doesn’t exist, raise a KeyError, even if the pin exists as a key in this dictionary.
    def __init__(self, nnno, cnco):
        dict.__init__(self);
        self.nnno=nnno;
        self.cnco=cnco;
    def __getitem__(self, key):
        result=dict.__getitem__(self, key);
        if key[0].name not in self.nnno or key[1].name not in self.cnco:
            raise KeyError("The node and/or context of that pin has been deleted.");
        return result;

class Node:
    def __init__(self, id, name, enabled=True):
        self.date_created=datetime.datetime.now(datetime.timezone.utc); #We add an argument instead of using utcnow() because we want an aware datetime object (not a naive one); this allows us to convert it to the local timezone later.
        self.name=name; #This is the nominative or subject name.
        self.title=None;
        self.cross_title=None;
        self.id=id;
        self.relations={}; #This is just backup in case we need to access relations directly from a node (e.g. to get all the relations for a specific node, which we do need to do)
        self.aliases=[]; #This is an ordered list of alias names for this node.
        self.enabled=enabled;
        self.license=None;
        self.a={}; #attributes
        self.viewers=set(); #This is a set of groups and users who can view this node.
        #Ideally, only one of the three items below will be in use, if any, unless you want something complicated.
    def __repr__(self):
        return "¡Node object ‘"+self.name+"’ ID="+str(self.id)+"¡";
    def get_attr(self, attr):
        #This allows you to get attributes without having to worry about making if statements to see if the attribute exists. If it doesn’t exist, it’s None. If you need to use None in a way that isn’t compatible with this, don’t use this method.
        if attr not in self.a:
            return None;
        else:
            return self.a[attr];
    def bool(self, attr): #This allows you to check for boolean attributes whether or not they exist. If they don’t exist, they’re False (if they do exist, they may be True or False). Similar to get_attr, but only for booleans.
        if attr not in self.a:
            return False;
        else:
            if isinstance(self.a[attr], bool):
                return self.a[attr];
            else:
                raise ValueError("‘"+attr+"’ of ‘"+self.name+"’ is not a boolean.");

class Relation:
    def __init__(self, context, *node_objects, enabled=True):
        self.date_created=datetime.datetime.now(datetime.timezone.utc); #We add an argument instead of using utcnow() because we want an aware datetime object (not a naive one); this allows us to convert it to the local timezone later.
        self.context=context; #Context object.
        self.node_objects=Group(Group);
        self.node_objects.add(*node_objects); #Keys are Node objects; values are automatically dictionaries (for attributes for that node as a secondary node of the relation; e.g. one key-value pair might be for URL parameters in the HTML export method)
        self.enabled=True;
        self.license=None;
        self.a={}; #attributes
        self.viewers=set(); #This is a set of groups and users who can view this Relation.
        self.rel_node_id_count=0; #This is used to give each node a unique relation ID (only within the relation/pin) that doesn’t change. This isn’t critical to the system at large, but users may be interested in having such IDs per relation/pin.
        self.rel_node_objects={"inherit_ancestors":True, "inherit_descendants":True}; #Keys are mostly node IDs that are unique within the entire project (although two keys, "inherit_ancestors" and "inherit_descendants", are dedicated for pin inheritance), and values are dictionaries that include the dates created (dates_created; element 0 is the most recent; element -1—the last one—is the first time it was created), and the node IDs (id) that are unique within the relation (but they are not unique within the project as a whole). Even if project nodes are removed from a relation or deleted, they retain this relation ID. You never have to delete any keys here, because it’s not meant to change. This dictionary is not intended to be used by those who extend Wikiweb as with attribute dictionaries of the classes and link relations, but rather internally. Keys are now node IDs instead of node objects—because, deleting nodes doesn’t delete the key (recreating a node object with the same name isn’t going to make it the same node). This way, you can make another node take its place more easily, if desired (although it should be intended to take its place with the ID system, since those IDs may be used all over the place already, even if the node were deleted).
        self.primary_node=None; #This is the primary node object.
    def __repr__(self):
        if self.primary_node==None:
            raise ValueError("The primary node of this relation has not been set.");
        else:
            return "¡Relation object with primary node ‘"+self.primary_node.name+"’ context ‘"+self.context.name+"’¡";
    def get_attr(self, attr):
        #This allows you to get attributes without having to worry about making if statements to see if the attribute exists. If it doesn’t exist, it’s None. If you need to use None in a way that isn’t compatible with this, don’t use this method.
        if attr not in self.a:
            return None;
        else:
            return self.a[attr];
    def bool(self, attr): #This allows you to check for boolean attributes whether or not they exist. If they don’t exist, they’re False (if they do exist, they may be True or False). Similar to get_attr, but only for booleans.
        if attr not in self.a:
            return False;
        else:
            if isinstance(self.a[attr], bool):
                return self.a[attr];
            else:
                raise ValueError("‘"+attr+"’ of ‘"+self.name+"’ is not a boolean.");

class Context:
    def __init__(self, id, name, enabled=True):
        self.date_created=datetime.datetime.now(datetime.timezone.utc); #We add an argument instead of using utcnow() because we want an aware datetime object (not a naive one); this allows us to convert it to the local timezone later.
        self.name=name;
        self.title=None;
        self.cross=None; #This is an object; not a name.
        self.id=id;
        self.nodes={}; #keys are node objects; values are relations
        self.enabled=enabled;
        self.license=None;
        self.a={}; #attributes
        self.viewers=set(); #This is a set of groups and users who can view this context, or relations of this Context.
    def __repr__(self):
        return "¡Context object ‘"+self.name+"’ ID="+str(self.id)+"¡";
    def get_attr(self, attr):
        #This allows you to get attributes without having to worry about making if statements to see if the attribute exists. If it doesn’t exist, it’s None. If you need to use None in a way that isn’t compatible with this, don’t use this method.
        if attr not in self.a:
            return None;
        else:
            return self.a[attr];
    def bool(self, attr): #This allows you to check for boolean attributes whether or not they exist. If they don’t exist, they’re False (if they do exist, they may be True or False). Similar to get_attr, but only for booleans.
        if attr not in self.a:
            return False;
        else:
            if isinstance(self.a[attr], bool):
                return self.a[attr];
            else:
                raise ValueError("‘"+attr+"’ of ‘"+self.name+"’ is not a boolean.");

class Project:
    def __init__(self, dirpath, name, default_context="includes", default_cross="is a", node_class=None, relation_class=None, context_class=None):
        #The user can name each database. Each must have a unique name so that the website can distinguish. However, different users can have databases with the same name as other users’ databases.
        #If you subclass this, make sure to put new attributes you want to be persistant above the Project.__init__(self, *args, **kwargs) or what-have-you.
        #If you make multiple subclassed projects wherein objects are to be made in the same run and/or in a way where they’ll be saved (and I don’t know why you would), don’t set the following classes in more than one of them, unless you want the second one to overwrite what the first did.
        if node_class!=None:
            global Node;
            Node=node_class;
        if relation_class!=None:
            global Relation;
            Relation=relation_class;
        if context_class!=None:
            global Context;
            Context=context_class;
        self.date_created=datetime.datetime.now(datetime.timezone.utc); #We add an argument instead of using utcnow() because we want an aware datetime object (not a naive one); this allows us to convert it to the local timezone later.
        self.dirpath=dirpath;
        self.imgpath=os.path.join(dirpath, "images");
        self.filepath=os.path.join(dirpath, name+".pkl");
        self.name=name;
        self.node_aliases=Group(); #keys are alias names and values could be the node objects they’re aliases for, but I don’t feel the need for this (so, it’s unset).
        self.nnno={};
        self.cnco={}; #context name -> context object
        self.node_id_count=0; #This is used to give each node a unique ID that doesn’t change.
        self.context_id_count=0; #This is used to give each context a unique ID that doesn’t change.
        self.license=None;
        self.a={}; #attributes
        self.viewers=set(); #This is a set of groups and users who can view this project.
        self.deleted_node_ids=[];
        self.deleted_context_ids=[];
        self.reuse_deleted_ids=False; #This is False in case people are using this to give such as tomato varieties unique identifiers that never change. If one is deleted and a new one took its place, that could cause ambiguity. In this case, it may be better to use a new number and never re-use the old one (especially as the old variety may prove to be real some day, anyway, and you may still want a number for it for historical purposes).
        self.reuse_deleted_context_ids=False;
        self.default_context=default_context;
        self.default_cross=default_cross;
        #self.make_context(default_context, default_cross);
        self.temp_dirs={}; #Keys are programmer-chosen names, and values are temporary directories (to store backups for rollbacks). See self.save_rollback() and self.load_rollback(). It’s a dictionary so you can have more than one backup (different kinds, or at different stages) if desired.
        self.load(); #This saves it if it doesn’t exist, and loads it if it does.
        self.crosses=CrossDict(self.cnco); #keys are context names and values are crossed context names. We don’t really need a regular dictionary like this since we can access the name from context objects (due to them containing the object of the cross): e.g. self.cnco["context name"].cross.name. So, updating Context.cross.name and self.cnco will be the updating of this.
        self.nnid=nidDict(self.nnno);
        self.cnid=nidDict(self.cnco);
        self.idnn=idnDict(self.nnno);
        self.idcn=idnDict(self.cnco);
        self.idno=idoDict(self.nnno);
        self.idco=idoDict(self.cnco);
    def node_title(self, node_name, subject=None, cross=None):
        #Return the titles of a node; optionally, set the title (and optionally its cross). The cross_title is what the node displays when it’s a secondary node, or for both if title isn’t set (title is for when it’s a primary node—or for both if cross_title isn’t set).
        #Titles are not necessarily unique (and they have no functionality in the database beyond display), but when set they are displayed instead of names (which are unique).
        #Title features aren’t strictly necessary for Wikiweb itself (as they could be attributes), but I thought it would be best to include them to make explaining Wikiweb easier (because now I can use different name inflections for the primary and secondary nodes and have people actually be able to do that if they want to).
        nobj=self.nnno[node_name];
        if subject!=None:
            nobj.title=subject;
            if nobj.cross_title==None and cross==None:
                nobj.cross_title=subject; #This is to make them the same if only one title is desired. Sorry, you can’t have it so the title is set and the cross_title isn’t.
        if cross!=None:
            if nobj.title==None and title==None: #Sorry, you can’t have title None if cross_title is set.
                nobj.title=cross;
            nobj.cross_title=cross;
        return nobj.title, nobj.cross_title; #Use either one if they’re supposed to be the same (or if you don’t know why there are two kinds of titles returned—a node can have a different title for when it’s a primary a node than when it’s a secondary node).
    def context_title(self, context_name, title=None):
        #Return the titles of a context; optionally.
        cobj=self.cnco[context_name];
        if title!=None:
            cobj.title=title;
        return cobj.title;
    def node_untitle(self, node_name):
        nobj=self.nnno[node_name];
        nobj.title=None;
        nobj.cross_title=None;
    def context_untitle(self, context_name):
        cobj=self.cnco[context_name];
        cobj.title=None;
    def untitle_all_nodes(self):
        for x in self.nnno:
            self.node_untitle(x);
    def untitle_all_contexts(self):
        for x in self.cnco:
            self.context_untitle(x);
    def rename_node(self, old_name, new_name, delete_title=True):
        if old_name not in self.nnno:
            raise IndexError("‘"+old_name+"’ is not a node. You cannot rename it.");
        elif new_name in self.nnno:
            raise ValueError("‘"+new_name+"’ is already taken. You cannot rename ‘"+old_name+"’ to that.");
        else:
            if old_name in self.node_aliases:
                self.rename_node_alias(old_name, new_name);
            else:
                obj=self.nnno[old_name];
                obj.name=new_name;
                del self.nnno[old_name];
                self.nnno[new_name]=obj;
            if self.nnno[new_name].title!=None and delete_title==True:
                self.node_untitle(new_name);
    def rename_context(self, old_name, new_name, delete_title=True):
        if old_name not in self.cnco:
            raise IndexError("‘"+old_name+"’ is not a context. You cannot rename it.");
        elif new_name in self.cnco:
            raise ValueError("‘"+new_name+"’ is already taken. You cannot rename ‘"+old_name+"’ to that.");
        else:
            obj=self.cnco[old_name];
            obj.name=new_name;
            del self.cnco[old_name];
            self.cnco[new_name]=obj;
            if self.cnco[new_name].title!=None and delete_title==True:
                self.context_untitle(new_name);
    def inc_node(self):
        if self.reuse_deleted_ids and len(self.deleted_node_ids)>0:
            return self.deleted_node_ids.pop();
        else:
            self.node_id_count+=1;
            return self.node_id_count-1;
    def inc_context(self):
        if self.reuse_deleted_context_ids and len(self.deleted_context_ids)>0:
            return self.deleted_context_ids.pop();
        else:
            self.context_id_count+=1;
            return self.context_id_count-1;
    def claim_node_id(self, id):
        if id not in self.deleted_node_ids:
            raise ValueError("‘"+str(id)+"’ is not a deleted node id.");
        else:
            return self.deleted_node_ids.pop(self.deleted_node_ids.index(id));
    def claim_context_id(self, id):
        if id not in self.deleted_context_ids:
            raise ValueError("‘"+str(id)+"’ is not a deleted context id.");
        else:
            return self.deleted_context_ids.pop(self.deleted_context_ids.index(id));
    def node_a(self, name, **kwargs):
        #Set attributes for a node.
        node=self.nnno[name];
        for k,v in kwargs.items():
            node.a[k]=v;
    def make_contexts(self, *context_pairs):
        #A context pair is a tuple containing the name and crossed name respectively
        for x in context_pairs:
            self.make_context(x[0], x[1]);
    def make_context(self, name, cross, make_default=False, quiet=True):
        if name in self.cnco:
            if quiet==False:
                raise ValueError("The context, ‘"+name+"’ already exists.");
            elif self.cnco[name].cross.name==cross:
                pass;
            else:
                raise ValueError("The context, ‘"+name+"’ already exists with a different crossed context than the one you tried to make.");
        elif cross in self.cnco:
            raise ValueError("The context, ‘"+cross+"’ already exists.");
        else:
            context_id=self.inc_context();
            cross_id=self.inc_context();
            cobj=Context(context_id, name);
            crossObj=Context(cross_id, cross);
            cobj.cross=crossObj;
            crossObj.cross=cobj;
            self.cnco[name]=cobj;
            self.cnco[cross]=crossObj;
            #self.crosses[name]=cross;
            #self.crosses[cross]=name;
            if make_default==True or self.default_context==None:
                self.default_context=name;
                self.default_cross=cross;
    def reset_node(self, name):
        self.disconnect(name);
        node=self.nnno[name];
        node.a.clear();
        node.date_created=datetime.datetime.now(datetime.timezone.utc); #We add an argument instead of using utcnow() because we want an aware datetime object (not a naive one); this allows us to convert it to the local timezone later.
        node.enabled=True;
        node.license=None;
        node.viewers.clear();
    def make_nodes(self, *names, overwrite=True):
        for x in names:
            self.make_node(x, overwrite);
    def make_node_auto(self):
        id=self.inc_node();
        node=Node(id=id, name=str(id));
        self.nnno[node.name]=node;
        return node;
    def make_node(self, name, overwrite=True):
        #overwrite is now a big misnomer. If overwrite is True, it does nothing if the node exists. If False, if raises an error if it exists.
        if name in self.nnno:
            if overwrite==True:
                #self.reset_node(name);
                pass; #Overwriting nodes is not allowed at this time. Just pass.
            else:
                raise NodeExistsError("That name is already taken and overwrite is set to false.");
        else:
            node=Node(id=self.inc_node(), name=name);
            self.nnno[name]=node;
    def make_node_aliases(self, name, *aliases, quiet=True):
        for x in aliases:
            self.make_node_alias(name, x, quiet=quiet);
    def make_node_alias(self, name, alias, quiet=True):
        #This makes a placeholder that points to a node object that already has a name.
        #quiet makes it so it doesn’t produce an error or do anything if the alias already exists for the same node you’re trying to make it for.
        if name in self.nnno:
            #This is to ensure that name doesn’t refer to an alias.
            original_name=name;
            name=self.nnno[name].name;
            if alias in self.nnno:
                if self.nnno[alias].name!=name:
                    raise ValueError("‘"+name+"’ and ‘"+alias+"’ are both already in the database, but ‘"+alias+"’ is not an alias of ‘"+name+"’. You can’t make it one when it’s already in use. Node that if you made a new node with an alias, the new node is made before an attempt is made at attaching the alias.");
                else:
                    if quiet==True:
                        pass;
                    else:
                        raise NodeExistsError("The name, ‘"+alias+"’, is already taken.");
            if name==alias:
                if original_name==name:
                    raise ValueError("‘"+original_name+"’ is an alias of ‘"+name+"’, and ‘"+name+"’ = ‘"+alias+"’");
                else:
                    if quiet==False: #If you have unexplained issues, check this (debug). This if statement is just here to make data entry stuff can be ignored if it's already been created. &&&
                        raise ValueError("Name and alias are the same: ‘"+name+"’.");
        if name not in self.nnno:
            raise KeyError("‘"+name+"’, the name you wish to alias is not that of a node.");
        elif alias in self.nnno:
            if self.nnno[name]==self.nnno[alias] and quiet==True:
                pass;
            else:
                raise NodeExistsError("The name, ‘"+alias+"’, is already taken.");
        else:
            node=self.nnno[name];
            self.nnno[alias]=node;
            node.aliases.append(alias);
            self.node_aliases.add(alias);
    def remove_node_alias(self, alias):
        if alias not in self.node_aliases:
            raise ValueError("The node, ‘"+alias+"’, is not an alias.");
        else:
            self.nnno[alias].aliases.remove(alias);
            self.node_aliases.remove(alias);
            del self.nnno[alias];
    def remove_node_aliases(self, *aliases, ignore_missing=False):
        for x in aliases:
            if ignore_missing==True:
                try:
                    self.remove_node_alias(x);
                except ValueError:
                    pass;
            else:
                self.remove_node_alias(x);
    def rename_node_alias(self, alias, new_name):
        if alias not in self.node_aliases:
            raise ValueError("The name, ‘"+alias+"’, is not an alias.");
        elif new_name in self.nnno:
            raise ValueError("The new name, ‘"+new_name+"’, is already taken.");
        else:
            self.node_aliases.remove(alias);
            self.node_aliases.add(new_name);
            nobj=self.nnno[alias];
            nobj.aliases.remove(alias);
            nobj.aliases.append(new_name);
            del self.nnno[alias];
            self.nnno[new_name]=nobj;
    def node_has_relation(self, node_name, context_name):
        #This checks to see if a node has a particular relation.
        cobj=self.cnco[context_name];
        if self.nnno[node_name] in cobj.nodes:
            return True;
        else:
            return False;
    def is_related(self, primary_node, context_name, secondary_node):
        pobj=self.nnno[primary_node];
        sobj=self.nnno[secondary_node];
        cobj=self.cnco[context_name];
        if pobj in cobj.nodes:
            if sobj in cobj.nodes[pobj].node_objects:
                return True;
            else:
                return False;
    def GIVE_REL_NODE_ID(self, primary, context, *secondary, raise_error=False):
        #This assigns a relative node ID to a secondary node. E.g. primary="tomato", context="includes", secondary="Cherokee Purple"; Cherokee Purple will get an ID within tomato includes (it’ll get a tomato ID, basically).
        #This method presupposes that all nodes passed into this method have been freshly related just before calling the method. No old nodes should be passed into this.
        for x in secondary:
            if self.nnno[x].id not in self.cnco[context].nodes[self.nnno[primary]].rel_node_objects:
                self.cnco[context].nodes[self.nnno[primary]].rel_node_objects[self.nnno[x].id]={"dates_created":[datetime.datetime.now(datetime.timezone.utc)], "id":self.cnco[context].nodes[self.nnno[primary]].rel_node_id_count};
                self.cnco[context].nodes[self.nnno[primary]].rel_node_id_count+=1;
            else:
                #The relation has been made before (and deleted and created again); there’s no need to give it another ID or increment rel_node_id_count since it keeps the original ID forever. This is to make the IDs useful for identification even in the face of updates (instead of re-using old IDs, we make new ones, even if the old IDs aren’t in use, since they were at use, and that number might be associated with it on someone’s website or something; this will let them know that it has been deleted rather than showing them a new node with that ID).
                self.cnco[context].nodes[self.nnno[primary]].rel_node_objects[self.nnno[x].id]["dates_created"].append(datetime.datetime.now(datetime.timezone.utc));
    def make_relation(self, node_name, context_name, *relative_node_names, side1=True, relation_func=False): #Create relations between nodes (this isn’t making Relation objects only, but you can add nodes to a Relation that already exists).
        relative_node_names_copy=relative_node_names;
        if len(relative_node_names)==0:
            raise ValueError("You don’t need to create Relation objects if you’re not making any relations between two specific nodes.");
        if context_name not in self.cnco:
            raise IndexError("‘"+context_name+"’ is not a context.");
        for x in relative_node_names:
            if x not in self.nnno:
                raise ValueError("The node, ‘"+x+"’ does not exist.");
        if node_name not in self.nnno:
            raise ValueError("The node, ‘"+node_name+"’ does not exist.");
        else:
            relative_node_names=set(relative_node_names);
            for x in relative_node_names.copy(): #Remove secondary node args wherein they’re already in the relation.
                if self.is_related(node_name, context_name, x):
                    relative_node_names.remove(x);
            relative_node_objects=self.nnno_set(relative_node_names);
            if self.nnno[node_name] not in self.cnco[context_name].nodes: #If the Relation doesn’t exist, make the Relation and add nodes to it.
                self.cnco[context_name].nodes[self.nnno[node_name]]=Relation(self.cnco[context_name], *relative_node_objects);
                self.cnco[context_name].nodes[self.nnno[node_name]].primary_node=self.nnno[node_name];
                self.nnno[node_name].relations[self.cnco[context_name]]=self.cnco[context_name].nodes[self.nnno[node_name]]; #Add the Relation object to the node, too.
                self.GIVE_REL_NODE_ID(node_name, context_name, *relative_node_names); #You have to give the relation node IDs after the relations are made.
            else: #Add Node names to the Relation.
                self.cnco[context_name].nodes[self.nnno[node_name]].node_objects.update(relative_node_objects);
                self.GIVE_REL_NODE_ID(node_name, context_name, *relative_node_names);
            if side1==True:
                for x in relative_node_names:
                    self.make_relation(x, self.crosses[context_name], node_name, side1=False);
    def disconnect_old(self, name, delete_relations=False):
        #Removes all relations from a node and removes the node from all relations. Delete this when you make sure the new disconnect works.
        #If delete_relations is True, then any empty relations will be deleted. This is not normally desirable behavior (if you want relative node IDs to be constant even when removed and added again).
        if name not in self.nnno:
            raise ValueError("The node, ‘"+name+"’, does not exist. It cannot be disconnected.");
        else:
            if delete_relations==True:
                for k,v in self.nnno[name].relations.copy().items():
                    for x in v.node_objects.copy():
                        x.relations[k.cross].node_objects.remove(self.nnno[name]);
                        if len(x.relations[k.cross].node_objects)==0:
                            del x.relations[k.cross];
                    del k.nodes[self.nnno[name]];
                    v.node_objects.clear();
                self.nnno[name].relations.clear();
                for x in self.cnco:
                    if self.nnno[name] in self.cnco[x].nodes:
                        del self.cnco[x].nodes[self.nnno[name]];
            else:
                for k,v in self.nnno[name].relations.items():
                    for x in v.node_objects:
                        x.relations[k.cross].node_objects.remove(self.nnno[name]);
                    v.node_objects.clear();
    def disconnect(self, name, delete_relations=False):
        #Removes all relations from a node and removes the node from all relations.
        nobj=self.nnno[name];
        for cobj in nobj.relations: #Remove all relations from the node. (It should no longer be a primary or secondary node to anything via any context. Relations are all two-way.)
            for sec_node_object in nobj.relations[cobj].node_objects.copy():
                self.remove_relation(nobj.name, cobj.name, sec_node_object.name, delete_relation=delete_relations);
    def del_node(self, name, delete_relations=False):
        #Deletes a node from the database. This will delete all aliases, too. If it is an alias, it will delete it, all aliases and the actual node, too.
        if name in self.nnno:
            if name in self.node_aliases:
                name=self.nnno[name].name;
            for x in self.nnno[name].aliases.copy():
                self.remove_node_alias(x);
            node_obj=self.nnno[name];
            self.disconnect(name, delete_relations=delete_relations);
            del self.nnno[name];
            self.deleted_node_ids.append(node_obj.id);
        else:
            raise ValueError("The node, ‘"+name+"’ does not exist.");
    def delete_node(self, name):
        self.del_node(name);
    def cnco_set(self, context_names):
        #Convert a set of context names to a set of context IDs.
        cl=set();
        for x in context_names:
            cl.add(self.cnco[x]);
        return cl;
    def nnno_set(self, node_names):
        #Convert a set of node names to a set of node objects.
        nl=set();
        for x in node_names:
            nl.add(self.nnno[x]);
        return nl;
    def remove_relation(self, node_name, context_name, *relative_node_names, side1=True, delete_relation=False, relation_func=False): #Remove relations between nodes.
        relative_node_names_copy=relative_node_names;
        if len(relative_node_names)==0:
            raise ValueError("You don’t need to delete Relation objects if you’re not removing any relations between two specific nodes.");
        for x in relative_node_names:
            if x not in self.nnno:
                raise ValueError("The node, ‘"+x+"’ does not exist.");
        if node_name not in self.nnno:
            raise ValueError("The node, ‘"+node_name+"’ does not exist.");
        else:
            if self.nnno[node_name] not in self.cnco[context_name].nodes: #Check to see if the Relation object exists.
                raise UnrelatedError("‘"+node_name+"’ does not have the Relation, ‘"+context_name+"’.");
            else: #Remove Node names from the Relation.
                relative_node_names=set(relative_node_names);
                relative_node_objects=self.nnno_set(relative_node_names);
                for x in relative_node_names.copy(): #Remove secondary node args wherein they are already not in the relation.
                    if not self.is_related(node_name, context_name, x):
                        relative_node_names.remove(x);
                self.cnco[context_name].nodes[self.nnno[node_name]].node_objects.remove(*relative_node_objects);
                if delete_relation==True:
                    if len(self.cnco[context_name].nodes[self.nnno[node_name]].node_objects)==0:
                        #Delete the relation object. Not necessary, but keeps the filesize smaller and makes iterations of self.relations more efficient.
                        del self.cnco[context_name].nodes[self.nnno[node_name]];
                        del self.nnno[node_name].relations[self.cnco[context_name]];
            if side1==True:
                for x in relative_node_names:
                    self.remove_relation(x, self.crosses[context_name], node_name, side1=False);
    def del_context(self, name):
        #This deletes the cross, too, and all relations that use either.
        cross=self.crosses[name];
        obj=self.cnco[name];
        cross_obj=self.cnco[cross];
        for pri in obj.nodes.copy():
            for sec in x.relations[obj].node_objects.copy():
                self.remove_relation(pri.name, obj.name, sec.name);
        for x in self.cnco[name].nodes:
            del x.relations[self.cnco[name]];
        for x in self.cnco[cross].nodes:
            del x.relations[self.cnco[cross]];
        #del self.crosses[name];
        #del self.crosses[cross];
        del self.cnco[name];
        del self.cnco[cross];
        self.deleted_context_ids.append(obj.id);
        self.deleted_context_ids.append(cross_obj.id);
    def del_context_old(self, name):
        #This deletes the cross, too, and all relations that use either.
        cross=self.crosses[name];
        obj=self.cnco[name];
        cross_obj=self.cnco[cross];
        
        for x in self.cnco[name].nodes:
            del x.relations[self.cnco[name]];
        for x in self.cnco[cross].nodes:
            del x.relations[self.cnco[cross]];
        #del self.crosses[name];
        #del self.crosses[cross];
        del self.cnco[name];
        del self.cnco[cross];
        self.deleted_context_ids.append(obj.id);
        self.deleted_context_ids.append(cross_obj.id);
    def delete_context(self, name):
        self.del_context(name);
    def rename_project(self, new_name):
        self.name=new_name;
    def save(self):
        #Saves the project.
        if os.path.exists(self.filepath):
            os.remove(self.filepath);
        if not os.path.exists(self.dirpath):
            os.makedirs(self.dirpath);
        if not os.path.exists(self.imgpath):
            os.makedirs(self.imgpath);
        with open(self.filepath, "wb") as FILE:
            pickle.dump(self, FILE, 4);
        #print("Project ‘"+self.name+"’ saved.");
    def save_rollback(self, rollback_name):
        #Saves a temporary backup for rollback purposes. The programmer gets to name it (so the programmer can track multiple ones with ease). rollback_name is an arbitrary name chosen by the programmer who uses this module. It is not the filepath (or anything like that).
        #These are not deleted when you close the program (but they are in your directory for temporary files; so, don’t count on them sticking around forever). If you desire to delete them, use the methods below, or use self.load_rollbacks with delete_after set to True (the default).
        self.temp_dirs[rollback_name]=tempfile.mkdtemp();
        with open(os.path.join(self.temp_dirs[rollback_name], self.name), "wb") as FILE:
            pickle.dump(self, FILE, 4);
    def load_rollback(self, rollback_name, delete_after=True):
        #Loads a temporary backup for rollback purposes. rollback_name is an arbitrary name chosen by the programmer who uses this module; it is not the filepath or anything like that.
        #Note that this only affects changes to what is loaded in memory (not to anything you used self.save() to create).
        print("Rollling back changes to the loaded database.");
        with open(os.path.join(self.temp_dirs[rollback_name], self.name), 'rb') as FILE:
            result=pickle.load(FILE);
        for k,v in result.__dict__.items():
            self.__dict__[k]=v;
        print("Rolled back.");
        if delete_after==True:
            self.delete_rollback(rollback_name);
            print("Temporary rollback filepath deleted.")
    def delete_rollback(self, rollback_name):
        #Removes the temporary directory containing the temporarily saved backup for rollback purposes.
        shutil.rmtree(self.temp_dirs[rollback_name]);
        del self.temp_dirs[rollback_name];
    def delete_rollbacks(self):
        for x in self.temp_dirs.copy():
            self.delete_rollback(x);
    def load(self):
        #Loads the project.
        #If it doesn’t exist, create it. If it exists, load it.
        if not os.path.exists(self.filepath):
            #print("The project has not been saved, yet.");
            #self.save();
            pass;
        else:
            with open(self.filepath, 'rb') as FILE:
                result=pickle.load(FILE);
            for k,v in result.__dict__.items():
                if k not in {"dirpath", "filepath", "imgpath"}:
                    self.__dict__[k]=v;
            #print("Project ‘"+self.name+"’ loaded.");
    def pin_startswith(self, text, pin, include_pins=None, exclude_pins=None):
        #Pin matches that start with text; pin is the pin that you pin the matches with (it’s not a pin you search among—that is include_pins)
        #pin should be a tuple, which contains a node and a context
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        include_pin_nodes=set();
        exclude_pin_nodes=set();
        for pin in include_pins:
            if self.cnco[pin[1]] in self.nnno[pin[0]].relations:
                for x in self.nnno[pin[0]].relations[self.cnco[pin[1]]].node_objects:
                    include_pin_nodes.add(x.name);
        for pin in exclude_pins:
            if self.cnco[pin[1]] in self.nnno[pin[0]].relations:
                for x in self.nnno[pin[0]].relations[self.cnco[pin[1]]].node_objects:
                    exclude_pin_nodes.add(x.name);
        if pin[0] not in self.nnno:
            raise ValueError(pin[0]+" is not in self.nnno.");
        if pin[1] not in self.cnco:
            raise ValueError(pin[1]+" is not in self.cnco.");
        matches=[];
        if len(include_pins)==0:
            for x in self.nnno.copy():
                if x.startswith(text)==True:
                    matches.append(x);
        else:
            for x in include_pin_nodes:
                if x.startswith(text)==True:
                    matches.append(x);
        #Pin the matches and return them
        if len(matches)>0:
            self.make_relation(pin[0], pin[1], *matches);
        return set(matches)-exclude_pin_nodes;
    def pin_endswith(self, text, pin, include_pins=None, exclude_pins=None):
        #Pin matches that end with text; pin is the pin that you pin the matches with (it’s not a pin you search among—that is include_pins)
        #pin should be a tuple, which contains a node and a context
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if pin[0] not in self.nnno:
            raise ValueError(pin[0]+" is not in self.nnno.");
        if pin[1] not in self.cnco:
            raise ValueError(pin[1]+" is not in self.cnco.");
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        include_pin_nodes=set();
        exclude_pin_nodes=set();
        for pin in include_pins:
            if self.cnco[pin[1]] in self.nnno[pin[0]].relations:
                for x in self.nnno[pin[0]].relations[self.cnco[pin[1]]].node_objects:
                    include_pin_nodes.add(x.name);
        for pin in exclude_pins:
            if self.cnco[pin[1]] in self.nnno[pin[0]].relations:
                for x in self.nnno[pin[0]].relations[self.cnco[pin[1]]].node_objects:
                    exclude_pin_nodes.add(x.name);
        matches=[];
        if len(include_pins)==0:
            for x in self.nnno.copy():
                if x.endswith(text)==True:
                    matches.append(x);
        else:
            for x in include_pin_nodes:
                if x.endswith(text)==True:
                    matches.append(x);
        #Pin the matches and return them
        if len(matches)>0:
            self.make_relation(pin[0], pin[1], *matches);
        return set(matches)-exclude_pin_nodes;
    def pin_regex(self, pin, text, exclude_text=None, include_pins=None, exclude_pins=None, cs=True):
        #Pin regular expression matches; pin is what you pin that matches with (i.e. add the matches to that relationship as secondary nodes).
        #pin should be a tuple, which contains a node and a context
        #text and exclude text can be either each a regex string or each a list of regex strings (if you want to perform more than one).
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if exclude_text==None:
            exclude_text=[];
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        if pin[0] not in self.nnno:
            raise ValueError(pin[0]+" is not in self.nnno.");
        if pin[1] not in self.cnco:
            raise ValueError(pin[1]+" is not in self.cnco.");
        matches=self.regex_node_matches(text, exclude_text, include_pins=include_pins, exclude_pins=exclude_pins, cs=cs);
        #Pin the matches and return them
        if len(matches)>0:
            #(node_name, context_name, *relative_node_names, side1=True)
            self.make_relation(pin[0], pin[1], *matches);
        return matches;
    def regex_node_matches(self, text, exclude_text=None, sort_it=False, include_pins=None, exclude_pins=None, cs=True):
        #text and exclude_text can either be a string regex or a list of regex strings (if you want more than one).
        #pins should be tuples. include_pins should be a set or a list (not a tuple, or else it will be interpreted as a single pin and put inside of a set).
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if exclude_text==None:
            exclude_text=[];
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        include_pin_nodes=set();
        exclude_pin_nodes=set();
        for pin in include_pins:
            if self.cnco[pin[1]] in self.nnno[pin[0]].relations:
                for x in self.nnno[pin[0]].relations[self.cnco[pin[1]]].node_objects:
                    include_pin_nodes.add(x.name);
        for pin in exclude_pins:
            if self.cnco[pin[1]] in self.nnno[pin[0]].relations:
                for x in self.nnno[pin[0]].relations[self.cnco[pin[1]]].node_objects:
                    exclude_pin_nodes.add(x.name);
        if isinstance(text, str):
            text=[text];
        if isinstance(exclude_text, str):
            exclude_text=[exclude_text];
        matches=set();
        if len(include_pins)==0:
            for rex in text:
                for x in self.nnno.copy():
                    if cs==True:
                        if re.search(rex, x)!=None:
                            matches.add(x);
                    else:
                        if re.search(rex, x, flags=re.IGNORECASE)!=None:
                            matches.add(x);
        else:
            for rex in text:
                for x in include_pin_nodes:
                    if cs==True:
                        if re.search(rex, x)!=None:
                            matches.add(x);
                    else:
                        if re.search(rex, x, flags=re.IGNORECASE)!=None:
                            matches.add(x);
        exclude=set();
        for rex in exclude_text:
            for x in self.nnno.copy():
                if cs==True:
                    if re.search(rex, x)!=None:
                        exclude.add(x);
                else:
                    if re.search(rex, x, flags=re.IGNORECASE)!=None:
                        exclude.add(x);
        if sort_it==False:
            return (matches-exclude)-exclude_pin_nodes;
        else:
            #return sorted((matches-exclude)-exclude_pin_nodes);
            return self.sort((matches-exclude)-exclude_pin_nodes);
    def regex_context_matches(self, text, exclude_text=None, sort_it=False, cs=True):
        #Return a list of all the contexts whose names match a regular expression.
        #text and exclude_text can either be a string regex or a list of regex strings (if you want more than one).
        if exclude_text==None:
            exclude_text=[];
        if isinstance(text, str):
            text=[text];
        if isinstance(exclude_text, str):
            exclude_text=[exclude_text];
        matches=set();
        for rex in text:
            for x in self.cnco.copy():
                if cs==True:
                    if re.search(rex, x)!=None:
                        matches.add(x);
                else:
                    if re.search(rex, x, flags=re.IGNORECASE)!=None:
                        matches.add(x);
        exclude=set();
        for rex in exclude_text:
            for x in self.cnco.copy():
                if cs==True:
                    if re.search(rex, x)!=None:
                        exclude.add(x);
                else:
                    if re.search(rex, x, flags=re.IGNORECASE)!=None:
                        exclude.add(x);
        if sort_it==False:
            return matches-exclude;
        else:
            #return sorted(matches-exclude);
            return self.sort(matches-exclude);
    def regex_rename_node(self, text, replace_text, exclude_text=None, include_pins=None, exclude_pins=None, cs=True):
        #replace_text can be either regular expression text or a regular expression function.
        #Text must be a regular expression string (not a list of them).
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if exclude_text==None:
            exclude_text=[];
        original_matches=self.regex_node_matches(text, exclude_text, include_pins=include_pins, exclude_pins=exclude_pins, cs=cs);
        renamed_matches=set();
        for x in original_matches.copy():
            renamed=re.sub(text, replace_text, x);
            renamed_matches.add(renamed);
            self.rename_node(x, renamed);
        return {"original":original_matches, "renamed":renamed_matches};
    def regex_rename_context(self, text, replace_text, exclude_text=None, cs=True):
        #Rename all contexts that match a regular expression.
        #replace_text can be either regular expression text or a regular expression function.
        #Text must be a regular expression string (not a list of them).
        if exclude_text==None:
            exclude_text=[];
        original_matches=self.regex_context_matches(text, exclude_text, cs=cs);
        renamed_matches=set();
        for x in original_matches.copy():
            renamed=re.sub(text, replace_text, x);
            renamed_matches.add(renamed);
            self.rename_context(x, renamed);
        return {"original":original_matches, "renamed":renamed_matches};
    def disconnect_regex(self, text, exclude_text=None, include_pins=None, exclude_pins=None, cs=True, delete_relations=False):
        #Disconnect all nodes that match a regular expression.
        #text and exclude text can be either each a regex string or each a list of regex strings (if you want to perform more than one).
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if exclude_text==None:
            exclude_text=[];
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        matches=self.regex_node_matches(text, exclude_text, include_pins=include_pins, exclude_pins=exclude_pins, cs=cs);
        #Disconnect the matches and return them
        if len(matches)>0:
            for x in matches:
                self.disconnect(x, delete_relations=delete_relations);
        return matches;
    def del_node_regex(self, text, exclude_text=None, include_pins=None, exclude_pins=None, cs=True, delete_relations=False):
        #Delete all nodes that match a regular expression.
        #text and exclude text can be either each a regex string or each a list of regex strings (if you want to perform more than one).
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if exclude_text==None:
            exclude_text=[];
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        matches=self.regex_node_matches(text, exclude_text, include_pins=include_pins, exclude_pins=exclude_pins, cs=cs);
        #Delete the matches and return them
        if len(matches)>0:
            for x in matches:
                self.del_node(x, delete_relations=delete_relations);
        return matches;
    def del_context_regex(self, text, exclude_text=None, sort_it=False, cs=True):
        #Delete all contexts that match a regular expression.
        #text and exclude text can be either each a regex string or each a list of regex strings (if you want to perform more than one).
        if exclude_text==None:
            exclude_text=[];
        matches=self.regex_context_matches(text, exclude_text, sort_it=sort_it, cs=cs);
        #Delete the matches and return them
        if len(matches)>0:
            for x in matches:
                self.del_context(x);
        return matches;
    def get_attr(self, attr):
        #This allows you to get attributes without having to worry about making if statements to see if the attribute exists. If it doesn’t exist, it’s None. If you need to use None in a way that isn’t compatible with this, don’t use this method.
        if attr not in self.a:
            return None;
        else:
            return self.a[attr];
    def bool(self, attr): #This allows you to check for boolean attributes whether or not they exist. If they don’t exist, they’re False (if they do exist, they may be True or False). Similar to get_attr, but only for booleans.
        if attr not in self.a:
            return False;
        else:
            if isinstance(self.a[attr], bool):
                return self.a[attr];
            else:
                raise ValueError("‘"+attr+"’ of ‘"+self.name+"’ is not a boolean.");
    def nattr(self, node_name, key, value=True):
        #Set a node attribute. Value is set to True by default (although it may be a string or whatever else).
        self.nnno[node_name].a[key]=value;
    def cattr(self, context_name, key, value=True, set_cross=True):
        #Set a context attribute (and optionally the attribute of its cross). Value is set to True by default.
        self.cnco[context_name].a[key]=value;
        if set_cross:
            self.cnco[context_name].cross.a[key]=value;
    def rattr(self, primary_node_name, context_name, key, value=True, set_cross=True):
        #Set a relation attribute and optionally the attribute of its crossed relations. Value is set to True by default.
        #If set_cross is True, it will set the same attribute in the cross relations, too.
        #Example usage: self.rattr("tomato", "children", "hidden") will hide the children context for tomato, and the parent context for tomato’s children (the relation will still exist, however); rather, it’ll set the a["hidden"] to True (and other parts of the program you make will hopefully use that to hide it).
        self.nnno[primary_node_name].relations[self.cnco[context_name]].a[key]=value;
        if set_cross:
            for node_obj in self.nnno[primary_node_name].relations[self.cnco[context_name]].node_objects:
                self.rattr(node_obj.name, self.crosses[context_name], key, value, set_cross=False);
    def lattr(self, primary, context, secondary, key, value=True):
        #This sets relation link attributes.
        if primary in self.nnno:
            if context in self.cnco:
                if self.cnco[context] in self.nnno[primary].relations:
                    if secondary in self.nnno:
                        if self.nnno[secondary] in self.nnno[primary].relations[self.cnco[context]].node_objects:
                            self.nnno[primary].relations[self.cnco[context]].node_objects[self.nnno[secondary]][key]=value;
                        else:
                            raise KeyError("‘"+secondary+"’ is not a secondary node to ‘"+primary+"’ with the relation ‘"+context+"’.");
                    else:
                        raise KeyError("‘"+secondary+"’ is not a node.");
                else:
                    raise KeyError("‘"+context+"’ is not a relation of ‘"+primary+"’.");
            else:
                raise KeyError("‘"+context+"’ is not a context.");
        else:
            raise KeyError("‘"+primary+"’ is not a node.");
    def grlattr(self, primary, context, secondary, key):
        #This gets a relation link attribute.
        if primary in self.nnno:
            if context in self.cnco:
                if self.cnco[context] in self.nnno[primary].relations:
                    if secondary in self.nnno:
                        if self.nnno[secondary] in self.nnno[primary].relations[self.cnco[context]].node_objects:
                            if key in self.nnno[primary].relations[self.cnco[context]].node_objects[self.nnno[secondary]]:
                                return self.nnno[primary].relations[self.cnco[context]].node_objects[self.nnno[secondary]][key];
                            else:
                                return None;
                        else:
                            raise KeyError("‘"+secondary+"’ is not a secondary node to ‘"+primary+"’ with the relation ‘"+context+"’.");
                    else:
                        raise KeyError("‘"+secondary+"’ is not a node.");
                else:
                    raise KeyError("‘"+context+"’ is not a relation of ‘"+primary+"’.");
            else:
                raise KeyError("‘"+context+"’ is not a context.");
        else:
            raise KeyError("‘"+primary+"’ is not a node.");
    def gnattr(self, node_name, key):
        #Get a node attribute
        return self.nnno[node_name].a[key];
    def gcattr(self, context_name, key):
        #Get a context attribute
        return self.cnco[context_name].a[key];
    def grattr(self, primary_node_name, context_name, key):
        #Get a relation attribute
        return self.nnno[primary_node_name].relations[self.cnco[context_name]].a[key];
    def gldates(self, pri, con, sec, dir=None, utc=False):
        #Get link dates; get a list of all the datetime objects representing a date when the secondary node was related/linked to the primary node. If a dir (directive) is added, it returns a list of strings instead of a list of datetime objects.
        #"%-d %b %Y" is a good example directive (on Linux; for Windows, replace the - with a #; these are to remove trailing zeros).
        po=self.nnno[pri];
        so=self.nnno[sec];
        con=self.cnco[con];
        if dir==None:
            return po.relations[con].rel_node_objects[so.id]["dates_created"];
        else:
            sl=[]; #string list
            for x in po.relations[con].rel_node_objects[so.id]["dates_created"]:
                if utc==False:
                    sl.append(x.astimezone().strftime(dir));
                else:
                    sl.append(x.strftime(dir).replace("UTC+00:00", "UTC"));
            return sl;
    def gldate(self, pri, con, sec, dir=None, utc=False):
        #Get link date; returns the latest time that the secondary node was related/added/linked to the relation. Time is in the form of a datetime object. If a dir (directive) is added, it is returned as a string.
        #"%-d %b %Y" is a good example directive (on Linux; for Windows, replace the - with a #; these are to remove trailing zeros).
        if dir==None:
            return self.gldates(pri, con, sec)[-1];
        else:
            if utc==False:
                return self.gldates(pri, con, sec)[-1].astimezone().strftime(dir);
            else:
                return self.gldates(pri, con, sec)[-1].strftime(dir).replace("UTC+00:00", "UTC");
    def sort_chunks(self, myList):
        #This takes a sorted list, and sorts each chunk of entries that would be the same if they had the same casing (according to the GROUPLETTERS algorithm). The returned list amounts to what GROUPLETTERS|IGNORECASE ought to result in, IMO.
        finds=[];
        previous_x=None;
        for x in myList:
            if len(finds)==0:
                finds.append([x]);
            else:
                if previous_x.lower()==x.lower():
                    finds[-1].append(x);
                else:
                    finds.append([x]);
            previous_x=x;
        #showinfo("HERE", str(finds));
        newList=[];
        for x in finds:
            case_sorted=natsort.natsorted(x, alg=natsort.ns.GROUPLETTERS);
            for y in case_sorted:
                newList.append(y);
        return newList;
    def sort(self, myList, rev=False, cs=False):
        result=None;
        if cs==True:
            result=natsort.natsorted(myList, alg=natsort.ns.GROUPLETTERS);
        else:
            result=natsort.natsorted(myList, alg=natsort.ns.IGNORECASE);
            try:
                result=self.sort_chunks(result);
            except:
                import traceback;
                traceback.print_exc();
        if rev==True:
            result.reverse();
        return result;
    def opin(self, pin):
        #This takes a string pin and converts it to an object pin—and returns it.
        if isinstance(pin, tuple)==False:
            raise ValueError("‘pin’ must be a tuple of strings.");
        else:
            if len(pin)==2:
                nobj=self.nnno[pin[0]];
                cobj=self.cnco[pin[1]];
                return (nobj, cobj);
            elif len(pin)==3:
                nobj=self.nnno[pin[0]];
                cobj=self.cnco[pin[1]];
                sobj=self.nnno[pin[2]];
                return (nobj, cobj, sobj);
            else:
                raise ValueError("Pins must have a length of two or three.");
    def get_relation_node_id(self, primary_node, context, secondary_node):
        #This gets the ID of a secondary node within its relation (which is unique to this relation).
        pobj, cobj, sobj=self.opin((primary_node, context, secondary_node));
        return pobj.relations[cobj].rel_node_objects[sobj.id]["id"];
    def get_pin_ancestor_inheritance(self, pin):
        #This returns whether or not a pin should inherit its ancestral pins.
        nobj, cobj=self.opin(pin);
        return nobj.relations[cobj].rel_node_objects["inherit_ancestors"];
    def get_pin_descendant_inheritance(self, pin):
        #This returns whether or not a pin should inherit its descendant pins.
        nobj, cobj=self.opin(pin);
        return nobj.relations[cobj].rel_node_objects["inherit_descendants"];
    def set_pin_ancestor_inheritance(self, pin, inherit=False):
        #This sets whether or not a pin should inherit its ancestral pins. All pins do by default (so, the default change to this is to make it False, since it’s usually already True).
        nobj, cobj=self.opin(pin);
        nobj.relations[cobj].rel_node_objects["inherit_ancestors"]=inherit;
    def set_pin_descendant_inheritance(self, pin, inherit=False):
        #This sets whether or not a pin should inherit its descendant pins. All pins do by default (so, the default change to this is to make it False, since it’s usually already True).
        nobj, cobj=self.opin(pin);
        nobj.relations[cobj].rel_node_objects["inherit_descendants"]=inherit;
    def pin(self, pin, include_pins=None, exclude_pins=None):
        #This pins all nodes that have the specified pins.
        #More specifically, pin=("cherry", "includes"), include_pins=[("tomato", "includes")] means that all tomatoes are now cherries. (Or that cherry now includes everything that tomato includes.)
        #This adds the pin to all nodes that have the include_pins and don’t have the exclude_pins. If there are no include_pins, it uses all nodes, sans those excluded.
        #pin should be a tuple, which contains a node and a context
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        if pin[0] not in self.nnno:
            raise ValueError(pin[0]+" is not in self.nnno.");
        if pin[1] not in self.cnco:
            raise ValueError(pin[1]+" is not in self.cnco.");
        matches=set();
        if len(include_pins)>0:
            for ipin in include_pins:
                nobj=self.nnno[ipin[0]];
                cobj=self.cnco[ipin[1]];
                if cobj in nobj.relations:
                    for x in nobj.relations[cobj].node_objects:
                        matches.add(x.name);
        else:
            for node_name in self.nnno:
                matches.add(node_name);
        for epin in exclude_pins:
            nobj=self.nnno[epin[0]];
            cobj=self.cnco[epin[1]];
            if cobj in nobj.relations:
                for x in nobj.relations[cobj].node_objects:
                    try:
                        matches.remove(x.name);
                    except KeyError:
                        pass;
        #Pin the matches and return them
        if len(matches)>0:
            self.make_relation(pin[0], pin[1], *matches);
        return matches;
    def unpin(self, pin, include_pins=None, exclude_pins=None):
        #This unpins all nodes that have the specified pins.
        #More specifically, pin=("cherry", "includes"), include_pins=[("tomato", "includes")] means that all tomatoes are now no longer cherries. (Or that cherry no longer includes anything that tomato includes.)
        #This adds the pin to all nodes that have the include_pins and don’t have the exclude_pins. If there are no include_pins, it uses all nodes, sans those excluded.
        #pin should be a tuple, which contains a node and a context
        #If a list of include_pins is set, then it only searches among those (as opposed to all nodes).
        #exclude_pins are pins that encompass nodes that are subtracted from the matches entirely.
        #include_pins and exclude_pins should be a set or tuple of pins (pins are two-member tuples, starting with a node name, followed by a context name).
        if include_pins==None:
            include_pins=set();
        else:
            if isinstance(include_pins, tuple):
                include_pins={include_pins};
        if exclude_pins==None:
            exclude_pins=set();
        else:
            if isinstance(exclude_pins, tuple):
                exclude_pins={exclude_pins};
        if pin[0] not in self.nnno:
            raise ValueError(pin[0]+" is not in self.nnno.");
        if pin[1] not in self.cnco:
            raise ValueError(pin[1]+" is not in self.cnco.");
        matches=set();
        all=set();
        nobj=self.nnno[pin[0]];
        cobj=self.cnco[pin[1]];
        if cobj in nobj.relations:
            for x in nobj.relations[cobj].node_objects:
                all.add(x.name);
        if len(include_pins)>0:
            for ipin in include_pins:
                nobj=self.nnno[ipin[0]];
                cobj=self.cnco[ipin[1]];
                if cobj in nobj.relations:
                    for x in nobj.relations[cobj].node_objects:
                        matches.add(x.name);
            matches=matches.intersection(all);
        else:
            pass;
        for epin in exclude_pins:
            nobj=self.nnno[epin[0]];
            cobj=self.cnco[epin[1]];
            if cobj in nobj.relations:
                for x in nobj.relations[cobj].node_objects:
                    try:
                        matches.remove(x.name);
                    except KeyError:
                        pass;
        #Unpin the matches and return them.
        if len(matches)>0:
            self.remove_relation(pin[0], pin[1], *matches);
        return matches;
    def get_pin_ancestors(self, pin, desc=False):
        """
            pin=(Matina, includes); this should get everything that includes Matina (everything Matina is), and everything that includes everything that includes Matina, and so forth.
            Then, in another method, we should pin Matina with all of them, Matina’s parents with all of them that aren’t its children, etc.
            #Do not set desc manually. It’s for internal stuff.
        """
        nobj, cobj=self.opin(pin);
        results=set();
        if cobj.cross in nobj.relations:
            if desc==False:
                if nobj.relations[cobj.cross].rel_node_objects["inherit_ancestors"]==True:
                    for x in nobj.relations[cobj.cross].node_objects: #each thing that Matina is
                        results.add(x.name);
            else:
                if nobj.relations[cobj.cross].rel_node_objects["inherit_descendants"]==True:
                    for x in nobj.relations[cobj.cross].node_objects: #each thing that Matina is
                        results.add(x.name);
        for x in results.copy():
            results.update(self.get_pin_ancestors((x, pin[1])));
        return results;
    def get_pin_descendants(self, pin):
        """
            pin=(Solanum, includes); this should get (tomato, includes), (eggplant, includes), (Matina, includes), (Aswad, includes), etc.
            We should return a list of those things above, and in another method, pin them all with (Solanum, includes).
        """
        return self.get_pin_ancestors((pin[0], self.crosses[pin[1]]), desc=True);
    def set_pin_ancestors(self, pin):
        #&&&Debug this and get_pin_ancestors/descendants.
        #Make this take into consideration nodes that don’t inherit. &&&
        nobj, cobj=self.opin(pin);
        results=self.get_pin_ancestors(pin);
        for x in results:
            self.pin((x, cobj.name), [pin]);
        if cobj.cross in nobj.relations.copy():
            for x in nobj.relations[cobj.cross].node_objects.copy(): #&&&If there are issues, it might be because node_objects is a Group and may need its own copy method instead.
                self.set_pin_ancestors((x.name, cobj.name));
        return results;
    def set_pin_descendants(self, pin):
        #Make this take into consideration nodes that don’t inherit. &&&
        nobj, cobj=self.opin(pin);
        results=self.get_pin_descendants(pin);
        for x in results:
            self.pin(pin, (x, cobj.name));
        if cobj in nobj.relations.copy():
            for x in nobj.relations[cobj].node_objects.copy():
                self.set_pin_descendants((x.name, cobj.name));
        return results;
    def set_pin_generations(self, pin, all_related=True):
        #This relates all ancestral and descendant pins. The only thing is it doesn’t specify a secondary node; so, it does this with all secondary nodes for the pin. Write another method that does just one secondary node.
        #If all_related is True, it does this with all related nodes (not just ancestral and descendant ones).
        a_results=self.set_pin_ancestors(pin);
        d_results=self.set_pin_descendants(pin);
        for x in d_results:
            self.set_pin_ancestors((x, pin[1]));
        if all_related==True:
            for x in a_results:
                self.set_pin_descendants((x, pin[1]));
    def set_pin_generations_all(self, context=None):
        #This sets ancestor and descendant pins for all nodes with a given context (if context is None then it does all contexts).
        con={context};
        if context==None:
            for x in self.cnco:
                con.add(x);
        for c in con:
            for x in self.nnno:
                pin=(x, c);
                a_results=self.set_pin_ancestors(pin);
                d_results=self.set_pin_descendants(pin);
                for d in d_results:
                    self.set_pin_ancestors((d, pin[1]));

"""
if __name__ == "__main__":
    import run;
"""