#!/usr/bin/python2
# -*- coding: utf-8 -*-
import json, re
from html import unescape
cache = {}
data = {}
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
              1000:     'Basic Ability',
              2000:     'Specific Ability',
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
              11000:    'Constant Companion',
              12000:    'Club',
              13000:    'Affiliation',
              14000:    'Transportation',
              15000:    'Home Comfort',
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
              26000:    'Rag Trade',
              27000:    'Ratness',
              28000:    'Rumour',
              29000:    'Legal',
              30000:    'Wild Words',
              31000:    'Wines',
              32000:    'Rubbery',
              33000:    'Sidebar Ability',
              34000:    'Major Lateral',
              35000:    'Quest',
              36000:    'Minor Lateral',
              37000:    'Circumstance',
              39000:    'Avatar',
              40000:    'Objective',
              45000:    'Key',
              50000:    'Knowledge',
              60000:    'Destiny',
              70000:    'Modfier',
              70001:    'Great Game',
              70002:    'Zee Treasures',
              70003:    'Sustenance'
}

def render_html(string):
    string = re.sub(r'<.{,2}?br.{,2}?>','\n', string)
    string = re.sub(r'<.{,2}?[pP].{,2}?>','', string)
    string = re.sub('</?em>', '_', string)
    string = re.sub('</?i>', '_', string)
    string = re.sub('</?strong>', '*', string)
    string = re.sub('</?b>', '*', string)
    return string

class Quality:
    def __init__(self, jdata):
        #HimbleLevel is used to determine order within categories for items
        self.raw = jdata
        self.name = unescape(jdata.get('Name', '(no name)'))
        self.id = jdata['Id']
        self.desc = unescape(jdata.get('Description', '(no description)'))
        self.pyramid = 'UsePyramidNumbers' in jdata
        self.nature = jdata.get('Nature', 1) #1: quality; 2: item
        try:
            qldstr = jdata['ChangeDescriptionText']
            self.changedesc = parse_qlds(unescape(qldstr))
        except KeyError:
            self.changedesc = None
        try:
            qldstr = jdata['LevelDescriptionText']
            self.leveldesc = parse_qlds(unescape(qldstr))
        except KeyError:
            self.leveldesc = None
        try:
            variables = {}
            d = json.loads(unescape(jdata['VariableDescriptionText']))
            for x in list(d.items()):
                variables[x[0]] = parse_qlds(x[1])
            self.variables = variables
        except KeyError:
            self.variables = None
        self.cap = jdata.get('Cap')
        self.category = categories.get(jdata.get('Category'))
        self.tag = jdata.get('Tag')
        self.test_type = 'Narrow' if 'DifficultyTestType' in jdata else 'Broad'
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
        return 'Quality: {}'.format(self.name)

    def __str__(self):
        string = 'Quality: {}'.format(self.name)
        try:
            string += '\nCategory: {}'.format(self.category)
        except AttributeError:
            pass
        try:
            if self.enhancements:
                string += '\nEnhancements: [{}]'.format(', '.join(self.enhancements))
        except AttributeError:
            pass
        return string

    @classmethod
    def get(self, id):
        key = 'qualities:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Quality(data[key])
            if cache[key].event:
                cache[key].event = Storylet.get(cache[key].event)
            return cache[key]

    def get_changedesc(self, level):
        if self.changedesc and isinstance(level, int):
            descs = sorted(list(self.changedesc.items()), reverse=True)
            for x in descs:
                if x[0] <= level:
                    desc = x
                    break
                desc = (-1, 'no description')
            return desc
        return None

    def get_leveldesc(self, level):
        if self.leveldesc and isinstance(level, int):
            descs = sorted(list(self.leveldesc.items()), reverse=True)
            for x in descs:
                if x[0] <= level:
                    desc = x
                    break
                desc = (-1, 'no description')
            return desc
        return None

def sub_qualities(string):
    for x in re.findall(r'\[qb?:(\d+)\]', string):
        string = string.replace(x, Quality.get(int(x)).name)
    return string

