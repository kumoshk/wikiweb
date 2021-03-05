jsscripts="""/*
    This provides functions that allow you to have persistent data in such as e-books and hypertext fiction (so long as JavaScript and URL parameters are allowed), as well as variables that pass from page to page. To save your progress, just bookmark whatever page you’re on (the saved data is in the URL itself). This even works offline (unlike some forms of persistent data used with websites), and you don’t have to worry about servers (just the e-book). update_params() is the main function some will want to use (and get_params() will allow you to use the parameters; dict_to_params() will convert it back to something you can put on a URL, if you want to manipulate the values in your code, rather than with the submission).
    To use update_params(), use this format for the parameters (the first shows what you do to instantiate variables; the second shows how to change them):
    1. URL for the next page, name:Maynard, age:22, level:1, beltcolor:blue
    2. URL for the next page, age|*=5, level++, beltcolor|del (this means, multiply the age by 5 to make it 110, increase the level by 1, to 2, and delete the beltcolor parameter; the name is retained and unchanged)
*/

function rall(s, r, the_string)
{
    return the_string.split(s).join(r)
}

var equal_symbol=":" //You don’t want to actually use equals as it’ll cause some problems with math operations (which use the character).

function get_params() //Get the parameters and put them into an object (which is kind of like a Python dictionary, with key-value pairs).
{
    var received_params=window.location.search.substr(1)
    //received_params=atob(received_params)
    //received_params=decodeURI(received_params)
    received_params=decodeURI(atob(received_params))
    var params_dict={}
    if (received_params!="")
    {
        var params_array=received_params.split("&")
        for (var x in params_array) //x is actually the element number (not the value as it would be in Python)
        {
            var x_split=params_array[x].split(equal_symbol)
            var action=""
            if (x_split[1].includes("|"))
            {
                action_split=x_split[1].split("|")
                x_split[1]=action_split[0]
                action=action_split[1]
            }
            if (isNaN(x_split[1])==true)
            {params_dict[x_split[0]]=x_split[1]}
            else
            {
                params_dict[x_split[0]]=Number(x_split[1])
                eval("params_dict[x_split[0]]"+action)
                //This let's you do such as x:5|++ (to increment x to 6), or x:43|*=2 (to make x 86). 
            }
        }
    }
    return params_dict
}

function dict_to_params(the_dict) //Convert the dictionary-like object back into a text string of paramters to put into the URL.
{
    var result=""
    var i=0
    for (x in the_dict)
    {
        if (Object.keys(the_dict).length-1!=i)
        {
            result+=x+equal_symbol+the_dict[x]+"&"
        }
        else
        {
            result+=x+equal_symbol+the_dict[x]
        }
        i++
    }
    return result
}

function get_and_write_params() //This is just for debugging purposes (so you can write the parameters to the screen).
{
    var received_params=window.location.search.substr(1)
    var params_dict=get_params()
    if (Object.keys(params_dict).length>0)
    {
        var i=0
        for (x in params_dict)
        {
            document.write("<p>"+x+": "+params_dict[x]+"</p>")
            i++
        }
    }
}

function submit_params(web_url, params) //This submits parameters, but it doesn’t update them (although it does allow you to create new ones).
{
    params=rall(" ", "", params)
    if (params!="")
    {
        var result=web_url+"?"+btoa(encodeURI(rall(",", "&", params))) //To hide the parameters and allow Unicode parameters at the same time.
        //var result=web_url+"?"+rall(",", "&", params)
        window.location=result
    }
    else
    {
        window.location=web_url
    }
}

function update_params(web_url, params) //This updates and submits the parameters. You can do math on number parameters and delete any parameter.
{
    params=rall(" ", "", params)
    var params_dict=get_params()
    if (params!="")
    {
        var params_array=params.split(",")
        for (var x in params_array) //x is actually the element number (not the value as it would be in Python)
        {
            if (params_array[x].includes(equal_symbol)) //the value is replaced
            {
                var x_split=params_array[x].split(equal_symbol)
                var action=""
                if (x_split[1].includes("|"))
                {
                    action_split=x_split[1].split("|")
                    x_split[1]=action_split[0]
                    action=action_split[1]
                }
                if (isNaN(x_split[1])==true)
                {
                    params_dict[x_split[0]]=x_split[1]
                }
                else
                {
                    params_dict[x_split[0]]=Number(x_split[1])
                    eval("params_dict[x_split[0]]"+action)
                    //This let's you do such as x:5|++ (to increment x to 6), or x:43|*=2 (to make x 86). 
                }
            }
            else if (params_array[x].includes("|")) //the value is modified
            {
                var x_split=params_array[x].split("|")
                if (x_split[1]=="del")
                {
                    delete params_dict[x_split[0]]
                }
                else
                {
                    eval("params_dict[x_split[0]]"+x_split[1])
                }
                //e.g. value1|++ means increment the current value of value1. value2|*=2 means multiply it by two.
            }
        }
    }
    var result_params=dict_to_params(params_dict)
    submit_params(web_url, result_params)
}"""