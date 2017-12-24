#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
cache = {}
data = {}
#convert events:# -> storylets:# because events are a separate thing

def render(string):
    string = re.sub(r'<.{,2}?br.{,2}?>','\n', string)
    string = re.sub(r'<.{,2}?[pP].{,2}?>','', string)
    string = string.replace('<em>', '_')
    string = string.replace('<i>', '_')
    string = string.replace('</em>', '_')
    string = string.replace('</i>', '_')
    string = string.replace('<strong>', '\x1B[1m*')
    string = string.replace('</strong>', '*\x1B[0m')
    string = string.replace('<b>', '\x1B[1m*')
    string = string.replace('</b>', '*\x1B[0m')
    return string

def render_requirements(rl, fate):
    reqs = []
    challenges = []
    if fate is not None:
        reqs.append('{} FATE'.format(fate))
    for r in rl:
        if r.type == 'Requirement':
            reqs.append(str(r))
        else:
            challenges.append(str(r))
    if not reqs and not challenges:
        return 'None'
    return ', '.join(reqs) + '\n' + '\n'.join(challenges)


class Storylet: #done?
    def __init__(self, jdata):
        global data
        self.raw = jdata
        self.title = jdata.get('Name', '(no title)')
        self.desc = jdata.get('Description', '(no description)')
        self.id = jdata.get('Id', '(no id)')
        try:
            self.setting = Setting.get(jdata['Setting']['Id'])
        except KeyError:
            self.setting = None
        try:
            self.area = Area.get(jdata['LimitedToArea'])
        except KeyError:
            self.area = None
        try:
            self.availability = jdata['Deck']['Name']
        except KeyError:
            self.availability = None
        self.requirements = []
        for r in jdata['QualitiesRequired']:
            self.requirements.append(Requirement(r))
        self.branches = []
        for b in jdata['ChildBranches']:
            self.branches.append(b)
    def __repr__(self):
        return 'Storylet ID {}: "{}"'.format(self.id, self.title)
    def __str__(self):
        #_,c = os.popen('stty size', u'r').read().split()
        return 'Storylet ID: {}\nStorylet Title: "{}"\nDescription: {}\nRequirements: {}\nBranches: {}'.format(
                        self.id,
                        self.title,
                        render(self.desc),
                        render_requirements(self.requirements, None),
                        '\n{}\n\n'\
                                .format('~' * 20)\
                                .join(self.render_branches()))
    def render_branches(self):
        return [str(b) for b in self.branches]
    @classmethod
    def get(self, id):
        global cache
        key = 'storylets:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            s = Storylet(data['events:{}'.format(id)])
            cache[key] = s
            cache[key].branches = [Branch.get(x, s) for x in s.branches]
            for b in s.branches:
                for e in list(b.events.items()):
                    if e[0].endswith('Event'):
                        e[1].parent = b
            return s

class Branch:   #done
    def __init__(self, jdata, parent):
        self.raw = jdata
        try:
            self.title = jdata['Name']
        except:
            self.title = '(no title)'
        self.id = jdata['Id']
        self.parent = parent
        try:
            self.desc = jdata['Description']
        except KeyError:
            self.desc = ''
        try:
            self.cost = jdata['ActionCost']
        except KeyError:
            self.cost = None
        try:
            self.button = jdata['ButtonText']
        except KeyError:
            self.button = 'Go'
        try:
            self.fate = jdata['CurrencyCost']
        except KeyError:
            self.fate = None
        try:
            self.act = Act.get(jdata['Act']['Id'])
        except KeyError:
            self.act = None
        self.requirements = []
        for r in jdata['QualitiesRequired']:
            self.requirements.append(Requirement(r))
        costs = [ r for r in self.requirements if r.is_cost ]
        self.events = {}
        for key in list(jdata.keys()):
            if key in ['DefaultEvent', 'SuccessEvent', 'RareSuccessEvent', 'RareSuccessEventChance', 'RareDefaultEvent', 'RareDefaultEventChance']:
                if key.endswith('Chance'):
                    self.events[key] = jdata[key]
                else:
                    self.events[key] = Event.get(jdata[key], costs)
    def __repr__(self):
        return '"{}"'.format(self.title)
    def __str__(self):
        return 'Branch Title: "{}"\nDescription: {}\nRequirements: {}\n{}'.format(self.title, render(self.desc) if self.desc is not None else '', render_requirements(self.requirements, self.fate if hasattr(self, 'fate') else None), render_events(self.events))
    @classmethod
    def get(self, jdata, parent=None):
        global cache
        key = 'branches:{}'.format(jdata['Id'])
        if key in cache:
            return cache[key]
        else:
            cache[key] = Branch(jdata, parent)
            return cache[key]