def parse_qlds(string):
    qld = {}
    qlds = string.split('~')
    for d in qlds:
        level, text = d.split('|', 1)
        level = int(level)
        qld[level] = text
    return dict(sorted(qld.items()))

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
        if hasattr(self, 'difficulty'):
            self.type = 'Challenge'
            self.test_type = self.quality.test_type
        else:
            self.type = 'Requirement'
        assert jdata.get('BranchVisibleWhenRequirementFailed') == jdata.get('VisibleWhenRequirementFailed')
        self.visibility = jdata.get('BranchVisibleWhenRequirementFailed', False)

    def __repr__(self):
        string = ''
        if not self.visibility:
            string += '[Branch hidden if failed] '
        if self.type == 'Challenge':
            if self.quality.id == 432:
                string += 'Luck: {}% chance'.format(50 - self.difficulty * 10)
            else:
                string += '{} {}: {} {}'.format(self.test_type, self.type, self.quality.name, self.difficulty)
        else:
            string += self.quality.name
            try:
                if self.lower_bound == self.upper_bound:
                    desc = self.quality.get_leveldesc(self.lower_bound)
                    if desc:
                        desc = f' ({desc[1]})'
                    string += f' exactly {self.lower_bound}{desc if desc else ""}'
                else:
                    lower = self.quality.get_leveldesc(self.lower_bound)
                    if lower:
                        lower = f' ({lower[1]})'
                    upper = self.quality.get_leveldesc(self.upper_bound)
                    if upper:
                        upper = f' ({upper[1]})'
                    string += f' [{self.lower_bound}{lower if lower else ""}-{self.upper_bound}{upper if upper else ""}]'
            except:
                try:
                    desc = self.quality.get_leveldesc(self.lower_bound)
                    if desc:
                        desc = f' ({desc[1]})'
                    string += f' at least {self.lower_bound}{desc if desc else ""}'
                except:
                    desc = self.quality.get_leveldesc(self.upper_bound)
                    if desc:
                        desc = f' ({desc[1]})'
                    string += f' no more than {self.upper_bound}{desc if desc else ""}'
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
    def __init__(self, jdata, shallow=False):
        self.raw = jdata
        self.title = unescape(jdata.get('Name', '(no name)'))
        self.desc = unescape(jdata.get('Description', '(no description)'))
        self.id = jdata['Id']
        try:
            self.setting = Setting.get(jdata['Setting']['Id'])
        except KeyError:
            self.setting = None
        try:
            self.area = Area.get(jdata['LimitedToArea']['Id'])
        except KeyError:
            self.area = None
        self.type = 'Storylet' if jdata['Deck']['Name'] == 'Always' else 'Card' if jdata['Deck']['Name'] == 'Sometimes' else 'Unknown type'
        if self.type == 'Card':
            self.frequency = jdata['Distribution']
            self.autofire = 'Autofire' in jdata
        else:
            self.autofire = False
        self.requirements = []
        for r in jdata['QualitiesRequired']:
            self.requirements.append(Requirement(r))
        if self.autofire:
            self.effects = [Effect(e) for e in jdata['QualitiesAffected']]
        else:
            self.branches = []
            if not shallow:
                for b in jdata['ChildBranches']:
                    branch=Branch.get(b, self)
                    self.branches.append(branch)
                    for e in list(branch.events.items()):
                        if e[0].endswith('Event'):
                            e[1].parent = branch

    def __repr__(self):
        return '{}: "{}"'.format(self.type, self.title)

    def __str__(self):
        #_,c = os.popen('stty size', u'r').read().split()
        string = '{}{} Title: "{}"\n'.format('Autofire ' if self.autofire else '', self.type, self.title)
        try:
            string += 'Appears in {} '.format(self.setting.title)
        except AttributeError:
            pass
        try:
            string += 'Limited to area: {}'.format(self.area.name)
        except AttributeError:
            pass
        string += '\nDescription: {}'.format(render_html(self.desc))
        string += '\nRequirements: {}'.format(render_requirements(self.requirements, None))
        if self.autofire:
            string += '\nEffects: {}'.format(self.effects)
        else:
            string += '\nBranches:\n{}'.format('\n\n{}\n\n'.format('~' * 20).join(self.render_branches()))
        return string

    def render_branches(self):
        return [str(b) for b in self.branches]

    @classmethod
    def get(self, id):
        key = 'storylets:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Storylet(data['events:{}'.format(id)],True)
            if not cache[key].autofire:
                cache[key] = Storylet(data['events:{}'.format(id)],False)
            return cache[key]

