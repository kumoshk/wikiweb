"""
This file is meant to contain a function that translates some plain text into HTML, in the manner I desire.

This is to do quick data entry for the "desc" attribute of Node objects.

To do:
• Blockquotes
• Nested lists
• Nested blockquotes
• Text styles (bold, italic, underline, strikethrough)
• Images
• Internal links
• External links
• Headings (make something to separate the stuff below/above from it so the headings don’t conflict with relations and aliases)
• Preformatted text
• Tables (you can use delimited multi-line strings)

This isn’t meant to be the exclusive way to do things (it’s just for a data entry command—granted, not the line-by-line sort). You should be able to do pure HTML if you want (including via a data entry command).
"""

import regex as re;
import math;

def num_start_spaces(text):
    return len(text)-len(text.lstrip(" "));

def translate(text):
    line=text.split("\n");
    i=0;
    list_type=None; #Options are ordered, unordered, and desc
    indents=[]; #Values are the number of indents on the line.
    while i<len(line):
        spaces=num_start_spaces(line[i]);
        if spaces%4!=0:
            raise ValueError("You have "+str(spaces)+" spaces on line "+str(i)+". It must be a multiple of 4.");
        indents.append(int(spaces/4));
        i+=1;
    i=0;
    while i<len(line):
        if line[i].strip()=="":
            pass;
        else:
            if i==0 and i==len(line)-1: #First and last line.
                pass;
            elif i==0: #First line
                if line[i+1].strip()=="" and line[i].startswith("    ")==False:
                    line[i]="<p>"+line[i]+"</p>";
                elif line[i+1].strip()=="" and line[i].startswith("    ")==True:
                    line[i]="<blockquote>"+line[i].strip()+"</blockquote>";
            elif i==len(line)-1: #Last line
                if line[i-1].strip()=="" and line[i].startswith("    ")==False:
                    line[i]="<p>"+line[i]+"</p>";
                elif line[i-1].strip()=="" and line[i].startswith("    ")==True:
                    line[i]="<blockquote>"+line[i].strip()+"</blockquote>";
            else:
                if line[i-1].strip()=="" and line[i+1].strip()=="" and line[i].startswith("    ")==False:
                    line[i]="<p>"+line[i]+"</p>";
                elif line[i-1].strip()=="" and line[i+1].strip()!="" and line[i].startswith("    ")==False:
                    if line[i].startswith("*") or line[i].startswith("•"):
                        line[i]="<ul>\n<li />"+line[i][1:].strip();
                        list_type="unordered";
                    elif line[i].startswith("1.") or line[i].startswith("1)"):
                        line[i]="<ol>\n<li />"+line[i][2:].strip();
                        list_type="ordered";
                    else:
                        line[i]="<dl>\n<dt />"+line[i];
                        list_type="desc";
                elif line[i-1].strip()!="" and line[i+1].strip()=="" and line[i].startswith("    ")==False:
                    if line[i].startswith("*") or line[i].startswith("•"):
                        line[i]="<li />"+line[i][1:].strip()+"\n</ul>";
                    elif list_type=="ordered":
                        line[i]=re.sub(r"^\d+[\.)] *", r"", line[i]);
                        line[i]="<li />"+line[i].strip()+"\n</ol>";
                    else:
                        line[i]="<dt />"+line[i]+"\n</dl>";
                    list_type=None;
                elif list_type=="unordered":
                    #&&&Make it so you can nest lists. Use the indents list (unless you have another idea that works better).
                    line[i]="<li />"+line[i][1:].strip();
                elif list_type=="ordered":
                    line[i]=re.sub(r"^\d+[\.)] *", r"", line[i]);
                    line[i]="<li />"+line[i].strip();
                elif list_type=="desc":
                    if line[i].startswith("    "):
                        line[i]="<dd>"+line[i][1:].strip()+"</dd>";
                    else:
                        line[i]="<dt />"+line[i];
                #line[i]=re.sub(r"^\S", r"", line[i]);
                """
                line[i]=re.sub(r"", r"", line[i]);
                line[i]=re.sub(r"", r"", line[i]);
                line[i]=re.sub(r"", r"", line[i]);
                """
        i+=1;
    return "\n".join(line).strip();

def lstrip(text):
    while text.startswith("\n"):
        text=text[1:];
    while text.endswith("\n"):
        text=text[:-1];
    return text;

test="""
This is a test!

Hi!

Ho!

• One!
    This is a test!
    This is a test!
• Two!
• Test!
• Three!
• Four!
• Five!

Hey.
""";
test=lstrip(test);

print(translate(test));