import os
def render_events(ed):
    #r,c = os.popen('stty size', u'r').read().split()
    strings = []
    try:
        se = ed['SuccessEvent']
        strings.append( 'Success: "{}"\n{}\nEffects: {}'.format(se.title, render(se.desc), se.list_effects()))
    except KeyError:
        pass
    try:
        rse = ed['RareSuccessEvent']
        strings.append('Rare Success: "{}" ({}% chance)\n{}\nEffects: {}'.format(rse.title, ed['RareSuccessEventChance'], render(rse.desc), rse.list_effects()))
    except KeyError:
        pass
    try:
        fe = ed['DefaultEvent']
        strings.append('{}: "{}"\n{}\nEffects: {}'.format('Failure' if len(strings) > 0 else 'Event', fe.title, render(fe.desc), fe.list_effects()))
    except KeyError:
        pass
    try:
        rfe = ed['RareDefaultEvent']
        strings.append('Rare {}: "{}" ({}% chance)\n{}\nEffects: {}'.format('Failure' if len(strings) > 1 else 'Success', rfe.title, ed['RareDefaultEventChance'], render(rfe.desc), rfe.list_effects()))
    except KeyError:
        pass
    return '\n{}\n\n'.format('-' * 20).join(strings)
import re 

#def parse_req(restriction):
#    reqs = re.findall(r'\[q:\d+\]', restriction)
#    for req in reqs:
class Requirement:  #done
    def __init__(self, jdata):
        self.raw = jdata
        self.quality = Quality.get(jdata['AssociatedQuality']['Id'])
        try:
            self.is_cost = jdata['IsCostRequirement']
        except KeyError:
            self.is_cost = False
        try:
            self.upper_bound = jdata['MaxLevel']
        except:
            try:
                self.upper_bound = sub_qualities(jdata['MaxAdvanced'])
            except KeyError:
                pass
        try:
            self.lower_bound = jdata['MinLevel']
        except:
            try:
                self.lower_bound = sub_qualities(jdata['MinAdvanced'])
            except KeyError:
                pass
        try:
            self.difficulty = jdata['DifficultyLevel']
        except:
            try:
                self.difficulty = jdata['DifficultyAdvanced']
            except KeyError:
                pass
        if hasattr(self, 'difficulty'):
            self.type = 'Challenge'
            self.test_type = self.quality.test_type
        else:
            self.type = 'Requirement'
        try:
            self.visibility = jdata['BranchVisibleWhenRequirementFailed']
        except KeyError:
            pass
    def __repr__(self):
        if self.type == 'Challenge':
            return '{} {}: {} {}'.format(self.test_type, self.type, self.quality.name, self.difficulty)
        else:
            try:
                if self.lower_bound == self.upper_bound:
                    return '{} exactly {}'.format(self.quality.name, self.lower_bound)
                else:
                    return '{} [{}-{}]'.format(self.quality.name, self.lower_bound, self.upper_bound)
            except:
                try:
                    return '{} at least {}'.format(self.quality.name, self.lower_bound)
                except:
                    return '{} no more than {}'.format(self.quality.name, self.upper_bound)
            

