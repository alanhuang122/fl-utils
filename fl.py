#!/usr/bin/python2
# -*- coding: utf-8 -*-
import json
cache = {}
data = {}
#convert events:# -> storylets:# because events are a separate thing

def render(string):
    string = re.sub(r'<.{,2}?br.{,2}?>',u'\n', string)
    string = re.sub(r'<.{,2}?[pP].{,2}?>',u'', string)
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
        if r.type == u'Requirement':
            reqs.append(unicode(r))
        else:
            challenges.append(unicode(r))
    if not reqs and not challenges:
        return u'None'
    return u', '.join(reqs) + u'\n' + u'\n'.join(challenges)


class Storylet: #done?
    def __init__(self, jdata, shallow=False):
        global data
        self.raw = jdata
        self.title = jdata.get('Name', '(no name)')
        self.desc = jdata.get('Description', '(no description)')
        self.id = jdata['Id']
        try:
            self.setting = Setting.get(jdata['Setting']['Id'])
        except KeyError:
            self.setting = None
        try:
            self.area = Area.get(jdata['LimitedToArea'])
        except KeyError:
            self.area = None
        self.availability = jdata['Deck']['Name']
        if self.availability == 'Sometimes':
            self.frequency = jdata['Distribution']
        self.requirements = []
        for r in jdata['QualitiesRequired']:
            self.requirements.append(Requirement(r))
        
        self.branches = []
        if not shallow:
            for b in jdata['ChildBranches']:
                branch=Branch.get(b, self)
                self.branches.append(branch)
                for e in branch.events.items():
                    if e[0].endswith('Event'):
                        e[1].parent = b
    def __repr__(self):
        return u'"{}"'.format(self.title)
    def __str__(self):
        #_,c = os.popen('stty size', u'r').read().split()
        return u'Storylet Title: "{}"\nDescription: {}\nRequirements: {}\nBranches: {}'.format( 
        self.title,
        render(self.desc),
        render_requirements(self.requirements, None),
        u'\n{}\n\n'\
                .format(u'~' * 20)\
                .join(self.render_branches()))\
                .encode('utf-8')
    def render_branches(self):
        return [str(b).decode('utf-8') for b in self.branches]
    @classmethod
    def get(self, id):
        global cache
        key = u'storylets:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Storylet(data['events:{}'.format(id)],True)
            cache[key] = Storylet(data['events:{}'.format(id)],False)
            return cache[key]

class Branch:   #done
    def __init__(self, jdata, parent):
        self.raw = jdata
        self.title = jdata.get('Name', u'(no title)')
        self.id = jdata['Id']
        self.parent = parent
        self.desc = jdata.get('Description', '(no description)')
        self.cost = jdata.get('ActionCost', 1)
        self.button = jdata.get('ButtonText', 'Go')
        self.fate = jdata.get('CurrencyCost')
        try:
            self.act = Act.get(jdata['Act']['Id'])
        except KeyError:
            self.act = None
        self.requirements = []
        for r in jdata['QualitiesRequired']:
            self.requirements.append(Requirement(r))
        costs = [ {'AssociatedQuality': {'Id': r.quality.id}, 'Level': -r.lower_bound} for r in self.requirements if r.is_cost ]
        self.events = {}
        for key in jdata.keys():
            if key in ['DefaultEvent', u'SuccessEvent', u'RareSuccessEvent', u'RareSuccessEventChance', u'RareDefaultEvent', u'RareDefaultEventChance']:
                if key.endswith('Chance'):
                    self.events[key] = jdata[key]
                else:
                    self.events[key] = Event.get(jdata[key], costs)
    def __repr__(self):
        return u'"{}"'.format(self.title)
    def __str__(self):
        return u'Branch Title: "{}"\nDescription: {}\nRequirements: {}\n{}'.format(self.title, render(self.desc) if self.desc is not None else '', render_requirements(self.requirements, self.fate if hasattr(self, 'fate') else None), render_events(self.events)).encode('utf-8')
    @classmethod
    def get(self, jdata, parent=None):
        global cache
        key = u'branches:{}'.format(jdata['Id'])
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
        strings.append( u'Success: "{}"\n{}\nEffects: {}'.format(se.title, render(se.desc), se.list_effects()))
    except KeyError:
        pass
    try:
        rse = ed['RareSuccessEvent']
        strings.append(u'Rare Success: "{}" ({}% chance)\n{}\nEffects: {}'.format(rse.title, ed['RareSuccessEventChance'], render(rse.desc), rse.list_effects()))
    except KeyError:
        pass
    try:
        fe = ed['DefaultEvent']
        strings.append(u'{}: "{}"\n{}\nEffects: {}'.format('Failure' if len(strings) > 0 else u'Event', fe.title, render(fe.desc), fe.list_effects()))
    except KeyError:
        pass
    try:
        rfe = ed['RareDefaultEvent']
        strings.append(u'Rare {}: "{}" ({}% chance)\n{}\nEffects: {}'.format('Failure' if len(strings) > 1 else 'Success', rfe.title, ed['RareDefaultEventChance'], render(rfe.desc), rfe.list_effects()))
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
        self.is_cost = jdata.get('IsCostRequirement', False)
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
                self.difficulty = sub_qualities(jdata['DifficultyAdvanced'])
            except KeyError:
                pass
        if hasattr(self, u'difficulty'):
            self.type = u'Challenge'
            self.test_type = self.quality.test_type
        else:
            self.type = u'Requirement'
        self.visibility = jdata.get('BranchVisibleWhenRequirementFailed')
    def __repr__(self):
        if self.type == u'Challenge':
            if self.quality.id == 432:
                return u'Luck: {}% chance'.format(50 - self.difficulty * 10)
            else:
                return u'{} {}: {} {}'.format(self.test_type, self.type, self.quality.name, self.difficulty)
        else:
            try:
                if self.lower_bound == self.upper_bound:
                    return u'{} exactly {}'.format(self.quality.name, self.lower_bound)
                else:
                    return u'{} [{}-{}]'.format(self.quality.name, self.lower_bound, self.upper_bound)
            except:
                try:
                    return u'{} at least {}'.format(self.quality.name, self.lower_bound)
                except:
                    return u'{} no more than {}'.format(self.quality.name, self.upper_bound)
            

