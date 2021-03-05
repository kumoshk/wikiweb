from . wikiweb import *;

"""
This contains print and data entry methods, but is otherwise like wikiweb.
"""

class HiddenError(Error):
    pass;

class UserExistsError(Error):
    pass;

class NotLoggedInError(Error):
    pass;

class LoggedInError(Error):
    pass;

class User:
    def __init__(self, id, name, enabled=True, password=None, sex=None, dob=None):
        self.date_created=datetime.datetime.now(datetime.timezone.utc); #We add an argument instead of using utcnow() because we want an aware datetime object (not a naive one); this allows us to convert it to the local timezone later.
        self.id=id;
        self.password=password; #If None then no password is required. Passwords should be hashes.
        self.name=name;
        self.triggers=[]; #These are for executing functions upon visiting a node. Nodes, Contexts, Relations, Relation links, Projects, and Users can all have triggers.
        self.hidden=False;
        self.detect_hidden=False;
        self.sex=sex;
        #The following sets should take tuples with element 0 being the kind (e.g. home/mobile/work) and element 1 being the address/email/phone/etc.
        self.address=set();
        self.email=set();
        self.phone=set();
        self.dob=dob; #date of birth: a datetime object should be passed in (with Project.date_parse)
        self.current_node=None; #Current node
        self.node_history=[];
        self.relation_link_history=[None];
        self.enabled=enabled;
        self.a={}; #attributes
    def __repr__(self):
        return "¡User object ‘"+self.name+"’ ID="+str(self.id)+"¡";
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

#These are passed in as arguments to Project.__init__() below (to replace the old classes with these; so, the original Project can use these).
class DPNode(Node):
    def __init__(self, *args, **kwargs):
        self.triggers=[]; #These are for executing functions upon visiting a node. Nodes, Contexts, Relations, Relation links, Projects, and Users can all have triggers.
        self.hidden=False;
        self.exit_triggers=[]; #These are triggers that go off when you exit a node.
        Node.__init__(self, *args, **kwargs);
class DPRelation(Relation):
    def __init__(self, *args, **kwargs):
        self.triggers=[]; #These are for executing functions upon visiting a node. Nodes, Contexts, Relations, Relation links, Projects, and Users can all have triggers.
        self.hidden=False;
        Relation.__init__(self, *args, **kwargs);
class DPContext(Context):
    def __init__(self, *args, **kwargs):
        self.triggers=[]; #These are for executing functions upon visiting a node. Nodes, Contexts, Relations, Relation links, Projects, and Users can all have triggers.
        self.hidden=False;
        Context.__init__(self, *args, **kwargs);