def add_requirements(l, req):
    if any([key in req for key in ['DifficultyLevel', 'DifficultyAdvanced']]) and any([key in req for key in ['MaxLevel', 'MaxAdvanced', 'MinLevel', 'MinAdvanced']]):
        l.append(Requirement(req))
        for i in list(req.items()):
            if i[0].startswith('Difficulty'):
                req.pop(i[0])
        l.append(Requirement(req))
    else:
        l.append(Requirement(req))

class Branch:   #done
    def __init__(self, jdata, parent):
        self.raw = jdata
        self.title = unescape(jdata.get('Name', '(no title)'))
        self.id = jdata['Id']
        self.parent = parent
        self.desc = unescape(jdata.get('Description', '(no description)'))
        self.cost = jdata.get('ActionCost', 1)
        self.button = jdata.get('ButtonText', 'Go')
        self.fate = jdata.get('CurrencyCost')
        try:
            self.act = Act.get(jdata['Act']['Id'])
        except KeyError:
            self.act = None
        self.requirements = []
        for r in jdata['QualitiesRequired']:
            add_requirements(self.requirements, r)
        costs = [ {'AssociatedQuality': {'Id': r.quality.id}, 'Level': -r.lower_bound} for r in self.requirements if r.is_cost ]
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
        string = 'Branch Title: "{}"'.format(self.title)
        if self.desc:
            string += '\nDescription: {}'.format(render_html(self.desc))
        string += '\nRequirements: {}'.format(render_requirements(self.requirements, self.fate if hasattr(self, 'fate') else None))
        if self.cost != 1:
            string += '\nAction cost: {}'.format(self.cost)
        string += '\n{}'.format(render_events(self.events))
        return string

    @classmethod
    def get(self, jdata, parent=None):
        key = 'branches:{}'.format(jdata['Id'])
        if key in cache:
            return cache[key]
        else:
            cache[key] = Branch(jdata, parent)
            return cache[key]

class Event:    #done
    def __init__(self, jdata, costs):
        self.raw = jdata
        self.id = jdata['Id']
        self.parent = None
        self.title = unescape(jdata.get('Name', '(no title)'))
        self.desc = unescape(jdata.get('Description', '(no description)'))
        self.category = jdata.get('Category')
        self.effects = []
        if costs:
            for c in costs:
                self.effects.append(Effect(c))
        for e in jdata['QualitiesAffected']:
            self.effects.append(Effect(e))
        try:
            if jdata['ExoticEffects'] != '':
                self.exotic_effect = jdata['ExoticEffects']
            else:
                self.exotic_effect = None
        except KeyError:
            self.exotic_effect = None
        self.lodging = jdata.get('MoveToDomicile', {}).get('Id')
        self.livingstory = jdata.get('LivingStory', {}).get('Id')
        self.img = jdata.get('Image')
        try:
            assert jdata.get('SwitchToSettingId') == jdata.get('SwitchToSetting', {}).get('Id')
        except AssertionError:
            print('Warning: event setting IDs don\'t match')
            print(jdata)
        try:
            self.newsetting = Setting.get(jdata.get('SwitchToSettingId'))
        except:
            self.newsetting = None
        try:
            self.newarea = Area.get(jdata.get('MoveToArea', {}).get('Id'))
        except:
            self.newarea = None
        try:
            self.linkedevent = Storylet.get(jdata['LinkToEvent']['Id'])
        except KeyError:
            self.linkedevent = None

    def __repr__(self):
        return 'Event: {}'.format(self.title) if self.title != '' else 'Event: (no title)'

    def __str__(self):
        return 'Title: "{}"\nDescription: {}\nEffects: {}\n'.format(self.title if self.title != '' else '(no title)', render_html(self.desc), self.list_effects())

    def list_effects(self):
        effects = []
        if self.effects != []:
            effects.append('[{}]'.format(', '.join([str(e) for e in self.effects])))
        if self.exotic_effect:
            effects.append('Exotic effect: {}'.format(self.exotic_effect))
        if self.livingstory:
            effects.append('Triggers Living Story: {}'.format(self.livingstory)) #todo make Livingstory class
        if self.lodging:
            effects.append('Move to lodging: {}'.format(self.lodging)) #todo make lodgings class
        if self.newsetting:
            effects.append('Move to new setting: {}'.format(self.newsetting)) #todo flesh out setting class
        if self.newarea:
            effects.append('Move to new area: {}'.format(self.newarea))
        try:
            if self.parent.act:
                effects.append('Associated social action: {}'.format(self.parent.act))
        except:
            pass
        if self.linkedevent:
            effects.append('Linked event: "{}" (Id {})'.format(self.linkedevent.title, self.linkedevent.id))
        return '\n'.join(effects)

    @classmethod
    def get(self, jdata, costs):
        key = 'events:{}'.format(jdata['Id'])
        if key in cache:
            return cache[key]
        else:
            cache[key] = Event(jdata, costs)
            return cache[key]