class Event:    #done
    def __init__(self, jdata, costs):
        self.raw = jdata
        self.id = jdata['Id']
        self.parent = None        
        self.title = jdata.get('Name', '(no title)')
        self.desc = jdata.get('Description', '(no description)')
        self.category = jdata.get('Category')
        self.effects = []
        if costs:
            for c in costs:
                self.effects.append(Effect(c))
        for e in jdata['QualitiesAffected']:
            self.effects.append(Effect(e))
        try:
            if jdata['ExoticEffects'] != u'':
                self.exotic_effect = jdata['ExoticEffects']
            else:
                self.exotic_effect = None
        except KeyError:
            self.exotic_effect = None
        self.lodging = jdata.get('MoveToDomicile', {}).get('Id')
        self.livingstory = jdata.get('LivingStory', {}).get('Id')
        self.img = jdata.get('Image')
        self.newsetting = jdata.get('SwitchToSettingId')
        self.newarea = jdata.get('MoveToArea')
        try:
            self.linkedevent = Storylet.get(jdata['LinkToEvent']['Id'])
        except KeyError:
            self.linkedevent = None
    def __repr__(self):
        return u'Event: {}'.format(self.title) if self.title != u'' else u'Event: (no title)'
    def __str__(self):
        return u'Title: "{}"\nDescription: {}\nEffects: {}\n'.format(self.title if self.title != u'' else u'(no title)', render(self.desc), self.list_effects()).encode('utf-8')
    def list_effects(self):
        string = u''
        if self.effects != []:
            string += u'[{}]\n'.format(u', '.join([unicode(e) for e in self.effects]))
        if self.exotic_effect:
            string += u'Exotic effect: {}\n'.format(self.exotic_effect)
        if self.livingstory:
            string += u'Triggers Living Story: {}\n'.format(self.livingstory) #todo make Livingstory class
        if self.lodging:
            string += u'Move to lodging: {}\n'.format(self.lodging) #todo make lodgings class
        if self.newsetting:
            string += u'Move to new setting: {}\n'.format(self.newsetting) #todo flesh out setting class
        if self.newarea:
            string += u'Move to new area: {}\n'.format(self.newarea)
        try:
            if self.parent.act:
                string += u'Associated social action: {}\n'.format(self.parent.act)
        except:
            pass
        if self.linkedevent:
            string += u'Linked event: "{}" (Id {})\n'.format(self.linkedevent.title, self.linkedevent.id)
        return string
        
    @classmethod
    def get(self, jdata, costs):
        global cache
        key = u'events:{}'.format(jdata['Id'])
        if key in cache:
            return cache[key]
        else:
            cache[key] = Event(jdata, costs)
            return cache[key]

def sub_qualities(string):
    for x in re.findall(r'\[qb?:(\d+)\]', string):
        string = string.replace(x, Quality.get(int(x)).name)
    return string

