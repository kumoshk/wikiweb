from . dp_wikiweb import *;
from . jsscripts import jsscripts;
#from . switch import Switch;

"""
This is for containing methods for conversion to HTML and other formats.
"""

home_file="""

""".strip();

class ExpProject(DPProject):
    def __init__(self, *args, **kwargs):
        DPProject.__init__(self, *args, **kwargs);
    def node_to_html(self, name, css="stylesheet.css", script="scripts.js", html_export_script="html_export_script", show_all=False):
        #Convert a node to an HTML page/article. If nodes, contexts or relations have "hidden" set to True, they are excluded.
        file_string="";
        obj=self.nnno[name];
        if obj.title!=None:
            if show_all==False:
                file_string+="<h1><abbr title=\""+name+"\">"+obj.title+"</abbr></h1>";
            else:
                file_string+="<h1>"+obj.title+" ("+name+")</h1>";
        else:
            file_string+="<h1>"+name+"</h1>";
        if len(obj.aliases)>0:
            file_string+="\n<h2>Aliases:</h2>\n<ul>";
            file_string+="\n<li />"+"\n<li />".join(self.sort(obj.aliases));
            file_string+="\n</ul>";
        def get_article_nodes(aname):
            aname=aname.groups()[0];
            title=None;
            if aname.endswith(".jpg") or aname.endswith(".png") or aname.endswith(".gif"):
                return "<img src=\"images/"+aname+"\" />";
            elif "\\" in aname:
                aname,title=aname.split("\\",1);
            if title==None:
                return '<a href="" onclick=\'update_params("'+str(self.nnno[aname].id)+'.html", ""); return false\'>'+aname+'</a>';
            else:
                return '<a href="" onclick=\'update_params("'+str(self.nnno[aname].id)+'.html", ""); return false\'>'+title+'</a>';
        if "desc" in obj.a:
            article=obj.a["desc"];
            article=re.sub(r"/([^/]+)/", r"<i>\1</i>", article);
            article=re.sub(r"\^([^\^]+)\^", r"<s>\1</s>", article);
            article=re.sub(r"\*([^\*]+)\*", r"<b>\1</b>", article);
            article=re.sub(r"\_([^\_]+)\_", r"<u>\1</u>", article);
            article=re.sub(r"\[\[([^\]]+)\]\]", get_article_nodes, article);
            file_string+="\n\n"+article+"\n\n";
        sorted_relations=[];
        #for context_obj, relation in obj.relations.items():
        for x in obj.relations:
            if not x.hidden and not obj.relations[x].bool("hidden"):
                sorted_relations.append(x.name);
        #sorted_relations.sort();
        sorted_relations=self.sort(sorted_relations);
        for iter_cname in sorted_relations:
            context_obj=self.cnco[iter_cname];
            relation=obj.relations[context_obj];
            if len(relation.node_objects)>0:
                if context_obj.title!=None:
                    file_string+="\n<h2><abbr title=\""+context_obj.name+"\">"+context_obj.title+":</abbr></h2>";
                else:
                    file_string+="\n<h2>"+context_obj.name+":</h2>";
                #for sec_node, sec_attr in relation.node_objects.items():
                sorted_node_objects=[];
                for x in relation.node_objects:
                    if not x.hidden:
                        sorted_node_objects.append(x.name);
                #sorted_node_objects.sort();
                sorted_node_objects=self.sort(sorted_node_objects);
                if len(sorted_node_objects)>10:
                    file_string+="<i>(Members: "+ str(len(sorted_node_objects))+")</i>";
                file_string+="\n<dl>"
                for iter_nname in sorted_node_objects:
                    sec_node=self.nnno[iter_nname];
                    sec_attr=relation.node_objects[sec_node];
                    if sec_node.cross_title!=None:
                        if show_all==False:
                            #file_string+="\n<dt /><a href=\"\" onclick='update_params(\""+str(sec_node.id)+".html\", \""+(str(sec_attr["html_update_params"]) if "html_update_params" in sec_attr else "")+"\"); return false'><abbr title=\""+sec_node.name+"\">"+sec_node.cross_title+"</abbr></a> <i>(Date last linked: "+self.date_string(relation.rel_node_objects[sec_node.id]["dates_created"][-1])+")</i>";
                            file_string+="\n<dt /><a href=\"\" onclick='update_params(\""+str(sec_node.id)+".html\", \""+(str(sec_attr["html_update_params"]) if "html_update_params" in sec_attr else "")+"\"); return false'><abbr title=\""+sec_node.name+"\">"+sec_node.cross_title+"</abbr></a> <i>(Relation ID: "+str(self.get_relation_node_id(name, iter_cname, sec_node.name))+")</i>";
                        else:
                            #file_string+="\n<dt /><a href=\"\" onclick='update_params(\""+str(sec_node.id)+".html\", \""+(str(sec_attr["html_update_params"]) if "html_update_params" in sec_attr else "")+"\"); return false'><abbr title=\""+sec_node.name+"\">"+sec_node.cross_title+" ("+sec_node.name+")"+"</abbr></a> <i>(Date last linked: "+self.date_string(relation.rel_node_objects[sec_node.id]["dates_created"][-1])+")</i>";
                            file_string+="\n<dt /><a href=\"\" onclick='update_params(\""+str(sec_node.id)+".html\", \""+(str(sec_attr["html_update_params"]) if "html_update_params" in sec_attr else "")+"\"); return false'><abbr title=\""+sec_node.name+"\">"+sec_node.cross_title+" ("+sec_node.name+")"+"</abbr></a> <i>(Relation ID: "+str(self.get_relation_node_id(name, iter_cname, sec_node.name))+")</i>";
                    else:
                        #file_string+="\n<dt /><a href=\"\" onclick='update_params(\""+str(sec_node.id)+".html\", \""+(str(sec_attr["html_update_params"]) if "html_update_params" in sec_attr else "")+"\"); return false'>"+sec_node.name+"</a> <i>(Date last linked: "+self.date_string(relation.rel_node_objects[sec_node.id]["dates_created"][-1])+")</i>";
                        file_string+="\n<dt /><a href=\"\" onclick='update_params(\""+str(sec_node.id)+".html\", \""+(str(sec_attr["html_update_params"]) if "html_update_params" in sec_attr else "")+"\"); return false'>"+sec_node.name+"</a> <i>(Relation ID: "+str(self.get_relation_node_id(name, iter_cname, sec_node.name))+")</i>";
                    relation_link_desc=self.grlattr(obj.name, context_obj.name, sec_node.name, "desc");
                    if relation_link_desc!=None and relation_link_desc.strip()!="":
                        file_string+="\n<dd>"+relation_link_desc+"</dd>";
                file_string+="\n</dl>";
        return "<html>\n<header>\n<meta charset=\"UTF-8\" />\n<link rel=\"stylesheet\" type=\"text/css\" href=\"stylesheet.css\" />\n<title>"+name+"</title>\n</header>\n<body>\n<script src=\""+script+"\"></script>\n<script>"+  ("\n"+obj.a[html_export_script]+"\n" if html_export_script in obj.a else "") +"</script>\n"+file_string+"\n<p><i>Date created: "+self.date_string(obj.date_created)+"</i></p>\n</body>\n</html>";
    def make_html_index_string(self, css="stylesheet.css", script="scripts.js", html_export_script="html_export_script", show_all=False):
        file_string="<h1>"+self.name+"</h1>\n<dl>";
        #for x in sorted(set(self.nnno.keys())):
        for x in self.sort(set(self.nnno.keys())):
            if self.nnno[x].hidden==False:
                file_string+="\n<li /><a href=\""+str(self.nnno[x].id)+".html\">"+x+"</a>: ID: "+str(self.nnno[x].id);
        return "<html>\n<header>\n<meta charset=\"UTF-8\" />\n<link rel=\"stylesheet\" type=\"text/css\" href=\"stylesheet.css\" />\n<title>"+self.name+"</title>\n</header>\n<body>\n<script src=\""+script+"\"></script>\n<script>"+  ("\n"+self.a[html_export_script]+"\n" if html_export_script in self.a else "") +"</script>\n"+file_string+"\n</dl>\n<p><i>Date created: "+self.date_string(self.date_created)+"</i></p>\n</body>\n</html>";
    def html_export(self, make_index=False):
        directory_path=os.path.join(self.dirpath, "html_export");
        if os.path.isdir(directory_path)==True:
            shutil.rmtree(directory_path);
        os.makedirs(directory_path);
        if not os.path.exists(self.imgpath):
            os.makedirs(os.path.join(directory_path, "images"));
        else:
            shutil.copytree(self.imgpath, os.path.join(directory_path, "images"));
        with open(os.path.join(directory_path, "scripts.js"), "w") as FILE:
            FILE.write(jsscripts);
        if make_index==True:
            html_index=self.make_html_index_string();
            with open(os.path.join(directory_path, "sitemap.html"), "w") as FILE:
                FILE.write(html_index);
        for node_name in self.nnno:
            if node_name not in self.node_aliases:
                node_html=self.node_to_html(node_name);
                with open(os.path.join(directory_path, str(self.nnno[node_name].id)+".html"), "w") as FILE:
                    FILE.write(node_html);
            else:
                pass; #The non-alias node has the file used for all the aliases (and itself).

"""
if __name__ == "__main__":
    import run;
"""