def render_events(ed):
    strings = []
    try:
        se = ed['SuccessEvent']
        strings.append( 'Success: "{}"\n{}\nEffects: {}'.format(se.title, render_html(se.desc), se.list_effects()))
    except KeyError:
        pass
    try:
        rse = ed['RareSuccessEvent']
        strings.append('Rare Success: "{}" ({}% chance)\n{}\nEffects: {}'.format(rse.title, ed['RareSuccessEventChance'], render_html(rse.desc), rse.list_effects()))
    except KeyError:
        pass
    try:
        fe = ed['DefaultEvent']
        strings.append('{}: "{}"\n{}\nEffects: {}'.format('Failure' if len(strings) > 0 else 'Event', fe.title, render_html(fe.desc), fe.list_effects()))
    except KeyError:
        pass
    try:
        rfe = ed['RareDefaultEvent']
        strings.append('Rare {}: "{}" ({}% chance)\n{}\nEffects: {}'.format('Failure' if len(strings) > 1 else 'Success', rfe.title, ed['RareDefaultEventChance'], render_html(rfe.desc), rfe.list_effects()))
    except KeyError:
        pass
    return '\n\n{}\n\n'.format('-' * 20).join(strings)

class Effect:   #done: Priority goes 3/2/1/0
    def __init__(self, jdata, costs=None):
        self.raw = jdata
        self.quality = Quality.get(jdata['AssociatedQuality']['Id'])
        self.equip = 'ForceEquip' in jdata
        try:
            self.amount = jdata['Level']
        except:
            try:
                self.amount = sub_qualities(jdata['ChangeByAdvanced']).strip()
            except KeyError:
                pass
        try:
            self.setTo = jdata['SetToExactly']
        except:
            try:
                self.setTo = sub_qualities(jdata['SetToExactlyAdvanced']).strip()
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
            limits = ' if no more than {} and at least {}'.format(self.ceil, self.floor)
        except:
            try:
                limits = ' if no more than {}'.format(self.ceil)
            except:
                try:
                    limits = ' only if at least {}'.format(self.floor)
                except:
                    limits = ''
        if self.equip:
            limits += ' (force equipped)'

        try:
            if isinstance(self.setTo, int):
                if self.quality.changedesc:
                    desc = self.quality.get_changedesc(self.setTo)
                elif self.quality.leveldesc:
                    desc = self.quality.get_leveldesc(self.setTo)
                else:
                    desc = None
                try:
                    return '{} (set to {} ({}){})'.format(self.quality.name, self.setTo, desc[1], limits)
                except TypeError:
                    pass
            return '{} (set to {}{})'.format(self.quality.name, self.setTo, limits)
        except:
            if self.quality.nature == 2 or not self.quality.pyramid:
                try:
                    return '{:+} x {}{}'.format(self.amount, self.quality.name, limits)
                except:
                    return '{} x {}{}'.format(('' if self.amount.startswith('-') else '+') + self.amount, self.quality.name, limits)
            else:
                try:
                    return '{} ({:+} cp{})'.format(self.quality.name, self.amount, limits)
                except:
                    return '{} ({} cp{})'.format(self.quality.name, ('' if self.amount.startswith('-') else '+') + self.amount, limits)