class Event:    #done
    def __init__(self, jdata, costs):
        self.raw = jdata
        self.id = jdata['Id']
        self.parent = None        
        try:
            self.title = jdata['Name']
        except KeyError:
            self.title = ''
        try:
            self.desc = jdata['Description']
        except KeyError:
            self.desc = ''
        try:
            self.category = jdata['Category']
        except KeyError:
            self.category = None
        
        self.effects = []
        for e in jdata['QualitiesAffected']:
            self.effects.append(Effect(e, costs))
        try:
            if jdata['ExoticEffects'] != '':
                self.exotic_effect = jdata['ExoticEffects']
            else:
                self.exotic_effect = None
        except KeyError:
            self.exotic_effect = None
        try:
            self.lodging = jdata['MoveToDomicile']['Id']
        except KeyError:
            self.lodging = None
        try:
            self.livingstory = jdata['LivingStory']['Id']
        except KeyError:
            self.livingstory = None
        try:
            self.img = jdata['Image']
        except KeyError:
            self.img = None
        try:
            self.newsetting = jdata['SwitchToSettingId']
        except KeyError:
            self.newsetting = None
        try:
            self.newarea = jdata['MoveToArea']
        except KeyError:
            self.newarea = None
        try:
            self.linkedevent = Storylet.get(jdata['LinkToEvent']['Id'])
        except KeyError:
            self.linkedevent = None
    def __repr__(self):
        return 'Event: {}'.format(self.title) if self.title != '' else 'Event: (no title)'
    def __str__(self):
        return 'Title: "{}"\nDescription: {}\nEffects: {}\n'.format(self.title if self.title != '' else '(no title)', render(self.desc), self.list_effects())
    def list_effects(self):
        string = ''
        if self.effects != []:
            string += '[{}]\n'.format(', '.join([str(e) for e in self.effects]))
        if self.exotic_effect:
            string += 'Exotic effect: {}\n'.format(self.exotic_effect)
        if self.livingstory:
            string += 'Triggers Living Story: {}\n'.format(self.livingstory) #todo make Livingstory class
        if self.lodging:
            string += 'Move to lodging: {}\n'.format(self.lodging) #todo make lodgings class
        if self.newsetting:
            string += 'Move to new setting: {}\n'.format(self.newsetting) #todo flesh out setting class
        if self.newarea:
            string += 'Move to new area: {}\n'.format(self.newarea)
        try:
            if self.parent.act:
                string += 'Associated social action: {}\n'.format(self.parent.act)
        except:
            pass
        if self.linkedevent:
            string += 'Linked event: "{}" (Id {})\n'.format(self.linkedevent.title, self.linkedevent.id)
        return string
        
    @classmethod
    def get(self, jdata, costs):
        global cache
        key = 'events:{}'.format(jdata['Id'])
        if key in cache:
            return cache[key]
        else:
            cache[key] = Event(jdata, costs)
            return cache[key]

def sub_qualities(string):
    for x in re.findall(r'\[q:(\d+)\]', string):
        string = string.replace(x, Quality.get(int(x)).name)
    return string


class Effect:   #done: Priority goes 3/2/1/0 #todo: integrate costs
    def __init__(self, effect, costs):
        self.raw = effect
        self.quality = Quality.get(effect['AssociatedQuality']['Id'])
        self.equip = 'ForceEquip' in effect
        try:
            self.amount = effect['Level']
        except:
            try:
                self.amount = sub_qualities(effect['ChangeByAdvanced'])
            except KeyError:
                pass
        try:
            self.setTo = effect['SetToExactly']
        except:
            try:
                self.setTo = sub_qualities(effect['SetToExactlyAdvanced'])
            except KeyError:
                pass
        try:
            self.ceil = effect['OnlyIfNoMoreThan']
        except KeyError:
            pass
        try:
            self.floor = effect['OnlyIfAtLeast']
        except KeyError:
            pass
        try:
            self.priority = effect['Priority']
        except KeyError:
            self.priority = 0
    def __repr__(self):
        try:
            limits = ' if no more than {} and at least {}'.format(self.ceil, self.floor)
        except:
            try:
                limits = ' if no more than {}'.format(self.ceil)
            except:
                try:
                    limits = ' only if at least {}'.format(self.floor)
                except:
                    limits = ''
                
        try:
            return '{} (set to {}{})'.format(self.quality.name, self.setTo, limits)
        except:
            if self.quality.nature == 2 or not self.quality.pyramid:
                try:
                    return '{:+} x {}{}'.format(self.amount, self.quality.name, limits)
                except:
                    return '{} {}{}'.format('' if self.amount.startswith('-') else '+' + self.amount, self.quality.name, limits)
            else:
                try:
                    return '{} ({:+} cp{})'.format(self.quality.name, self.amount, limits)
                except:
                    return '{} ({} cp{})'.format(self.quality.name, '' if self.amount.startswith('-') else '' + self.amount, limits)
                    