class Effect:   #done: Priority goes 3/2/1/0
    def __init__(self, jdata, costs=None):
        self.raw = jdata
        self.quality = Quality.get(jdata['AssociatedQuality']['Id'])
        self.equip = u'ForceEquip' in jdata
        try:
            self.amount = jdata['Level']
        except:
            try:
                self.amount = sub_qualities(jdata['ChangeByAdvanced'])
            except KeyError:
                pass
        try:
            self.setTo = jdata['SetToExactly']
        except:
            try:
                self.setTo = sub_qualities(jdata['SetToExactlyAdvanced'])
            except KeyError:
                pass
        try:
            self.ceil = jdata['OnlyIfNoMoreThan']
        except KeyError:
            pass
        try:
            self.floor = jdata['OnlyIfAtLeast']
        except KeyError:
            pass
        try:
            self.priority = jdata['Priority']
        except KeyError:
            self.priority = 0
    def __repr__(self):
        try:
            limits = u' if no more than {} and at least {}'.format(self.ceil, self.floor)
        except:
            try:
                limits = u' if no more than {}'.format(self.ceil)
            except:
                try:
                    limits = u' only if at least {}'.format(self.floor)
                except:
                    limits = u''
        if self.equip:
            limits += u' (force equipped)'
                
        try:
            if hasattr(self.quality, 'leveldesc') and isinstance(self.setTo, int):
                descs = sorted(self.quality.leveldesc.items(), reverse=True)
                for x in descs:
                    if x[0] <= self.setTo:
                        desc = x
                        break
                try:
                    return u'{} (set to {} ({}){})'.format(self.quality.name, self.setTo, desc[1], limits)
                except NameError:
                    pass
            return u'{} (set to {}{})'.format(self.quality.name, self.setTo, limits)
        except:
            if self.quality.nature == 2 or not self.quality.pyramid:
                try:
                    return u'{:+} x {}{}'.format(self.amount, self.quality.name, limits)
                except:
                    return u'{} {}{}'.format(('' if self.amount.startswith('-') else u'+') + self.amount, self.quality.name, limits)
            else:
                try:
                    return u'{} ({:+} cp{})'.format(self.quality.name, self.amount, limits)
                except:
                    return u'{} ({} cp{})'.format(self.quality.name, u'' if self.amount.startswith('-') else u'' + self.amount, limits)
                    
categories = {0:        'Unspecified',
              1:        'Currency',
              101:      'Weapon',
              103:      'Hat',
              104:      'Gloves',
              105:      'Boots',
              106:      'Companion',
              107:      'Clothing',
              150:      'Curiosity',
              160:      'Advantage',
              170:      'Document',
              200:      'Goods',
              1000:     'BasicAbility',
              2000:     'SpecificAbility',
              3000:     'Profession',
              5000:     'Story',
              5001:     'Intrigue',
              5002:     'Dreams',
              5003:     'Reputation',
              5004:     'Quirk',
              5025:     'Acquaintance',
              5050:     'Accomplishment',
              5100:     'Venture',
              5200:     'Progress',
              5500:     'Menace',
              6000:     'Contacts',
              6661:     'Hidden',
              6662:     'Randomizer',
              7000:     'Ambition',
              8000:     'Route',
              9000:     'Seasonal',
              10000:    'Ship',
              11000:    'ConstantCompanion',
              12000:    'Club',
              13000:    'Affiliation',
              14000:    'Transportation',
              15000:    'HomeComfort',
              16000:    'Academic',
              17000:    'Cartography',
              18000:    'Contraband',
              19000:    'Elder',
              20000:    'Infernal',
              21000:    'Influence',
              22000:    'Literature',
              22500:    'Lodgings',
              23000:    'Luminosity',
              24000:    'Mysteries',
              25000:    'Nostalgia',
              26000:    'RagTrade',
              27000:    'Ratness',
              28000:    'Rumour',
              29000:    'Legal',
              30000:    'WildWords',
              31000:    'Wines',
              32000:    'Rubbery',
              33000:    'SidebarAbility',
              34000:    'MajorLateral',
              35000:    'Quest',
              36000:    'MinorLateral',
              37000:    'Circumstance',
              39000:    'Avatar',
              40000:    'Objective',
              45000:    'Key',
              50000:    'Knowledge',
              60000:    'Destiny',
              70000:    'Modfier',
              70001:    'GreatGame',
              70002:    'ZeeTreasures',
              70003:    'Sustenance'
}