class Lodging:
    def __init__(self, jdata):
        self.raw = jdata
        self.id = jdata.get('Id')
        self.name = jdata.get('Name', '(no name)')
        self.desc = render_html(jdata.get('Description', '(no description)'))
        self.image = jdata.get('ImageName')
        self.hand = jdata.get('MaxHandSize')

    def __repr__(self):
        return self.name

    def __str__(self):
        string = 'Lodging: {} (Id {})'.format(self.name, self.id)
        string += '\nDescription: {}'.format(self.desc)
        if not self.hand:
            string += '\nHand size: None'
        elif self.hand == 1:
            string += '\nHand size: 1 card'
        else:
            string += '\nHand size: {}'.format('{} cards'.format(self.hand) if self.hand else 'N/A')
        return string

    @classmethod
    def get(self, id):
        key = 'domiciles:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Lodging(data[key])
            return cache[key]

class Setting:
    def __init__(self, jdata):
        self.raw = jdata
        self.id = jdata.get('Id')
        self.title = jdata.get('Name')
        self.persona = jdata.get('Personae')
        self.maxactions = jdata.get('MaxActionsAllowed')
        self.exhaustion = jdata.get('ActionsInPeriodBeforeExhaustion')
        self.turnlength = jdata.get('TurnLengthSeconds')

        self.area = jdata.get('StartingArea', {}).get('Id')
        if self.area:
            try:
                assert jdata.get('StartingArea') == data['areas:{}'.format(self.area)]
            except AssertionError:
                print('Warning: Area data mismatch')
                print(jdata.get('StartingArea'))
                print(data[f'areas:{self.area}'])
            self.area = Area.get(self.area)

        self.domicile = jdata.get('StartingDomicile')
        if self.domicile:
            self.domicile = Lodging(self.domicile)

#        self.exchange = jdata.get('Exchange')
#        if self.exchange:
#            self.exchange = Exchange(self.exchange)

        self.items = 'ItemsUsableHere' in jdata

    def __repr__(self):
        return self.title

    def __str__(self):
        string = 'Setting name: {} (Id {})'.format(self.title, self.id)
        if self.area:
            string += '\nStarting area: {}'.format(self.area)
        if self.domicile:
            string += '\nStarting lodging: {}'.format(self.domicile)
        string += '\nItems are {}usable here'.format('' if self.items else 'NOT ')
        return string

    @classmethod
    def get(self, id):
        key = 'settings:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Setting(data[key])
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
        return '{} (Id {})'.format(self.name, self.id)

    def __str__(self):
        string = '{} (Id {})'.format(self.name, self.id)
        string += '\nDescription: {}'.format(self.desc)
        string += '\nOpportunity cards are ' + ('' if self.showOps else 'NOT ') + 'visible'
        try:
            string += '\nUnlocks with {}'.format(self.unlock.name)
        except AttributeError:
            pass
        if self.premium:
            string += '\nRequires Exceptional Friendship'
        string += '\n{}'.format(self.message)
        return string

    @classmethod
    def get(self, id):
        key = 'areas:{}'.format(id)
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
        return '"{}"'.format(self.name)

    @classmethod
    def get(self, id):
        key = 'acts:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Act(data[key])
            return cache[key]