#debug 284734

class Quality:  #done
    def __init__(self, id):
        #HimbleLevel is used to determine order within categories for items
        jdata = data['qualities:{}'.format(id)]
        self.raw = jdata
        self.name = jdata['Name']
        self.id = id
        try:
            self.desc = jdata['Description']
        except KeyError:
            self.desc = ''
        self.pyramid = 'UsePyramidNumbers' in jdata
        try:
            self.desc += '\n' + jdata['LevelDescriptionText']
        except KeyError:
            pass
        try:
            self.nature = jdata['Nature'] #1: quality; 2: item
        except KeyError:
            self.nature = 1
            pass
        try:
            qldstr = jdata['ChangeDescriptionText']
            self.changedesc = parse_qlds(qldstr)
        except KeyError:
            pass
        try:
            qldstr = jdata['LevelDescriptionText']
            self.leveldesc = parse_qlds(qldstr)
        except KeyError:
            pass
        try:
            variables = {}
            d = json.loads(jdata['VariableDescriptionText'])
            for x in list(d.items()):
                variables[x[0]] = parse_qlds(x[1])
            self.variables = variables
        except KeyError:
            pass
        try:
            self.cap = jdata['Cap']
        except KeyError:
            pass
        try:
            self.category = jdata['Category']
        except KeyError:
            pass
        try:
            self.tag = jdata['Tag']
        except KeyError:
            pass
        if 'DifficultyTestType' in jdata:
            self.test_type = 'Narrow'
        else:
            self.test_type = 'Broad'
        try:
            self.difficulty = jdata['DifficultyScaler']
        except KeyError:
            pass
        try:
            self.slot = jdata['AssignToSlot']
        except KeyError:
            pass
        try:
            self.event = jdata['UseEvent']['Id']#fix
        except KeyError:
            pass
    def __repr__(self):
        return 'Quality: {}'.format(self.name)

    @classmethod
    def get(self, id):
        key = 'qualities:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Quality(id)
            try:
                cache[key].event = Storylet.get(cache[key].event)
            except AttributeError:
                pass
            return cache[key]

def parse_qlds(string):
    qld = {}
    qlds = string.split('~')
    for d in qlds:
        level, text = d.split('|', 1)
        level = int(level)
        qld[level] = text
    return qld

class Setting:  #definition unclear
    def __init__(self, id):
        temp = data['settings:{}'.format(id)]
        self.raw = temp
        self.title = temp['Name']
        description = temp['StartingArea']['Description']

    @classmethod
    def get(self, id):
        key = 'settings:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Setting(id)
            return cache[key]

class Area:
    def __init__(self, id):
        pass
    @classmethod
    def get(self, id):
        return Area(0)
    
class Act:  #for social actions
    def __init__(self, id):
        jdata = data['acts:{}'.format(id)]
        self.name = jdata['Name']
        self.msg = jdata['InviteMessage']
    def __repr__(self):
        return '"{}"'.format(self.name)
    @classmethod
    def get(self, id):
        key = 'acts:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Act(id)
            return cache[key]

class AccessCode:
    def __init__(self, jdata):
        self.raw = jdata
        try:
            self.name = jdata['Name']
        except:
            self.name = '(no name)'
        try:
            self.message1 = jdata['InitialMessage']
        except:
            self.message1 = '(no message)'
        try:
            self.message2 = jdata['CompletedMessage']
        except:
            self.message2 = '(no message)'
        self.effects = []
        for e in jdata['QualitiesAffected']:
            self.effects.append(Effect(e, None))
        return string
    def __str__(self):
        string = 'Access code name: {}'.format(self.name)
        string += '\nInitial message: {}'.format(self.message1)
        string += '\nFinish message: {}'.format(self.message2)
        string += '\nEffects: {}'.format(self.list_effects())
        return string
    def list_effects(self):
        if self.effects != []:
            return '[{}]'.format(', '.join([str(e) for e in self.effects]))