class DPProject(Project):
    def __init__(self, *args, **kwargs):
        self.unuo={}; #This is for user name to user object
        self.user_id_count=0; #This is used to give each user a unique ID that doesn’t change.
        self.deleted_user_ids=[];
        self.reuse_deleted_user_ids=False;
        #self.hash_algorithm="sha3_512"; #Change to this after you start using Python 3.6+
        self.hash_algorithm="bcrypt";
        self.log_rounds=8; #For use with bcrypt
        self.authenticated=Group(); #Keys are user objects; values are a unique (and hard to guess/calculate) value used to identify the session (so people who hack the client can’t use anyone’s session who is already logged in unless they have the unique value). These are the users that are logged in (with a correct password, if required).
        self.home_node=None;
        self.triggers=[]; #These are for executing functions upon visiting a node. Nodes, Contexts, Relations, Relation links, Projects, and Users can all have triggers.
        #The stuff above is above to allow it to be saved (anything below the constructor call below won’t save).
        Project.__init__(self, *args, **kwargs, node_class=DPNode, relation_class=DPRelation, context_class=DPContext);
        self.unid=nidDict(self.unuo);
        self.idun=idnDict(self.unuo);
        self.iduo=idoDict(self.unuo);
        if "msgbox" in kwargs:
            self.msgbox=kwargs["msgbox"]; #This is so you can pass in a GUI’s message box method. &&&Perhaps this should be an attribute to the project instead.
        else:
            self.msgbox=None;
        if "pr" in kwargs:
            self.pr=kwargs["pr"]; #This is so you can pass in a print method. &&&Perhaps this should be an attribute to the project instead.
        else:
            self.pr=print;
    def data_entry(self, mstring, delim="|", concat_char="*", command_char="&", formatted_quotes=True, formatted_dashes=True, hyphen_rep="--", dash_rep="—", inheritance_char="#"):
        #This allows for flexible data entry by importing a block of text (the data) to parse. This is particularly designed for adding plant varieties.
        #Make another one that isn’t designed for making nodes of a specific type that always end with a certain word or set of words.
        #If there’s an exception, nothing done in self.data_entry is saved, unless you handle the exception and save it afterward. (In that case, you may wish to use self.save_rollback() and self.load_rollback() to overcome that obstacle.)
        mstring=mstring.strip();
        strings=re.split(r" *\n *\n *", mstring);
        if len(strings)%2>0:
            print(strings);
            raise ValueError("Your string is improperly formatted. Each set of instructions must have a heading, and vice versa.");
        """
        if self.default_context not in self.cnco:
            self.make_context(self.default_context, self.default_cross);
        """
        def format_chars(text):
            #Makes sure text is either formatted or not formatted, according to what is desired with the parameters above.
            #This applies to the standard data entry method where no command character is used (to both primary and secondary nodes, as well as to descriptions). The only commands where the command character is used that this is applies to are for creating and renaming nodes and contexts (with the exception of renaming with regular expressions).
            text=text.strip();
            if formatted_quotes==False: #If this is False, formatted quotes will be converted to quotes that aren’t formatted; nothing changes if it is True.
                text=text.replace("’", "'"); #I add this because I format them on accident sometimes (and we need consistency).
                text=text.replace("‘", "'");
                text=text.replace("“", "\"");
                text=text.replace("”", "\"");
            else:
                #text=re.sub(r"(\w)'(\w)", r"\1’\2", text);
                text=re.sub(r"(\S)'", r"\1’", text); #This makes sure most apostrophes are converted to be formatted correctly. This also takes care of situations with abbreviations (e.g. J.D.’s Special C-Tex tomato)
                if "'" in text or '"' in text:
                    raise ValueError("Unformatted quotes are not allowed, and single quotes that begin a word, and any double quotes, are not converted (and this error is produced). Try again with them pre-formatted, or make formatted_quotes=False.");
            if formatted_dashes==False:
                text=text.replace("—", hyphen_rep);
                text=text.replace(" – ", hyphen_rep);
            else:
                text=text.replace("--", dash_rep);
                text=text.replace(" - ", dash_rep);
            return text;
        while 1:
            concat=False;
            command=False;
            inherit=False;
            kinds=[];
            try:
                kind=strings[0].strip();
                keep_looping=True;
                while keep_looping==True and (kind.startswith(concat_char) or kind.startswith(inheritance_char) or kind.startswith(command_char)):
                    if kind.startswith(command_char) and command==False and concat==False:
                        command=True;
                        kind=kind[1:];
                        keep_looping=False;
                    elif kind.startswith(inheritance_char) and inherit==False:
                        inherit=True;
                        kind=kind[1:];
                    elif kind.startswith(concat_char) and concat==False and command==False:
                        concat=True
                        kind=kind[1:];
                    else:
                        keep_looping=False;
                instructions=strings[1].split("\n");
            except IndexError:
                break;
            context=self.default_context;
            contexts=[];
            line_contexts=[];
            if delim in kind and command==False: #node1|node2|node3||context1a|context1b||context2a|context2b|||line_context1a|line_context1b||line_context2a|line_ontext2b
                halves=kind.split(delim+delim+delim,1);
                if len(halves)>1:
                    pairs=halves[1].split(delim+delim);
                    for pair in pairs:
                        if delim not in pair:
                            line_contexts.append({"context":pair, "cross":None});
                        else:
                            line_context=pair.split(delim,1)
                            line_contexts.append({"context":line_context[0], "cross":line_context[1]});
                halves=halves[0].split(delim+delim);
                for half in halves:
                    the_kind={"primary":None, "context":None, "cross":None};
                    try:
                        the_kind["primary"], the_kind["context"], the_kind["cross"]=half.split(delim);
                    except ValueError:
                        try:
                            the_kind["primary"], the_kind["context"]=half.split(delim);
                            the_kind["cross"]=None;
                        except:
                            the_kind["primary"]=half.split(delim)[0];
                            the_kind["cross"]=None;
                            the_kind["context"]=self.default_context;
                    kinds.append(the_kind);
                for pair in kinds+line_contexts: #&&&&
                    if pair["context"]=="" or pair["cross"]=="":
                        raise ValueError("A context name string has a length of zero. Fix the error causing this.");
                    if pair["context"] not in self.cnco and pair["cross"]!=None:
                        if pair["cross"] in self.cnco:
                            raise ValueError("‘"+pair["cross"]+"’ is already in a context pair with ‘"+self.cnco[pair["cross"]].cross.name+"’.");
                        else:
                            self.make_context(pair["context"], pair["cross"]);
                    elif pair["context"] in self.cnco and pair["cross"]!=None:
                        if self.cnco[pair["context"]].cross.name==pair["cross"]:
                            pair["cross"]=None; #&&& Check here if you have unexplained issues. Debug. This is here to make sure that data entry stuff can be ignored if it has already been created.
                        else:
                            raise ValueError("‘"+pair["context"]+"’ already exists in a context pair with ‘"+self.cnco[pair["context"]].cross.name+"’ You attempted to create a new context pair with it and ‘"+pair["cross"]+"’.");
                    elif pair["context"] not in self.cnco and pair["cross"]==None:
                        print(contexts, "HERE", line_contexts);
                        raise ValueError("The context, ‘"+pair["context"]+"’, does not exist.");
                    elif pair["context"] in self.cnco and pair["cross"]==None:
                        pass; #We don’t need to do anything here, since the proper pair already exists.
            else:
                kinds.append({"primary":kind, "context":self.default_context, "cross":self.default_cross});
            if command==True:
                if kind in {"rn", "rename nodes", "rename node", "rnode", "rnodes"}:
                    for line in instructions:
                        line=line.strip();
                        old_name, new_name=line.split(delim, 1);
                        old_name=format_chars(old_name);
                        new_name=format_chars(new_name);
                        self.rename_node(old_name, new_name);
                elif kind in {"rc", "rename contexts", "rename context", "rcontext", "rcontexts", "rcon"}:
                    for line in instructions:
                        line=line.strip();
                        old_name, new_name=line.split(delim, 1);
                        old_name=format_chars(old_name);
                        new_name=format_chars(new_name);
                        self.rename_context(old_name, new_name);
                elif kind in {"mn", "nodes", "node", "n", "make node", "make nodes", "mnode", "mnodes", "cn", "create node", "create nodes", "cnode", "cnodes"}:
                    for line in instructions:
                        line=line.strip();
                        name=None;
                        aliases=[];
                        alias_roots=[];
                        if delim in line:
                            name, aliases_start=line.split(delim, 1);
                            name=format_chars(name);
                            for alias in aliases_start.split(delim):
                                if alias.strip()=="":
                                    raise ValueError("One of your aliases is blank. Did you put || where | should have been in creating an alias?");
                                if alias not in self.nnno:
                                    aliases.append(format_chars(alias.strip()));
                                else:
                                    alias_roots.append(format_chars(alias.strip()));
                            roots=set();
                            for root in alias_roots:
                                roots.add(self.nnno[root].name);
                            if len(roots)>1:
                                raise ValueError("You are attempting to add multiple aliases that already exist, but they don’t point to the same thing.");
                        else:
                            name=format_chars(line);
                        if len(alias_roots)>0:
                            self.make_node_alias(alias_roots[0], name); #Make entry an alias instead of a regular node.
                        else:
                            self.make_node(name);
                        for x in aliases:
                            self.make_node_alias(name, x);
                elif kind in {"mc", "contexts", "context", "con", "c", "make context", "make contexts", "make context pair", "make context pairs", "mcontext", "mcontexts", "cc", "create context", "create contexts", "create context pair", "create context pairs", "ccontext", "ccontexts"}:
                    for line in instructions:
                        line=line.strip();
                        try:
                            name, cross, make_default=line.split(delim, 2);
                            if make_default.lower() in {"true", "t", "yes", "y", "default", "make default"}:
                                make_default=True;
                            else:
                                raise ValueError2("The third argument when making a context must be 'true', 't', 'yes', 'y', 'make default', or 'default'—they all mean the same thing; their absence is the only other option.");
                        except ValueError:
                            name, cross=line.split(delim, 1);
                            make_default=False;
                        name=format_chars(name);
                        cross=format_chars(cross);
                        self.make_context(name, cross, make_default);
                elif kind.startswith("relate ") or kind.startswith("rel ") or kind.startswith("r "):
                    #What this does is make it so you can add the same relation between several different primary node / secondary node pairs (instead of between one Primary node and several secondary nodes). It creates the contexts if they don’t exist.
                    #e.g.
                    """
                    &rel is a|includes||second context
                    
                    grasshopper|insect
                    snail|mollusk
                    cat|mammal
                    
                    This will make grasshopper an insect, and snail a mollusk. It will also relate them similarly with the second context. It will first create the includes|is a context (but second context should already be created since the other side isn’t mentioned).
                    """
                    
                    kind=" ".join(kind.split(" ")[1:]); #Getting rid of the command name so we just have the context or context pair
                    kind=format_chars(kind);
                    our_contexts=[];
                    for cpair in kind.split(delim+delim):
                        if delim in cpair:
                            side1, side2=cpair.split(delim);
                            self.make_context(side1, side2);
                            our_contexts.append(side1);
                        else:
                            our_contexts.append(cpair);
                    for line in instructions:
                        line=line.strip();
                        line=format_chars(line);
                        node1, node2=line.split(delim,1);
                        if node1 not in self.nnno:
                            self.make_node(node1);
                        if node2 not in self.nnno:
                            self.make_node(node2);
                        for cont in our_contexts:
                            self.make_relation(node1, cont, node2);
                elif kind in {"pin regex delim", "prd"}:
                    for line in instructions:
                        line=line.strip();
                        try:
                            node, context, regex=line.split(delim);
                            if node not in self.nnno:
                                self.make_node(node);
                            #self.pin_regex((node, context), regex, inheritance=inherit);
                            self.pin_regex((node, context), regex);
                        except ValueError:
                            node, context, regex, exclude_regex=line.split(delim);
                            if node not in self.nnno:
                                self.make_node(node);
                            #self.pin_regex((node, context), regex, exclude_regex, inheritance=inherit);
                            self.pin_regex((node, context), regex, exclude_regex);
                elif kind in {"pin regex", "pr", "regex pin"}:
                    for line in instructions:
                        line=line.strip();
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"pins to use", "node and context"} and "pin" not in line:
                                line["pin"]=linecopy[x];
                                del line[x];
                            elif x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"include pins", "ipins", "in pins", "inpins", "within pins"} and "include_pins" not in line:
                                line["include_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"exclude pins", "epins", "expins", "ex pins", "not these pins"} and "exclude_pins" not in line:
                                line["exclude_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                        if "text" not in line or "pin" not in line:
                            raise KeyError("pin and text must be set, although you can use aliases for them. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"pin", "text", "exclude_text", "include_pins", "exclude_pins", "cs"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for pin regex.");
                        #self.pin_regex(**line, inheritance=inherit);
                        self.pin_regex(**line);
                elif kind in {"html update parameters", "html update params", "hup", "huparams", "hu params"}:
                    for line in instructions:
                        line=line.strip();
                        primary, context, secondary, parameters=line.split(delim,3);
                        self.lattr(primary, context, secondary, "html_update_params", parameters);
                elif kind in {"link attribute", "relation link attribute", "link attributes", "lattr", "link attr", "relation link attributes", "rla"}:
                    for line in instructions:
                        line=line.strip();
                        try:
                            primary, context, secondary, key, value_type, value=line.split(delim,5);
                        except ValueError:
                            primary, context, secondary, key, value=line.split(delim,4);
                            self.lattr(primary, context, secondary, key, value);
                            continue
                        value_type=value_type.lower().strip();
                        node_obj=self.nnno[primary];
                        if value_type in {"datetime", "date time", "date", "dt"}:
                            dto=self.date_parse(value);
                            if dto!=None:
                                value=dto;
                            else:
                                raise ValueError("‘"+value+"’ is not a recognized date format.");
                        elif value_type in {"i", "int", "integer"}:
                            value=int(value);
                        elif value_type in {"fl", "float"}:
                            value=float(value);
                        elif value_type in {"fr", "fraction"}:
                            value=fractions.Fraction(value);
                        elif value_type in {"b", "bool", "boolean"}:
                            value=bool(value);
                        elif value_type in {"s", "st", "str", "string"}:
                            pass; #It’s already a string!
                        elif value_type in {"literal_eval", "eval", "evaluate", "literal eval", "literal evaluate", "auto", "Python type", "python type"}:
                            #This allows you to enter a Python type the same way you would in code (remember, strings need quotes, and comments allowed).
                            value=ast.literal_eval(value);
                        else:
                            raise ValueError("The type, ‘"+value_type+"’, is not currently a valid type. You only need declare a type if it’s not to be stored as a string.");
                        self.lattr(primary, context, secondary, key, value);
                elif kind in {"pin startswith", "pin sw", "pinsw"}:
                    for line in instructions:
                        line=line.strip();
                        text, node, context=line.split(delim,2);
                        if node not in self.nnno:
                            self.make_node(node);
                        #self.pin_startswith(text, (node, context), inheritance=inherit);
                        self.pin_startswith(text, (node, context));
                elif kind in {"pin endswith", "pin ew", "pinew"}:
                    for line in instructions:
                        line=line.strip();
                        text, node, context=line.split(delim,2);
                        if node not in self.nnno:
                            self.make_node(node);
                        #self.pin_endswith(text, (node, context), inheritance=inherit);
                        self.pin_endswith(text, (node, context));
                elif kind in {"disconnect", "dc", "disc", "disconnect nodes", "disconnect node", "dcn", "dc node", "dc nodes", "discn", "disc n", "disc node", "disc nodes"}:
                    for line in instructions:
                        line=line.strip();
                        if line not in self.nnno:
                            raise ValueError("‘"+line+"’ is not a node and therefore cannot be disconnected.");
                        else:
                            self.disconnect(line);
                elif kind in {"delete node", "del node", "d node", "dnode", "dn", "delete nodes", "del nodes", "d nodes", "dnodes"}:
                    for line in instructions:
                        line=line.strip();
                        if line not in self.nnno:
                            raise ValueError("‘"+line+"’ is not a node and therefore cannot be deleted.");
                        else:
                            self.delete_node(name=line);
                elif kind in {"delete context", "del context", "d context", "dcontext", "dcon", "del con", "delcon", "dc", "delete contexts", "del contexts", "d contexts", "dcontexts"}:
                    for line in instructions:
                        line=line.strip();
                        if line not in self.cnco:
                            raise ValueError("‘"+line+"’ is not a context and therefore cannot be deleted.");
                        else:
                            self.delete_context(name=line);
                elif kind in {"regex node matches", "find nodes with regex", "regex node match", "find node regex"} and (self.msgbox!=None or self.pr!=None):
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"sort it", "sort"} and "sort_it" not in line:
                                line["sort_it"]=linecopy[x];
                            elif x in {"include pins", "ipins", "in pins", "inpins", "within pins"} and "include_pins" not in line:
                                line["include_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"exclude pins", "epins", "expins", "ex pins", "not these pins"} and "exclude_pins" not in line:
                                line["exclude_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                        if "text" not in line:
                            raise KeyError("text must be set, although you can use aliases for it. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "exclude_text", "sort_it", "include_pins", "exclude_pins", "cs"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for regex_node_matches.");
                        report=self.regex_node_matches(**line);
                        if self.msgbox!=None:
                            self.msgbox("‘"+regex+"’, excluding: ‘"+ex_regex+"’ regex matches", "\n".join(report));
                        else:
                            self.pr("Matches for this regex: ‘"+regex+"’\nExcluding this regex: ‘"+ex_regex+"’\n\n"+"\n".join(report));
                elif kind in {"regex context matches", "find contexts with regex", "regex context match", "find context regex"} and (self.msgbox!=None or self.pr!=None):
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"sort it", "sort"} and "sort_it" not in line:
                                line["sort_it"]=linecopy[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                        if "text" not in line:
                            raise KeyError("text must be set, although you can use aliases for it. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "exclude_text", "sort_it", "cs"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for regex_context_matches.");
                        report=self.regex_context_matches(**line);
                        if self.msgbox!=None:
                            self.msgbox("‘"+regex+"’, excluding: ‘"+ex_regex+"’ regex matches", "\n".join(report));
                        else:
                            self.pr("Matches for this regex: ‘"+regex+"’\nExcluding this regex: ‘"+ex_regex+"’\n\n"+"\n".join(report));
                elif kind in {"rrn", "regex rename node", "rename node regex", "regex node rename", "node regex rename", "node rename regex"}:
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"replace text", "replace regex", "replace"} and "replace_text" not in line:
                                line["replace_text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"include pins", "ipins", "in pins", "inpins", "within pins"} and "include_pins" not in line:
                                line["include_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"exclude pins", "epins", "expins", "ex pins", "not these pins"} and "exclude_pins" not in line:
                                line["exclude_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                        if "text" not in line or "replace_text" not in line:
                            raise KeyError("text and replace_text must be set, although you can use aliases for them. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "replace_text", "exclude_text", "include_pins", "exclude_pins", "cs"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for regex rename node.");
                        self.regex_rename_node(**line);
                elif kind in {"del nr", "delete nr", "delete node regex", "del node regex", "regex del node", "regex delete node", "del regex node", "delete regex node"}:
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"include pins", "ipins", "in pins", "inpins", "within pins"} and "include_pins" not in line:
                                line["include_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"exclude pins", "epins", "expins", "ex pins", "not these pins"} and "exclude_pins" not in line:
                                line["exclude_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                            elif x in {"delete relations", "del relations", "del rel", "delete rel", "del r"} and "delete_relations" not in line:
                                line["delete_relations"]=linecopy[x];
                                del line[x];
                        if "text" not in line:
                            raise KeyError("text must be set, although you can use aliases for it. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "exclude_text", "include_pins", "exclude_pins", "cs", "delete_relations"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for del node regex.");
                        self.del_node_regex(**line);
                elif kind in {"del cr", "delete cr", "delete context regex", "del context regex", "regex del context", "regex delete context", "del regex context", "delete regex context"}:
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"sort it", "sort"} and "sort_it" not in line:
                                line["sort_it"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                        if "text" not in line:
                            raise KeyError("text must be set, although you can use aliases for it. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "exclude_text", "sort_it", "cs"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for del context regex.");
                        self.del_context_regex(**line);
                elif kind in {"dis r", "disr", "disc r", "discr", "disconnect r", "disconnect regex", "dis regex", "disc regex", "regex dis", "regex disc", "r dis", "r disc", "regex disconnect node", "dis regex node", "disc regex node", "disconnect regex node"}:
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"include pins", "ipins", "in pins", "inpins", "within pins"} and "include_pins" not in line:
                                line["include_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"exclude pins", "epins", "expins", "ex pins", "not these pins"} and "exclude_pins" not in line:
                                line["exclude_pins"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                            elif x in {"delete relations", "del relations", "del rel", "delete rel", "del r"} and "delete_relations" not in line:
                                line["delete_relations"]=linecopy[x];
                                del line[x];
                        if "text" not in line:
                            raise KeyError("text must be set, although you can use aliases for it. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "exclude_text", "include_pins", "exclude_pins", "cs", "delete_relations"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for disconnect regex.");
                        self.disconnect_regex(**line);
                elif kind in {"rrc", "regex rename context", "rename context regex", "regex context rename", "context regex rename", "context rename regex"}:
                    for line in instructions:
                        if line.startswith("{") and line.endswith("}"):
                            line=ast.literal_eval(line.strip());
                        else:
                            line=ast.literal_eval("{"+line.strip()+"}");
                        linecopy=line.copy();
                        for x in linecopy:
                            if x in {"t", "search", "search text", "regex", "search regex"} and "text" not in line:
                                line["text"]=linecopy[x];
                                del line[x];
                            elif x in {"replace text", "replace regex", "replace"} and "replace_text" not in line:
                                line["replace_text"]=linecopy[x];
                                del line[x];
                            elif x in {"extext", "exclude text", "ex text", "exclude regex", "ex", "exclude"} and "exclude_text" not in line:
                                line["exclude_text"]=linecopy[x];
                                del line[x];
                            elif x in {"case sensitive"} and "cs" not in line:
                                line["cs"]=linecopy[x];
                                del line[x];
                        if "text" not in line or "replace_text" not in line:
                            raise KeyError("text and replace_text must be set, although you can use aliases for them. Got only ‘"+str(line)+"’");
                        for x in line:
                            if x not in {"text", "replace_text", "exclude_text", "cs"}:
                                raise KeyError("‘"+str(x)+"’ is not an applicable key for regex rename context.");
                        self.regex_rename_context(**line);
                elif kind in {"nt", "ntitle", "node title", "n title"}: #This sets the title of each node you specify. The title is displayed instead of the name when the title is present (but only the name can be used in self.nnno and such). The title isn’t much use to the programmer (just to the viewer of the running program). When the name is renamed, the default is for the title to be deleted.
                    for line in instructions:
                        node_name, title=line.split(delim,1);
                        node_name=format_chars(node_name);
                        title=format_chars(title.strip());
                        node_obj=self.nnno[node_name];
                        node_obj.a["title"]=title;
                elif kind in {"ct", "ctitle", "context title", "c title"}:
                    for line in instructions:
                        context_name, title=line.split(delim,1);
                        context_name=format_chars(context_name);
                        title=format_chars(title.strip());
                        context_obj=self.cnco[context_name];
                        context_obj.a["title"]=title;
                elif kind in {"a", "at", "att", "attr", "attribute", "attributes"}:
                    #def node_a(self, name, **kwargs)
                    for line in instructions:
                        line=line.strip();
                        try:
                            node_name,attribute,value_type,value=line.split(delim,3);
                        except ValueError:
                            node_name,attribute,value=line.split(delim,2);
                            node_obj=self.nnno[node_name];
                            node_obj.a[attribute]=value;
                            continue;
                        value_type=value_type.lower().strip();
                        node_obj=self.nnno[node_name];
                        if value_type in {"datetime", "date time", "date", "dt"}:
                            dto=self.date_parse(value);
                            if dto!=None:
                                value=dto;
                            else:
                                raise ValueError("‘"+value+"’ is not a recognized date format.");
                        elif value_type in {"i", "int", "integer"}:
                            value=int(value);
                        elif value_type in {"fl", "float"}:
                            value=float(value);
                        elif value_type in {"fr", "fraction"}:
                            value=fractions.Fraction(value);
                        elif value_type in {"b", "bool", "boolean"}:
                            value=bool(value);
                        elif value_type in {"s", "st", "str", "string"}:
                            pass; #It’s already a string!
                        elif value_type in {"literal_eval", "eval", "evaluate", "literal eval", "literal evaluate", "auto", "Python type", "python type"}:
                            #This allows you to enter a Python type the same way you would in code (remember, strings need quotes, and comments allowed).
                            value=ast.literal_eval(value);
                        else:
                            raise ValueError("The type, ‘"+value_type+"’, is not currently a valid type. You only need declare a type if it’s not to be stored as a string.");
                        node_obj.a[attribute]=value;
                elif kind in {"delete relation", "drel", "dr", "del relation", "delete relations", "del relations", "d relations", "d rel", "d relation", "del rel", "delrel", "delete relationship", "del relationship", "delete relationships", "del relationships", "d relationships", "d relationship", "delete rel", "remove relation", "remove rel"}:
                    for line in instructions:
                        primary, context, secondaries=line.split(delim, 2);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its relationship or relationships cannot be deleted.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the pertinent relationship or relationships cannot be deleted.");
                        secondaries=secondaries.split(delim);
                        for x in secondaries:
                            if x not in self.nnno:
                                raise ValueError("‘"+x+"’ is not a node; therefore its relationship or relationships cannot be deleted.");
                        self.remove_relation(primary, context, *secondaries);
                elif kind in {"disable descendant inheritance", "disable desc", "disable descendants", "dis desc"}:
                    for line in instructions:
                        primary, context=line.split(delim, 1);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its descendant inheritance cannot be disabled.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the descendant inheritance of this pin cannot be disabled.");
                        self.set_pin_descendant_inheritance((primary, context));
                elif kind in {"disable ancestor inheritance", "disable anc", "disable ancestors", "dis anc"}:
                    for line in instructions:
                        primary, context=line.split(delim, 1);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its ancestor inheritance cannot be disabled.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the ancestor inheritance of this pin cannot be disabled.");
                        self.set_pin_ancestor_inheritance((primary, context));
                elif kind in {"enable descendant inheritance", "enable desc", "enable descendants", "en desc"}:
                    for line in instructions:
                        primary, context=line.split(delim, 1);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its descendant inheritance cannot be enabled.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the descendant inheritance of this pin cannot be enabled.");
                        self.set_pin_descendant_inheritance((primary, context), True);
                elif kind in {"enable ancestor inheritance", "enable anc", "enable ancestors", "en anc"}:
                    for line in instructions:
                        primary, context=line.split(delim, 1);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its ancestor inheritance cannot be enabled.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the ancestor inheritance of this pin cannot be enabled.");
                        self.set_pin_ancestor_inheritance((primary, context), True);
                elif kind in {"set ancestor inheritance", "set anc", "set ancestors"}:
                    for line in instructions:
                        primary, context, the_bool=line.split(delim, 2);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its ancestor inheritance cannot be set.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the ancestor inheritance of this pin cannot be set.");
                        the_bool=bool(the_bool);
                        self.set_pin_ancestor_inheritance((primary, context), the_bool);
                elif kind in {"set descendant inheritance", "set desc", "set descendants"}:
                    for line in instructions:
                        primary, context, the_bool=line.split(delim, 2);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its descendant inheritance cannot be set.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the descendant inheritance of this pin cannot be set.");
                        the_bool=bool(the_bool);
                        self.set_pin_descendant_inheritance((primary, context), the_bool);
                elif kind in {"set inheritance", "set inh"}:
                    #This sets both ancestor and descendant inheritance to the same thing, at once.
                    for line in instructions:
                        primary, context, the_bool=line.split(delim, 2);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its inheritance cannot be set.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the inheritance of this pin cannot be set.");
                        the_bool=bool(the_bool);
                        self.set_pin_ancestor_inheritance((primary, context), the_bool);
                        self.set_pin_descendant_inheritance((primary, context), the_bool);
                elif kind in {"enable inheritance", "enable inh", "en inh", "en inheritance"}:
                    #This enables both ancestor and descendant inheritance to the same thing, at once.
                    for line in instructions:
                        primary, context=line.split(delim, 1);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its inheritance cannot be enabled.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the inheritance of this pin cannot be enabled.");
                        self.set_pin_ancestor_inheritance((primary, context), True);
                        self.set_pin_descendant_inheritance((primary, context), True);
                elif kind in {"disable inheritance", "disable inh", "dis inh", "dis inheritance"}:
                    #This disables both ancestor and descendant inheritance to the same thing, at once.
                    for line in instructions:
                        primary, context=line.split(delim, 1);
                        if primary not in self.nnno:
                            raise ValueError("‘"+primary+"’ is not a node; therefore its inheritance cannot be disabled.");
                        if context not in self.cnco:
                            raise ValueError("‘"+context+"’ is not a context; therefore the inheritance of this pin cannot be disabled.");
                        self.set_pin_ancestor_inheritance((primary, context), False);
                        self.set_pin_descendant_inheritance((primary, context), False);
                elif delim in kind: #If you need to add another that uses this, do it within here (not in this if/elif/else).
                    if kind.split(delim)[0] in {"delete relation", "drel", "dr", "del relation", "delete relations", "del relations", "d relations", "d rel", "d relation", "del rel", "delrel", "delete relationship", "del relationship", "delete relationships", "del relationships", "d relationships", "d relationship", "delete rel", "remove relation", "remove rel"}:
                        pcontext=self.default_context;
                        try:
                            kind, pnode=kind.split(delim);
                        except ValueError:
                            kind, pnode, pcontext=kind.split(delim, 2);
                        if pnode not in self.nnno:
                            raise ValueError("‘"+pnode+"’ is not a node; therefore its relationship or relationships cannot be deleted.");
                        else:
                            for line in instructions:
                                line=line.strip();
                                if line not in self.nnno:
                                    raise ValueError("‘"+line+"’ is not a node and therefore its relationship with ‘"+pnode+"’ cannot be deleted.");
                                else:
                                    self.remove_relation(pnode, pcontext, line);
                    elif kind.split(delim)[0] in {"multiple relations", "multirel", "misc rel", "miscrel", "misc relations", "miscellaneous relations"}:
                        command=None;
                        context=self.default_context;
                        if delim in kind:
                            command, context = kind.split(delim, 1);
                        else:
                            command=kind;
                        for line in instructions:
                            aliases=[];
                            secondary=None;
                            if delim in line:
                                secondary, aliases_start=line.strip().split(delim, 1);
                                secondary=format_chars(secondary).strip();
                                for alias in aliases_start.split(delim):
                                    if alias.strip()=="":
                                        raise ValueError("One of your aliases is blank. Did you put || where | should have been in creating an alias?");
                                    aliases.append(alias.strip());
                            else:
                                secondary=format_chars(line.strip());
                            primary=""; #Get the primary node from the last lower-case words of the line.
                            for x in secondary.split():
                                if x[0].islower()==True:
                                    primary+=" "+x;
                                else:
                                    primary="";
                            primary=primary.strip();
                            if primary=="":
                                raise ValueError("‘"+secondary+"’ has no primary node at the end of its name.");
                            if secondary not in self.nnno:
                                try:
                                    self.make_node(secondary, overwrite=False);
                                except NodeExistsError:
                                    pass;
                            if primary not in self.nnno:
                                try:
                                    self.make_node(primary, overwrite=False);
                                except NodeExistsError:
                                    pass;
                            #Make the relation
                            self.make_relation(primary, context, secondary);
                            for x in aliases:
                                self.make_node_alias(secondary, x);
                    else:
                        raise ValueError("‘"+kind+"’ is not a recognized command.");
                else:
                    raise ValueError("‘"+kind+"’ is not a recognized command.");
            else:
                #del kind;
                for kind in kinds:
                    kind["primary"]=format_chars(kind["primary"]);
                    if kind["primary"] not in self.nnno:
                        self.make_node(kind["primary"]);
                    for line in instructions:
                        line=line.strip();
                        entry=None;
                        aliases=[];
                        alias_roots=[];
                        if delim in line:
                            entry,aliases_start=line.split(delim,1);
                            entry=format_chars(entry);
                            for alias in aliases_start.split(delim):
                                if alias.strip()=="":
                                    raise ValueError("One of your aliases is blank. Did you put || where | should have been in creating an alias?");
                                if concat==True:
                                    alias=alias.strip()+" "+kinds[0]["primary"];
                                if alias not in self.nnno:
                                    aliases.append(format_chars(alias.strip()));
                                else:
                                    alias_roots.append(format_chars(alias.strip()));
                            roots=set();
                            for root in alias_roots:
                                roots.add(self.nnno[root].name);
                            if len(roots)>1:
                                raise ValueError("You are attempting to add multiple aliases that already exist, but they don’t point to the same thing.");
                            if concat==True:
                                entry=entry.strip()+" "+kinds[0]["primary"];
                            else:
                                entry=entry.strip();
                        else:
                            line=format_chars(line);
                            if concat==True:
                                entry=line+" "+kinds[0]["primary"];
                            else:
                                entry=line;
                        if entry not in self.nnno:
                            if len(alias_roots)>0:
                                self.make_node_alias(alias_roots[0], entry); #Make entry an alias instead of a regular node.
                            else:
                                self.make_node(entry, overwrite=False); #Don’t let it overwrite unless you want it to wipe out relations, too (which could make problems for data entry as it processes one thing at a time).
                        else:
                            pass;
                        if kind["context"]!=None:
                            self.make_relation(kind["primary"], kind["context"], entry);
                        else:
                            self.make_relation(kind["primary"], self.default_context, entry);
                        if len(line_contexts)>0:
                            #Make the secondary (or line) relation, if a context for one is specified; so, if the line says `Cherokee Purple tomato` and the line_context is `is a` it will do (Cherokee Purple tomato, is a, tomato). It gathers the lowercase words following any uppercase words to make the secondary node: e.g.
                            """
                            Shule|grew in 2017||is a
                            
                            Cherokee Purple tomato
                            """
                            primary=entry;
                            secondary="";
                            if concat==True:
                                secondary=kinds[0]["primary"];
                            else:
                                for x in primary.split():
                                    if x[0].islower()==True:
                                        secondary+=" "+x;
                                    else:
                                        secondary="";
                                secondary=secondary.strip();
                                if secondary=="":
                                    #raise ValueError("‘"+primary+"’ has no secondary node at the end of its name.");
                                    pass;
                                if secondary not in self.nnno:
                                    try:
                                        if len(alias_roots)>0:
                                            self.make_node_alias(alias_roots[0], secondary);
                                        else:
                                            self.make_node(secondary, overwrite=False);
                                    except NodeExistsError:
                                        pass;
                            for pair in line_contexts:
                                self.make_relation(primary, pair["context"], secondary);
                        for x in aliases:
                            self.make_node_alias(entry, x);
                    if inherit==True:
                        if len(contexts)>0:
                            for pair in contexts:
                                self.set_pin_generations((kind["primary"], pair["context"])); #&&&&
                        else:
                            self.set_pin_generations((kind["primary"], self.default_context));
            strings.pop(0);
            strings.pop(0);
    def date_check(self, date, directives):
        #Checks a date and if it's valid, it returns a datetime object of that date. If it's invalid, it returns None.
        date=date.replace(",", "");
        date=re.sub(r"(\d)+(st|nd|rd|th)", r"\1", date);
        try:
            return datetime.datetime.strptime(date, directives);
        except ValueError:
            return None;
    def date_parse(self, date_str):
        #Returns a datetime object when you give a string date. This is used in self.data_entry() for parsing human-entered dates that were entered in any of a variety of formats.
        if re.search(r"\d\d\d\d$", date_str)==None:
            year=int(date_str[-2:]);
            today=datetime.datetime.today();
            cur_year=int(str(today.year)[-2:]);
            if year>cur_year:
                last_century=str(today.year-100)[:2];
                my_year=last_century+str(year);
                date_str=re.sub(r"\d+$", my_year, date_str);
        #Century is set.
        date_list=date_str.split();
        date=None;
        directives=["%d %B %Y", "%d %b %Y", "%d %B %y", "%d %b %y", "%b %d %Y", "%b %d %y", "%B %d %Y", "%B %d %y", "%m/%d/%Y", "%m/%d/%y"]; #Add more
        for x in directives:
            date=self.date_check(date_str, x);
            if date!=None:
                break;
        return date; #Returns None if the string isn't formatted correctly, or if it's not a date.
    def date_string(self, dt, directive=None):
        #Converts a date-time object to a string date formatted the default way, if directive is None; otherwise, return a date string using the directive specified.
        if directive==None:
            if sys.platform not in ["win32", "cygwin"]:
                #If it’s not Windows
                return dt.astimezone().strftime("%-d %b %Y (%-I:%M:%S:%f %p) %Z");
            else:
                return dt.astimezone().strftime("%#d %b %Y (%-I:%M:%S:%f %p) %Z");
        else:
            return dt.astimezone().strftime(directive);
    def print_nodes(self):
        #for x in sorted(set(self.nnno.keys())):
        for x in self.sort(set(self.nnno.keys())):
            if "desc" in self.nnno[x].a:
                print(x+":\n\tID: "+str(self.nnno[x].id)+"\n\tDesc: "+self.nnno[x].a["desc"]);
            else:
                print(x+":\n\tID: "+str(self.nnno[x].id));
                #Get rid of the if else statement and just make it list all the attributes in a for loop here starting with a tab.&&&
    def print_relations(self, name, print_ids=False):
        context_name_list=set();
        for x in self.nnno[name].relations:
            context_name_list.add(x.name);
        if print_ids:
            print("Relations for node ‘"+name+"’ (ID: "+str(self.nnno[name].id)+"):");
        else:
            print("Relations for node ‘"+name+"’:");
        #for x in sorted(context_name_list):
        for x in self.sort(context_name_list):
            node_name_list=set();
            for y in self.nnno[name].relations[self.cnco[x]].node_objects:
                node_name_list.add(y.name);
            print("\t"+x);
            #for y in sorted(node_name_list):
            for y in self.sort(node_name_list):
                relNodeID=self.nnno[name].relations[self.cnco[x]].rel_node_objects[self.nnno[y].id];
                if print_ids:
                    print("\t\t"+y+"\t(RNID "+str(relNodeID)+"; ID "+str(self.nnno[y].id)+")");
                else:
                    print("\t\t"+y);
    def print_all_relations(self, print_ids=False):
        #for x in sorted(set(self.nnno.keys())):
        for x in self.sort(set(self.nnno.keys())):
            self.print_relations(x, print_ids);
    def set_html_update_params(self, primary, context, secondary, parameters):
        #This allows you to set how HTML parameters change when you follow a relation to a secondary node (from a primary node). This is useful for creating e-books with persistent data.
        self.lattr(primary, context, secondary, "html_update_params", parameters);
    def is_secondary(self, primary, secondary):
        #This tells you if secondary is a secondary node to primary through any of its relations.
        obj=self.nnno[primary];
        for co in obj.relations:
            if not co.hidden:
                for nobj in obj.relations[co]:
                    if nobj.name==secondary:
                        if not nobj.hidden:
                            return True;
        return False;
    def valid_password(self, pw, hashedpw):
        #This compares a password with a hash
        if self.hash_algorithm=="bcrypt":
            return bcrypt.checkpw(pw.encode(), hashedpw.encode());
        else:
            return self.hash(pw)==hashedpw;
    def login(self, user_name, password=None):
        if self.unuo[user_name] in self.authenticated:
            raise LoggedInError("The user, ‘"+user_name+"’, is already logged in.");
        elif self.unuo[user_name].enabled==False:
            raise DisabledError("`enabled` has been set to false for this user. You cannot log in.");
        elif password==None:
            if self.unuo[user_name].password==None:
                self.authenticated[self.unuo[user_name]]=random.getrandbits(1024);
            else:
                raise ValueError("Wrong password.");
        elif self.valid_password(password, self.unuo[user_name].password):
            self.authenticated[self.unuo[user_name]]=random.getrandbits(1024);
        else:
            raise ValueError("Wrong password.");
    def logout(self, user_name):
        if self.unuo[user_name] not in self.authenticated:
            raise NotLoggedInError("That user is not logged in. You cannot log out.");
        else:
            self.authenticated.remove(self.unuo[user_name]);
    def inc_user(self):
        if self.reuse_deleted_user_ids and len(self.deleted_user_ids)>0:
            return self.deleted_user_ids.pop();
        else:
            self.user_id_count+=1;
            return self.user_id_count-1;
    def claim_user_id(self, id):
        if id not in self.deleted_user_ids:
            raise ValueError("‘"+str(id)+"’ is not a deleted user id.");
        else:
            return self.deleted_user_ids.pop(self.deleted_user_ids.index(id));
    def make_user(self, name, password=None):
        if name in self.unuo:
            raise UserExistsError("That name is already taken.");
        else:
            user=User(id=self.inc_user(), name=name, password=self.hash(password));
            self.unuo[name]=user;
    def hash(self, text): #Use sha3_512 when you update to Xubuntu 17.10 (bcrypt passwords can only be so long before they’re truncated). &&&
        if self.hash_algorithm=="bcrypt":
            hash=bcrypt.hashpw(text.encode(), bcrypt.gensalt(self.log_rounds));
            return hash.decode();
        else:
            hash=hashlib.new(self.hash_algorithm);
            hash.update(text.encode());
            return hash.hexdigest();
    def change_user_password(self, username, old_pw, new_pw):
        #To remove a password, do new_pw=None
        new_pw.upper(); #Just checking to see if it’s a string.
        uo=self.unuo[username];
        #if self.hash(old_pw)==uo.password:
        if self.valid_password(old_pw, uo.password):
            uo.password=self.hash(new_pw) if new_pw!=None else None;
        else:
            raise ValueError("Incorrect password.");
    def rename_user(self, old_name, new_name):
        if old_name not in self.unuo:
            raise IndexError("‘"+old_name+"’ is not a user. You cannot rename it.");
        elif new_name in self.unuo:
            raise ValueError("‘"+new_name+"’ is already taken. You cannot rename ‘"+old_name+"’ to that.");
        else:
            obj=self.unuo[old_name];
            obj.name=new_name;
            del self.unuo[old_name];
            self.unuo[new_name]=obj;
    def del_user(self, name):
        #Deletes a user from the database.
        if name in self.unuo:
            user_obj=self.unuo[name];
            del self.unuo[name];
            self.deleted_user_ids.append(user_obj.id);
        else:
            raise ValueError("The user, ‘"+name+"’ does not exist.");
    def delete_user(self, name):
        self.del_user(name);
    def clear_history(self, user_name):
        self.unuo[user_name].node_history.clear(); #We’re clearing it in case the list is stored somewhere else (if we made a new list, the old list would still be stored elsewhere).
    def visit(self, user_name, node_name, context=None, primary=None, trigger_order=("project", "leave primary", "context", "relation", "relation link", "enter secondary"), show_hidden=False):
        #This method allows you to visit a node (not necessarily via a relation).
        #This is not for HTML export. See node.a["html_update_params"] (in wikiweb_with_exports.py see pro.node_to_html()) and jsscripts.py (and pro.html_export()) for doing similar things with JavaScript.
        #triggers are functions that are executed when you visit a node. Trigger attributes should be lists (of functions/methods). Omit kinds of triggers in the order if you don’t wish them to be executed.
        #To change the trigger order, simply change the value of trigger_order to your specified order (as opposed to the default).
        user=self.unuo[user_name];
        if user not in self.authenticated:
            raise NotLoggedInError("That user is not logged in.");
        if context==None:
            if self.nnno[node_name].hidden==False or show_hidden==True or user.detect_hidden==True:
                user.node_history.append(self.nnno[node_name]);
                user.relation_link_history.append(context);
                user.current_node=self.nnno[node_name];
                for kind in trigger_order:
                    if kind=="project":
                        for x in self.triggers:
                            x(primary=self.nnno[primary], context=self.cnco[context], secondary=self.nnno[node_name]);
                    elif kind=="enter secondary":
                        for x in self.nnno[node_name].triggers:
                            x(secondary=self.nnno[node_name]);
            else:
                raise HiddenError("‘"+node_name+"’ is hidden and you cannot detect hidden. You cannot visit it.");
        elif primary==None and context!=None:
            raise ValueError("primary must not be None if context is not None.");
        else:
            if self.cnco[context] not in self.nnno[primary].relations:
                raise KeyError("‘"+context+"’ is not a relation of ‘"+primary+"’.");
            else:
                if self.nnno[node_name] not in self.nnno[primary].relations[self.cnco[context]].node_objects:
                    raise KeyError("‘"+node_name+"’ is not a secondary node of ‘"+primary+"’ with the ‘"+context+"’ context.");
                else:
                    if (self.nnno[node_name].hidden==False and self.cnco[context].hidden==False) or show_hidden==True or user.detect_hidden==True:
                        user.node_history.append(self.nnno[node_name]);
                        user.relation_link_history.append(context);
                        user.current_node=self.nnno[node_name];
                        #Trigger order: context, relation, relation link, secondary node
                        for kind in trigger_order:
                            if kind=="project":
                                for x in self.triggers:
                                    x(primary=self.nnno[primary], context=self.cnco[context], secondary=self.nnno[node_name]);
                            elif kind=="leave primary":
                                for x in self.nnno[primary].exit_triggers:
                                    x(primary=self.nnno[primary], context=self.cnco[context], secondary=self.nnno[node_name]);
                            elif kind=="context":
                                for x in self.cnco[context].triggers:
                                    x(primary=self.nnno[primary], context=self.cnco[context], secondary=self.nnno[node_name]);
                            elif kind=="relation":
                                for x in self.nnno[primary].relations[self.cnco[context]].triggers:
                                    x(primary=self.nnno[primary], context=self.cnco[context], secondary=self.nnno[node_name]);
                            elif kind=="relation link":
                                if "triggers" in self.nnno[primary].relations[self.cnco[context]].node_objects[self.nnno[node_name]]:
                                    for x in self.nnno[primary].relations[self.cnco[context]].node_objects[self.nnno[node_name]]["triggers"]:
                                        x(primary=self.nnno[primary], context=self.cnco[context], secondary=self.nnno[node_name]);
                            elif kind=="enter secondary":
                                for x in self.nnno[node_name].triggers:
                                    x(secondary=self.nnno[node_name]);
                            else:
                                raise ValueError("‘"+str(kind)+"’ is not a supported kind of trigger for ‘trigger_order’.");
                    else:
                        raise HiddenError("Something here is hidden. You cannot visit that location.");

"""
if __name__ == "__main__":
    import run;
"""