class AccessCode:
    def __init__(self, jdata):
        self.raw = jdata
        self.name = jdata.get('Name', '(no name)')
        self.message1 = jdata.get('InitialMessage', '(no message)')
        self.message2 = jdata.get('CompletedMessage', '(no message)')
        self.effects = []
        for e in jdata['QualitiesAffected']:
            self.effects.append(Effect(e))

    def __repr__(self):
        string = 'Access code name: {}'.format(self.name)
        string += '\nInitial message: {}'.format(self.message1)
        string += '\nFinish message: {}'.format(self.message2)
        string += '\nEffects: {}'.format(self.list_effects())
        return string

    def list_effects(self):
        if self.effects != []:
            return '[{}]'.format(', '.join([str(e) for e in self.effects]))

    @classmethod
    def get(self, id):
        key = 'accesscodes:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = AccessCode(data[key])
            return cache[key]

class Exchange:
    def __init__(self, jdata):
        self.raw = jdata
        self.id = jdata.get('Id')
        self.name = jdata.get('Name', '(no name)')
        self.title = jdata.get('Title', '(no title)')
        self.desc = jdata.get('Description', '(no description)')
        self.shops = []
        for x in jdata.get('Shops', []):
            self.shops.append(Shop(x))

    def __repr__(self):
        return 'Exchange Title: {} (ID {})'.format(self.title, self.id)

    def __str__(self):
        return 'Exchange Name: {} (ID {})\nExchange Title: {}\nExchange Description: {}\nShops:\n{}'.format(self.name, self.id, self.title, self.desc, '\n'.join([s.name for s in self.shops]))

    @classmethod
    def get(self, id):
        key = 'exchanges:{}'.format(id)
        if key in cache:
            return cache[key]
        else:
            cache[key] = Exchange(data[key])
            return cache[key]

class Shop:
    def __init__(self, jdata):
        self.raw = jdata
        self.id = jdata.get('Id')
        self.name = jdata.get('Name', '(no name)')
        self.desc = jdata.get('Description', '(no description)')
        self.image = jdata.get('Image')
        self.requirements = []
        for r in jdata.get('QualitiesRequired', []):
            self.requirements.append(Requirement(r))
        self.offerings = {}
        for item in jdata.get('Availabilities'):
            i = Offering(item)
            self.offerings[i.item.name] = i

    def __repr__(self):
        return self.name

    def __str__(self):
        return 'Shop Name: {}\nDescription: {}\nItems: [{}]'.format(self.name, self.desc, ', '.join(list(self.offerings.keys())))

    def __getitem__(self, key):
        return self.offerings[key]

class Offering:
    def __init__(self, jdata):
        self.raw = jdata
        self.id = jdata.get('Id')
        self.item = Quality.get(jdata.get('Quality', {}).get('Id'))
        self.price = Quality.get(jdata.get('PurchaseQuality', {}).get('Id'))
        self.buymessage = jdata.get('BuyMessage', '(no message)')
        if not self.buymessage.replace('"',''):
            self.buymessage = '(no message)'
        self.sellmessage = jdata.get('SellMessage', '(no message)')
        if not self.sellmessage.replace('"',''):
            self.sellmessage = '(no message)'
        if 'Cost' in jdata:
            self.buy = (jdata.get('Cost'), self.price)
        if 'SellPrice' in jdata:
            self.sell = (jdata.get('SellPrice'), self.price)

    def __repr__(self):
        return 'Item: {}'.format(self.item.name)

    def __str__(self):
        string = 'Item: {}'.format(self.item.name)
        try:
            string += '\nBuy for {0[0]} x {0[1].name}'.format(self.buy)
            if self.buymessage != '(no message)':
                string += ' - Buy Message: {}'.format(self.buymessage)
        except AttributeError:
            if self.buymessage != '(no message)':
                string += '\nBuy Message: {} (cannot be bought)'.format(self.buymessage)
        try:
            string += '\nSell for {0[0]} x {0[1].name}'.format(self.sell)
            if self.sellmessage != '(no message)':
                string += ' - Sell Message: {}'.format(self.sellmessage)
        except AttributeError:
            if self.sellmessage != '(no message)':
                string += '\nSell Message: {} (cannot be sold)'.format(self.sellmessage)
        return string