class Quality:
    def __init__(self, jdata):
        #HimbleLevel is used to determine order within categories for items
        self.raw = jdata
        self.name = jdata.get('Name', u'(no name)')
        self.id = jdata['Id']
        self.desc = jdata.get('Description', u'(no description)')
        self.pyramid = u'UsePyramidNumbers' in jdata
        self.nature = jdata.get('Nature', 1) #1: quality; 2: item
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
            for x in d.items():
                variables[x[0]] = parse_qlds(x[1])
            self.variables = variables
        except KeyError:
            pass
        self.cap = jdata.get('Cap')
        self.category = categories.get(jdata.get('Category'))
        self.tag = jdata.get('Tag')
        self.test_type = u'Narrow' if u'DifficultyTestType' in jdata else u'Broad'
        self.difficulty = jdata.get('DifficultyScaler')
        self.slot = jdata.get('AssignToSlot', {}).get('Id')
        self.event = jdata.get('UseEvent', {}).get('Id') #fix infinite loop
        try:
            self.enhancements = []
            for x in jdata['Enhancements']:
                self.enhancements.append('{:+} {}'.format(x['Level'], Quality.get(x['AssociatedQuality']['Id']).name))
        except KeyError:
            pass
    def __repr__(self):
        return u'Quality: {}'.format(self.name)
    def __str__(self):
        string = u'Quality: {}'.format(self.name)
        try:
            string += u'\nCategory: {}'.format(self.category)
        except AttributeError:
            pass
        try:
            if self.enhancements:
                string += u'\nEnhancements: [{}]'.format(', '.join(self.enhancements))
        except AttributeError:
            pass
        return string.encode('utf-8')
            
    @classmethod
    def get(self, id):
        key = u'qualities:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Quality(data[key])
            if cache[key].event:
                cache[key].event = Storylet.get(cache[key].event)
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
    def __init__(self, jdata):
        self.raw = jdata
        self.title = jdata['Name']
        description = jdata['StartingArea']['Description']

    @classmethod
    def get(self, id):
        key = u'settings:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Setting(data[id])
            return cache[key]

class Area:
    def __init__(self, jdata):
        self.raw = jdata
        self.id = jdata.get('Id')
        self.name = jdata.get('Name', '(no name)')
        self.desc = jdata.get('Description', '(no description)')
        self.image = jdata.get('ImageName', '(no image)')
        self.showOps = 'ShowOps' in jdata
        try:
            self.unlock = Quality.get(jdata['UnlocksWithQuality']['Id'])
        except:
            pass
        self.premium = 'PremiumSubRequired' in jdata
        self.message = jdata.get('MoveMessage', '(no move message)')
    def __repr__(self):
        return u'{} (Id {})'.format(self.name, self.id)
    def __str__(self):
        string = u'{} (Id {})'.format(self.name, self.id)
        string += u'\nDescription: {}'.format(self.desc)
        string += u'\nOpportunity cards are ' + (u'' if self.showOps else u'NOT ') + u'visible'
        try:
            string += u'\nUnlocks with {}'.format(self.unlock.name)
        except AttributeError:
            pass
        if self.premium:
            string += u'\nRequires Exceptional Friendship'
        string += u'\n{}'.format(self.message)
        return string.encode('utf-8')
    @classmethod
    def get(self, id):
        key = u'areas:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Area(data[key])
            return cache[key]
    
class Act:  #for social actions
    def __init__(self, jdata):
        self.raw = jdata
        self.name = jdata['Name']
        self.msg = jdata['InviteMessage']
    def __repr__(self):
        return u'"{}"'.format(self.name)
    @classmethod
    def get(self, id):
        key = u'acts:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Act(data[id])
            return cache[key]

class AccessCode:
    def __init__(self, jdata):
        self.raw = jdata
        self.name = jdata.get('Name', u'(no name)')
        self.message1 = jdata.get('InitialMessage', u'(no message)')
        self.message2 = jdata.get('CompletedMessage', u'(no message)')
        self.effects = []
        for e in jdata['QualitiesAffected']:
            self.effects.append(Effect(e))
    def __repr__(self):
        string = u'Access code name: {}'.format(self.name)
        string += u'\nInitial message: {}'.format(self.message1)
        string += u'\nFinish message: {}'.format(self.message2)
        string += u'\nEffects: {}'.format(self.list_effects())
        return string.encode('utf-8')
    def __unicode__(self):
        string = u'Access code name: {}'.format(self.name)
        string += u'\nInitial message: {}'.format(self.message1)
        string += u'\nFinish message: {}'.format(self.message2)
        string += u'\nEffects: {}'.format(self.list_effects())
        return string
    def list_effects(self):
        if self.effects != []:
            return u'[{}]'.format(u', '.join([unicode(e) for e in self.effects]))
