#!/usr/bin/env python3
#ð

#Written on 1–2 September 2017 (Friday)

import random, fractions;

class Switch:
    def __init__(self, item):
        self.switch(item);
    def __getitem__(self, item):
        #Index the object to switch a value with the equals operator.
        return self.case(op="==", value=item);
    def __contains__(self, item):
        return self.case_in_iter(value=item);
    def switch(self, item):
        #You can use this to set the value you’re switching to something else if you want to re-use the object, or change it in the middle of a switch.
        self.item=item;
    def case_in_iter(self, value):
        try:
            return eval("value in self.item");
        except TypeError:
            return False;
    def case(self, op, value):
        try:
            return eval("self.item "+op+" value");
        except TypeError:
            return False;
    def range(self, min, max):
        #Return true if the value is a number in the range.
        try:
            return self.item in range(min, max) or max==self.item or min==self.item;
        except TypeError:
            return False;
    def nrange(self, min, max):
        #Return True is the value is a number not in the range.
        return not self.range(min, max);
    def any(self, *items, op="=="):
        #Return true if the value is equal to any of the items.
        try:
            for x in items:
                if eval("self.item "+op+" x"):
                    return True;
            return False;
        except TypeError:
            return False;
    def all(self, *items, op="=="):
        #Return true is self.item is equal/op to all of the items.
        if len(items)>0:
            for item in items:
                if eval("self.item "+op+" item"):
                    pass;
                else:
                    return False
            return True
        else:
            return False;
    def rand(self, min, max):
        #Return True if self.item matches a random number between min and max. Otherwise, return False.
        n=random.randint(min, max);
        #print(n);
        return self.item==n;
    def rb(self, t=50, scale=100):
        #Random bool, based on the probability you enter. The default is 50/50.
        #Return True if the random bool is within 1 and t, and false if it’s greater than t and less than or equal to scale (no matter what self.item actually is). t and f determine the odds of it being True or False. If the scale is 100, and t is 50, then you have a 50/50 chance of it being True/False. f is scale minus t.
        f=scale-t;
        if t>scale:
            raise ValueError("t must be less than or equal to scale.");
        elif t==scale:
            return True;
        else:
            n=random.randint(1,scale);
            if n<=t:
                return True;
            else:
                return False;

"""
s=Switch(1);
if s.rb(6, 12):
    print("This is the 50/50 chance that happens whether or not we match the value.");
elif s.rand(1,5):
    print("It matches the random number!");
elif s.nrange(1,77):
    print("Not in range!");
elif s.any("453", 32434, "asdf"):
    print("any!");
elif s.all(-5, -6, -7, -3, op=">"):
    print("all!");
elif s[5]:
    print("Five!");
elif s[7]:
    print("Seven!");
elif s[8]:
    print("Eight!");
elif s["hello!"]:
    print("Hello world!");
elif "e" in s:
    print("e");
elif s.range(100,400):
    print("range!");
elif s.case(">=", 500):
    print("Greater than or equal to 500!");
else:
    print("Else!");
"""